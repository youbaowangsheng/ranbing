"""
图片验证码 Captcha 生成
"""
import random
import io
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt


# 简单字符集（不含0/O,1/l/I等易混淆）
CHARS = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'


def generate_captcha_text(length=4):
    return ''.join(random.choice(CHARS) for _ in range(length))


def make_captcha_image(text):
    """生成验证码图片（内存）"""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        # 没有PIL时返回简单SVG
        return make_captcha_svg(text)

    width, height = 120, 40
    image = Image.new('RGB', (width, height), color=(245, 247, 250))
    draw = ImageDraw.Draw(image)

    # 画干扰线
    for _ in range(3):
        x1, y1 = random.randint(0, width), random.randint(0, height)
        x2, y2 = random.randint(0, width), random.randint(0, height)
        draw.line([(x1, y1), (x2, y2)], fill=(200, 210, 220), width=1)

    # 画字符
    try:
        font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 24)
    except Exception:
        font = ImageFont.load_default()

    avg_width = width // len(text)
    for i, ch in enumerate(text):
        x = avg_width * i + random.randint(2, 6)
        y = random.randint(4, 10)
        color = (random.randint(30, 80), random.randint(60, 120), random.randint(150, 200))
        draw.text((x, y), ch, font=font, fill=color)

    buf = io.BytesIO()
    image.save(buf, format='PNG')
    return buf.getvalue()


def make_captcha_svg(text):
    """无PIL时的SVG fallback"""
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="120" height="40"><rect fill="#f5f7fa" width="120" height="40"/>'
    for i, ch in enumerate(text):
        x = 15 + i * 24
        y = 28
        color = f'rgb({random.randint(30,80)},{random.randint(60,120)},{random.randint(150,200)})'
        svg += f'<text x="{x}" y="{y}" font-family="Arial" font-size="26" fill="{color}">{ch}</text>'
    svg += '</svg>'
    return svg.encode()


@csrf_exempt
def captcha_image(request):
    """验证码图片接口 GET /users/captcha/"""
    text = generate_captcha_text()
    # 存入 session
    request.session['captcha_code'] = text.lower()
    request.session.set_expiry(300)

    try:
        from PIL import Image, ImageDraw, ImageFont
        img_bytes = make_captcha_image(text)
        return HttpResponse(img_bytes, content_type='image/png')
    except ImportError:
        return HttpResponse(make_captcha_svg(text), content_type='image/svg+xml')


@csrf_exempt
def captcha_refresh(request):
    """刷新验证码"""
    text = generate_captcha_text()
    request.session['captcha_code'] = text.lower()
    request.session.set_expiry(300)
    return JsonResponse({'code': 0, 'captcha_id': text})  # 前端自己刷新图片


def verify_captcha(request, user_input):
    """验证验证码是否正确"""
    stored = request.session.get('captcha_code', '').lower()
    return stored and user_input.lower() == stored
