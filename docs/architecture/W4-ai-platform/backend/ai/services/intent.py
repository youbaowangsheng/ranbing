"""
AI Intent Recognition & Tag Extraction & Match & Script Generation

所有 LLM 调用走 gateway.py。
所有 prompt 从 ai/prompts/*.yaml 加载，修改 prompt 不需要改代码。
"""
import re
import json
import logging
from ..gateway import gateway
from ..prompts import render as render_prompt, get_system

logger = logging.getLogger(__name__)


def _parse_json(response: str, fallback: dict) -> dict:
    """从 LLM 文本里抽 JSON，失败返回 fallback"""
    try:
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            return json.loads(match.group())
    except (json.JSONDecodeError, AttributeError):
        pass
    return fallback


def _build_messages(prompt_id: str, user_content: str) -> list:
    """构造 messages 数组，自动读取 YAML 的 system 部分"""
    system = get_system(prompt_id) or '你是一个商务社交AI助手。'
    return [
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': user_content},
    ]


def recognize_intent(text: str, user_id=None) -> dict:
    """意图识别"""
    try:
        user_content = render_prompt('intent_recognition', text=text)
        response = gateway.chat(
            _build_messages('intent_recognition', user_content),
            temperature=0.3, max_tokens=300,
            prompt_id='recognize_intent', user_id=user_id,
        )
    except Exception as e:
        logger.exception(f"[intent] error: {e}")
        return {
            'intent': 'general_chat',
            'entities': {},
            'reply_text': 'AI暂时不可用，请稍后再试',
        }
    return _parse_json(response, {
        'intent': 'general_chat',
        'entities': {},
        'reply_text': '我理解了您的需求，请问具体是哪方面的商务合作？'
    })


def extract_tags(text: str, supply_type: int = 1, user_id=None) -> dict:
    """从文本中提取标签"""
    try:
        user_content = render_prompt('tag_extract', text=text, supply_type=supply_type)
        response = gateway.chat(
            _build_messages('tag_extract', user_content),
            temperature=0.3, max_tokens=400,
            prompt_id='extract_tags', user_id=user_id,
        )
    except Exception as e:
        logger.exception(f"[extract_tags] error: {e}")
        return {'tags': [], 'title_suggestion': text[:15], 'quality_tips': []}
    return _parse_json(response, {
        'tags': [],
        'title_suggestion': text[:15],
        'quality_tips': []
    })


def generate_match_reason(supply, profile, user_id=None) -> dict:
    """生成 AI 匹配理由（单个）"""
    try:
        user_content = render_prompt(
            'match_reason',
            supply_title=supply.title,
            supply_content=supply.content[:200],
            supply_tags=str(supply.tags),
            profile_name=profile.real_name,
            profile_company=profile.company,
            profile_tags=str(list(profile.profile_tags.values_list('tag__name', flat=True))),
            overlap_count=str(len(set(supply.tags or []) & set(
                pt.tag_id for pt in profile.profile_tags.all()
            ))),
        )
        response = gateway.chat(
            _build_messages('match_reason', user_content),
            temperature=0.3, max_tokens=200,
            prompt_id='generate_match_reason', user_id=user_id,
        )
    except Exception as e:
        logger.exception(f"[match_reason] error: {e}")
        return {'match_score': 0.5, 'ai_reason': '标签匹配，有潜在合作机会'}
    return _parse_json(response, {
        'match_score': 0.5,
        'ai_reason': '标签匹配，有潜在合作机会'
    })


def generate_introduction_script(from_profile, to_profile, context: str = '', user_id=None) -> dict:
    """生成牵线话术"""
    try:
        user_content = render_prompt(
            'intro_script',
            from_name=from_profile.real_name,
            from_company=from_profile.company,
            from_position=from_profile.position,
            to_name=to_profile.real_name,
            to_company=to_profile.company,
            to_position=to_profile.position,
            context=context,
        )
        response = gateway.chat(
            _build_messages('intro_script', user_content),
            temperature=0.7, max_tokens=400,
            prompt_id='generate_introduction_script', user_id=user_id,
        )
    except Exception as e:
        logger.exception(f"[intro_script] error: {e}")
        return {
            'script': f'{to_profile.real_name}您好，我是{from_profile.real_name}，想和您交流一下合作机会。',
            'variants': [],
        }
    return _parse_json(response, {
        'script': f'{to_profile.real_name}您好，我是{from_profile.real_name}，想和您交流一下合作机会。',
        'variants': []
    })


def generate_followup_script(from_profile, to_profile, context: str = '', user_id=None) -> dict:
    """生成跟进话术"""
    try:
        user_content = render_prompt(
            'followup_script',
            from_name=from_profile.real_name,
            to_name=to_profile.real_name,
            context=context,
        )
        response = gateway.chat(
            _build_messages('followup_script', user_content),
            temperature=0.7, max_tokens=300,
            prompt_id='generate_followup_script', user_id=user_id,
        )
    except Exception as e:
        logger.exception(f"[followup_script] error: {e}")
        return {
            'suggested_message': f'{to_profile.real_name}您好，之前发的资料有没有机会看一下？希望能进一步交流。',
            'alternatives': [],
        }
    return _parse_json(response, {
        'suggested_message': f'{to_profile.real_name}您好，之前发的资料有没有机会看一下？希望能进一步交流。',
        'alternatives': []
    })
