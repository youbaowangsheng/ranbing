#!/usr/bin/env bash
# deploy-w4-ai-platform.sh
#
# 部署 W4 AI 平台架构改造到生产
# 用法：bash deploy-w4-ai-platform.sh
#
# 服务器：root@8.138.90.48
# 部署路径：/www/ranbing/backend

set -e

REMOTE_HOST="root@8.138.90.48"
REMOTE_DIR="/www/ranbing/backend"
LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "==================================="
echo " W4 AI 平台部署脚本"
echo " 服务器: $REMOTE_HOST"
echo " 路径: $REMOTE_DIR"
echo "==================================="
echo ""

# ── 1. 备份 ──────────────────────────────────────────
echo "[1/7] 备份原文件..."
ssh $REMOTE_HOST << 'EOF'
cd /www/ranbing/backend
BACKUP_DIR="/tmp/ranbing-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p $BACKUP_DIR
cp -r ai/ $BACKUP_DIR/ 2>/dev/null || true
cp -r supplies/ $BACKUP_DIR/ 2>/dev/null || true
cp -r profiles/ $BACKUP_DIR/ 2>/dev/null || true
cp -r activities/ $BACKUP_DIR/ 2>/dev/null || true
cp -r communities/ $BACKUP_DIR/ 2>/dev/null || true
echo "  备份到 $BACKUP_DIR"
EOF

# ── 2. 上传新文件 ────────────────────────────────────
echo ""
echo "[2/7] 上传新文件..."
rsync -avz --include='ai/gateway.py' \
  --include='ai/registry.py' \
  --include='ai/vector_index.py' \
  --include='ai/profile_context.py' \
  --include='ai/views.py' \
  --include='ai/urls.py' \
  --include='ai/apps.py' \
  --include='ai/prompts/' \
  --include='ai/services/intent.py' \
  --include='ai/services/deepseek.py' \
  --include='supplies/ai_tools.py' \
  --include='supplies/views.py' \
  --include='profiles/ai_tools.py' \
  --include='profiles/views.py' \
  --include='activities/ai_tools.py' \
  --include='communities/ai_tools.py' \
  --exclude='*' \
  $LOCAL_DIR/ $REMOTE_HOST:$REMOTE_DIR/

# ── 3. 删除 ai/tools.py ───────────────────────────────
echo ""
echo "[3/7] 删除老 ai/tools.py..."
ssh $REMOTE_HOST << 'EOF'
if [ -f /www/ranbing/backend/ai/tools.py ]; then
    rm /www/ranbing/backend/ai/tools.py
    echo "  已删除 ai/tools.py"
else
    echo "  不存在，跳过"
fi
EOF

# ── 4. 安装依赖 ────────────────────────────────────
echo ""
echo "[4/7] 安装 Python 依赖..."
ssh $REMOTE_HOST << 'EOF'
cd /www/ranbing/backend
./venv/bin/pip install numpy pyyaml httpx 2>&1 | tail -5
EOF

# ── 5. 数据库迁移（如果有新 migration） ─────────────
echo ""
echo "[5/7] 检查数据库迁移..."
ssh $REMOTE_HOST << 'EOF'
cd /www/ranbing/backend
./venv/bin/python manage.py makemigrations --dry-run 2>&1 | head -20
EOF

# ── 6. 重启服务 ────────────────────────────────────
echo ""
echo "[6/7] 重启服务..."
ssh $REMOTE_HOST << 'EOF'
systemctl restart ranbing
sleep 3
systemctl status ranbing | head -10
EOF

# ── 7. 验证 ────────────────────────────────────
echo ""
echo "[7/7] 验证关键日志..."
echo ""
echo "  期望看到："
echo "    [ai-registry] registered tool: search_supplies (from supplies)"
echo "    [ai-registry] registered tool: search_profiles (from profiles)"
echo "    [ai-registry] registered tool: search_activities (from activities)"
echo "    [ai-registry] registered tool: search_communities (from communities)"
echo "    [ai] 向量索引预热完成: N 条"
echo ""
echo "  实际日志："
ssh $REMOTE_HOST "journalctl -u ranbing -n 200 | grep -E 'ai-registry|ai-gw|vector-index' | tail -10"

# ── 8. 接口回归 ────────────────────────────────────
echo ""
echo "[8/8] 接口冒烟..."
ssh $REMOTE_HOST << 'EOF'
echo "  - GET /api/v1/supplies/?page=1"
curl -s -o /dev/null -w "    status: %{http_code}, time: %{time_total}s\n" \
  https://www.asiamlhk.com/api/v1/supplies/?page=1
echo "  - POST /api/v1/ai/chat/ (匿名)"
curl -s -o /dev/null -w "    status: %{http_code}, time: %{time_total}s\n" \
  -X POST https://www.asiamlhk.com/api/v1/ai/chat/ \
  -H 'Content-Type: application/json' \
  -d '{"message":"test"}'
EOF

echo ""
echo "==================================="
echo " 部署完成"
echo "==================================="
echo ""
echo "回滚（如果出问题）："
echo "  ssh $REMOTE_HOST 'cd $REMOTE_DIR && BACKUP=\$(ls -td /tmp/ranbing-backup-* | head -1) && cp -r \$BACKUP/* . && systemctl restart ranbing'"