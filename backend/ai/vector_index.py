"""
向量索引抽象层

当前实现：内存版（numpy）
- 千级候选人规模：单查询 < 5ms
- 零依赖，立即可用

未来切换到 pgvector / Milvus：
- 继承 BaseVectorIndex 即可
- 调用方 zero change（接口稳定）

切换方式：
    settings.AI_VECTOR_BACKEND = 'numpy' | 'pgvector' | 'milvus'

设计原则：
- 候选集由调用方提供（DB 查询过滤后的子集）
- 索引只管"快速算最近邻"
"""
import hashlib
import logging
import threading
import time
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional

import numpy as np

logger = logging.getLogger(__name__)


class BaseVectorIndex(ABC):
    """抽象基类"""

    @abstractmethod
    def index(self, ids: List[str], vectors: List[List[float]]):
        """构建索引（首次或重建）"""
        ...

    @abstractmethod
    def upsert(self, ids: List[str], vectors: List[List[float]]):
        """增量更新"""
        ...

    @abstractmethod
    def search(self, query_vec: List[float], top_k: int = 20,
               exclude_ids: Optional[List[str]] = None) -> List[Tuple[str, float]]:
        """
        检索 top_k
        返回 [(id, similarity), ...]
        """
        ...

    @abstractmethod
    def size(self) -> int:
        """当前索引规模"""
        ...


class NumpyIndex(BaseVectorIndex):
    """
    内存版实现：每次 query 都是"矩阵 × 向量"

    适用场景：
    - 候选数 < 1万
    - QPS < 50

    性能（1536 维）：
    - 100 候选：~2ms
    - 1000 候选：~8ms
    - 10000 候选：~80ms
    """

    def __init__(self):
        self._ids: List[str] = []
        self._matrix: Optional[np.ndarray] = None  # shape: (N, D)
        self._lock = threading.RLock()
        self._dirty = False

    def index(self, ids: List[str], vectors: List[List[float]]):
        """重建索引"""
        with self._lock:
            if not ids:
                self._ids = []
                self._matrix = None
                self._dirty = True
                return
            self._ids = list(ids)
            self._matrix = np.asarray(vectors, dtype=np.float32)
            # 预归一化（之后检索只要点积即可 = 余弦相似度）
            norms = np.linalg.norm(self._matrix, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1.0, norms)
            self._matrix = self._matrix / norms
            self._dirty = True
            logger.info(f"[vector-index:numpy] indexed {len(ids)} vectors, dim={self._matrix.shape[1]}")

    def upsert(self, ids: List[str], vectors: List[List[float]]):
        """增量更新：覆盖同名 id"""
        if not ids:
            return
        with self._lock:
            if self._matrix is None:
                self.index(ids, vectors)
                return
            id_to_idx = {uid: i for i, uid in enumerate(self._ids)}
            new_ids = []
            new_vecs = []
            for uid, vec in zip(ids, vectors):
                if uid in id_to_idx:
                    # 覆盖
                    i = id_to_idx[uid]
                    v = np.asarray(vec, dtype=np.float32)
                    v = v / (np.linalg.norm(v) or 1.0)
                    self._matrix[i] = v
                else:
                    new_ids.append(uid)
                    new_vecs.append(vec)
            if new_ids:
                # append 新向量
                new_matrix = np.asarray(new_vecs, dtype=np.float32)
                norms = np.linalg.norm(new_matrix, axis=1, keepdims=True)
                norms = np.where(norms == 0, 1.0, norms)
                new_matrix = new_matrix / norms
                self._ids.extend(new_ids)
                self._matrix = np.vstack([self._matrix, new_matrix])

    def search(self, query_vec: List[float], top_k: int = 20,
               exclude_ids: Optional[List[str]] = None) -> List[Tuple[str, float]]:
        """检索 top_k 相似"""
        with self._lock:
            if self._matrix is None or len(self._ids) == 0:
                return []
            q = np.asarray(query_vec, dtype=np.float32)
            q_norm = np.linalg.norm(q)
            if q_norm == 0:
                return []
            q = q / q_norm
            # 单次矩阵 × 向量
            sims = self._matrix @ q  # shape: (N,)
            # 排除
            if exclude_ids:
                exclude_set = set(exclude_ids)
                mask = np.array([uid not in exclude_set for uid in self._ids], dtype=bool)
                sims = np.where(mask, sims, -np.inf)
            # 取 top_k
            top_k = min(top_k, len(sims))
            if top_k == 0:
                return []
            idx = np.argpartition(-sims, top_k - 1)[:top_k]
            idx = idx[np.argsort(-sims[idx])]
            results = [(self._ids[i], float(sims[i])) for i in idx if sims[i] > -np.inf]
            return results

    def size(self) -> int:
        return len(self._ids) if self._ids else 0


# ── 供应（Supply）向量索引单例 ───────────────────────────────
_supply_index: Optional[NumpyIndex] = None
_supply_index_lock = threading.Lock()
SUPPLY_INDEX_TTL = 300  # 5 分钟自动过期重建


def _get_supply_index():
    """获取供应向量索引（懒加载 + TTL 过期）"""
    global _supply_index, _supply_index_last_built
    now = time.time()
    last = globals().get('_supply_index_last_built', 0)
    if _supply_index is None or (now - last) > SUPPLY_INDEX_TTL:
        with _supply_index_lock:
            if _supply_index is None or (now - last) > SUPPLY_INDEX_TTL:
                _supply_index = NumpyIndex()
                _supply_index_last_built = now
                _load_supply_index(_supply_index)
    return _supply_index


def _load_supply_index(idx: NumpyIndex):
    """从 DB 加载所有有 embedding 的 Supply"""
    from supplies.models import SupplyEmbedding
    rows = SupplyEmbedding.objects.select_related('supply').filter(
        supply__status=1
    ).values_list('supply__uuid', 'embedding')
    ids = []
    vecs = []
    for uuid_bytes, emb in rows:
        if not emb or len(emb) < 10:
            continue
        ids.append(str(uuid_bytes))
        vecs.append(emb)
    if ids:
        idx.index(ids, vecs)
    logger.info(f"[vector-index:supply] loaded {idx.size()} vectors")


def rebuild_supply_index():
    """手动重建（admin 操作）"""
    global _supply_index_last_built
    idx = _get_supply_index()
    _load_supply_index(idx)
    _supply_index_last_built = time.time()
    return idx.size()


def search_supply_similar(query_vec, top_k=20, exclude_uuids=None):
    """外部调用入口"""
    idx = _get_supply_index()
    return idx.search(query_vec, top_k=top_k, exclude_ids=exclude_uuids)


def upsert_supply_embedding(u_uuid: str, vector: List[float]):
    """新增/更新单个供应的 embedding（写入侧调用）"""
    idx = _get_supply_index()
    idx.upsert([u_uuid], [vector])


def delete_supply_embedding(u_uuid: str):
    """删除单个（重建索引最简单）"""
    global _supply_index_last_built
    _supply_index = None
    _supply_index_last_built = 0


# ── 哈希工具（用于缓存 key）──────────────────────────────────
def stable_hash(obj) -> str:
    """对 obj 做稳定哈希，用于缓存 key"""
    s = repr(obj).encode('utf-8')
    return hashlib.md5(s).hexdigest()[:16]