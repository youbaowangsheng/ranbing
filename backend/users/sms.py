"""
阿里云短信发送封装
文档: https://help.aliyun.com/document_detail/101419.html
"""
import random
import json
import base64
import time
import hmac
import hashlib
import urllib.parse
from datetime import datetime


ALIYUN_ACCESS_KEY_ID = 'LTAI5t5qBjRMNDJMN1PN25bt'
ALIYUN_ACCESS_KEY_SECRET = 'p1EEqf45q97hrtycNlzMlo1gIg9PRg'
ALIYUN_SMS_SIGN_NAME = '湖南器宇'
ALIYUN_SMS_TEMPLATE_CODE = 'SMS_481780008'
DEMO_MODE = False


def _make_signature(method, path, params, secret):
    """
    阿里云 API 签名 (HMAC-SHA1)
    method: GET 或 POST
    path: 如 /
    params: dict of query parameters
    secret: AccessKeySecret
    """
    # 1. Sort and encode params
    sorted_params = sorted(params.items())
    encoded_params = '&'.join(f'{urllib.parse.quote(str(k))}={urllib.parse.quote(str(v))}' for k, v in sorted_params)

    # 2. String to sign
    string_to_sign = f'{method}&{urllib.parse.quote(path, safe="")}&{urllib.parse.quote(encoded_params, safe="")}'

    # 3. HMAC-SHA1
    h = hmac.new(f'{secret}&'.encode('utf-8'), string_to_sign.encode('utf-8'), hashlib.sha1)
    signature = base64.b64encode(h.digest()).decode('utf-8')

    return signature


def send_sms(phone, code, template_code=None):
    """
    发送短信验证码
    phone: 手机号
    code: 验证码
    template_code: 短信模板CODE，默认用配置的
    返回: (success, message)
    """
    import urllib.request

    if DEMO_MODE:
        print(f"[SMS DEMO] phone={phone} code={code}")
        return True, "demo模式"

    template_code = template_code or ALIYUN_SMS_TEMPLATE_CODE
    sign_name = ALIYUN_SMS_SIGN_NAME
    access_key_id = ALIYUN_ACCESS_KEY_ID
    access_key_secret = ALIYUN_ACCESS_KEY_SECRET

    domain = 'dysmsapi.aliyuncs.com'
    path = '/'

    params = {
        'AccessKeyId': access_key_id,
        'SignatureMethod': 'HMAC-SHA1',
        'SignatureVersion': '1.0',
        'SignatureNonce': f'{time.time()}{random.randint(1000, 9999)}',
        'Timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'Format': 'JSON',
        'Version': '2017-05-25',
        'Action': 'SendSms',
        'SignName': sign_name,
        'TemplateCode': template_code,
        'PhoneNumbers': phone,
        'TemplateParam': json.dumps({'code': code}),
    }

    signature = _make_signature('GET', path, params, access_key_secret)
    params['Signature'] = signature

    query_string = '&'.join(
        f'{urllib.parse.quote(str(k))}={urllib.parse.quote(str(v))}' for k, v in sorted(params.items())
    )
    url = f'https://{domain}{path}?{query_string}'

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode('utf-8'))

        if result.get('Code') == 'OK':
            return True, "发送成功"
        else:
            return False, result.get('Message', str(result))
    except Exception as e:
        return False, str(e)


def generate_code(length=6):
    """生成随机验证码"""
    return ''.join([str(random.randint(0, 9)) for _ in range(length)])