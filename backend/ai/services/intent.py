"""
AI Intent Recognition & Tag Extraction & Match & Script Generation
"""
from .deepseek import DeepSeekClient

client = DeepSeekClient()

INTENT_PROMPT = """你是一个商务社交AI助手。根据用户输入，识别用户意图。

用户输入: {text}

可选意图类型：
- find_investors: 找投资人
- find_partners: 找合伙人
- find_talents: 找人才
- find_channels: 找渠道
- find_experts: 找行业专家
- publish_supply: 发布供需
- find_activity: 找活动
- find_community: 找社群
- general_chat: 闲聊

请以JSON格式返回：
{{"intent": "意图类型", "entities": {{"industry": "行业", "stage": "阶段", "amount": "金额"}}, "reply_text": "简短回复"}}
"""


def recognize_intent(text: str) -> dict:
    """意图识别"""
    messages = [
        {'role': 'system', 'content': '你是一个商务社交AI助手，回复简洁专业。'},
        {'role': 'user', 'content': INTENT_PROMPT.format(text=text)}
    ]
    response = client.chat(messages, temperature=0.3, max_tokens=300)
    
    # 解析JSON响应
    try:
        import re, json
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    
    return {
        'intent': 'general_chat',
        'entities': {},
        'reply_text': '我理解了您的需求，请问具体是哪方面的商务合作？'
    }


TAG_EXTRACT_PROMPT = """你是一个商务社交标签专家。根据用户输入的供需描述，提取最相关的标签。

用户输入: {text}
供需类型: {supply_type}

请返回3-5个最相关的标签ID和名称（使用中文），以及标题建议。

格式要求：
- 标签应从以下类别中选择：供给资源(资金/人脉/渠道/技术)、需求帮助(找资金/找人脉/找渠道/找技术)、行业经验、投资意向、社交兴趣
- 标题要简洁，15字以内

请以JSON格式返回：
{{"tags": [{{"id": 1, "name": "天使投资"}}], "title_suggestion": "建议标题", "quality_tips": ["建议1"]}}
"""


def extract_tags(text: str, supply_type: int = 1) -> dict:
    """从文本中提取标签"""
    messages = [
        {'role': 'system', 'content': '你是一个专业的商务社交标签专家。'},
        {'role': 'user', 'content': TAG_EXTRACT_PROMPT.format(text=text, supply_type=supply_type)}
    ]
    response = client.chat(messages, temperature=0.3, max_tokens=400)
    
    try:
        import re, json
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    
    return {
        'tags': [],
        'title_suggestion': text[:15],
        'quality_tips': []
    }


MATCH_PROMPT = """你是一个商务社交匹配专家。根据供需信息，评估匹配度并给出理由。

供给信息：{supply_title} - {supply_content}
供给方标签：{supply_tags}

被评估的用户信息：{profile_name}@{profile_company}，标签：{profile_tags}

请评估匹配度（0.0~1.0），给出匹配理由（50字以内）。

请以JSON格式返回：
{{"match_score": 0.85, "ai_reason": "匹配理由"}}
"""


def generate_match_reason(supply, profile) -> dict:
    """生成AI匹配理由"""
    messages = [
        {'role': 'system', 'content': '你是一个专业的商务社交匹配专家。'},
        {'role': 'user', 'content': MATCH_PROMPT.format(
            supply_title=supply.title,
            supply_content=supply.content[:200],
            supply_tags=str(supply.tags),
            profile_name=profile.real_name,
            profile_company=profile.company,
            profile_tags=str(list(profile.profile_tags.values_list('tag__name', flat=True)))
        )}
    ]
    response = client.chat(messages, temperature=0.3, max_tokens=200)
    
    try:
        import re, json
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    
    return {
        'match_score': 0.5,
        'ai_reason': '标签匹配，有潜在合作机会'
    }


SCRIPT_PROMPT = """你是一个商务社交话术专家。根据双方信息，生成自然的初次联系话术。

发起方：{from_name}，{from_company}，{from_position}
接收方：{to_name}，{to_company}，{to_position}
背景：{context}

要求：
- 话术要自然、简洁，不超过100字
- 体现双方的共同点或明确价值交换点
- 不要过于商业化

请以JSON格式返回：
{{"script": "话术内容", "variants": ["变体1", "变体2"]}}
"""


def generate_introduction_script(from_profile, to_profile, context: str = '') -> dict:
    """生成牵线话术"""
    messages = [
        {'role': 'system', 'content': '你是一个商务社交话术专家，擅长生成自然、专业的联系话术。'},
        {'role': 'user', 'content': SCRIPT_PROMPT.format(
            from_name=from_profile.real_name,
            from_company=from_profile.company,
            from_position=from_profile.position,
            to_name=to_profile.real_name,
            to_company=to_profile.company,
            to_position=to_profile.position,
            context=context
        )}
    ]
    response = client.chat(messages, temperature=0.7, max_tokens=400)
    
    try:
        import re, json
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    
    return {
        'script': f'{to_profile.real_name}您好，我是{from_profile.real_name}，想和您交流一下合作机会。',
        'variants': []
    }


FOLLOWUP_PROMPT = """你是商务社交跟进专家。用户需要给一个潜在合作伙伴发跟进消息。

发起方：{from_name}
接收方：{to_name}
背景：{context}

请生成一条自然的跟进消息，询问对方是否有空进一步交流。

要求：不超过80字，自然不生硬。

以JSON返回：
{{"suggested_message": "消息内容", "alternatives": ["备选1"]}}
"""


def generate_followup_script(from_profile, to_profile, context: str = '') -> dict:
    """生成跟进话术"""
    messages = [
        {'role': 'system', 'content': '你是一个商务社交跟进专家。'},
        {'role': 'user', 'content': FOLLOWUP_PROMPT.format(
            from_name=from_profile.real_name,
            to_name=to_profile.real_name,
            context=context
        )}
    ]
    response = client.chat(messages, temperature=0.7, max_tokens=300)
    
    try:
        import re, json
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    
    return {
        'suggested_message': f'{to_profile.real_name}您好，之前发的资料有没有机会看一下？希望能进一步交流。',
        'alternatives': []
    }
