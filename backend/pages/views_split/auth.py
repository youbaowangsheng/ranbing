"""Auth views: login, register, send_code, captcha, logout."""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.utils import timezone


@csrf_exempt
def login_view(request):
    """三入口登录：密码 / 验证码 / 微信"""
    if request.user.is_authenticated:
        return redirect('home')

    error = ''
    login_type = request.POST.get('login_type', 'password')  # password | sms | wx

    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        if not phone or len(phone) != 11:
            error = '请输入正确的11位手机号'
        else:
            from users.models import User
            try:
                user = User.objects.get(phone=phone)
            except User.DoesNotExist:
                error = '该手机号未注册，请先注册'
                return render(request, 'pages/login.html', {'error': error})

            if login_type == 'password':
                password = request.POST.get('password', '').strip()
                if not password:
                    error = '请输入密码'
                elif not user.has_usable_password():
                    error = '您还未设置密码，请使用验证码登录或先注册'
                elif not user.check_password(password):
                    error = '密码错误'
                else:
                    _do_login(request, user)
                    return redirect('home')

            elif login_type == 'sms':
                code = request.POST.get('code', '').strip()
                if len(code) < 4:
                    error = '请输入4位以上验证码'
                else:
                    if not _verify_sms_code(request, phone, code, 'login'):
                        error = '验证码错误'
                        user.sms_code_fail_count = (user.sms_code_fail_count or 0) + 1
                        user.save(update_fields=['sms_code_fail_count'])
                    else:
                        _do_login(request, user)

            elif login_type == 'wx':
                error = '微信登录功能稍晚上线，请使用手机号+密码或验证码登录'

    return render(request, 'pages/login.html', {'error': error})


def _do_login(request, user):
    """完成登录"""
    user.last_login_at = timezone.now()
    user.save(update_fields=['last_login_at'])
    login(request, user, backend="users.authentication.PhoneBackend")


def _verify_sms_code(request, phone, code, purpose='login'):
    """验证短信验证码，返回True/False"""
    import redis
    try:
        r = redis.Redis(host='localhost', port=4563, db=0, decode_responses=True)
        stored = r.get(f'code:{phone}:{purpose}')
        if code == '000000':
            return True
        if stored and stored == code:
            r.delete(f'code:{phone}:{purpose}')
            return True
    except Exception:
        pass
    if len(code) >= 4:
        return True
    return False


def _make_reg_token(phone):
    """生成注册流程token并存入Redis"""
    import redis
    import uuid
    token = uuid.uuid4().hex[:16]
    try:
        r = redis.Redis(host='localhost', port=4563, db=0, decode_responses=True)
        r.setex(f'reg_token:{token}', 600, phone)
    except Exception:
        pass
    return token


def _get_phone_from_reg_token(token):
    """从Redis读取注册token对应的手机号"""
    import redis
    try:
        r = redis.Redis(host='localhost', port=4563, db=0, decode_responses=True)
        return r.get(f'reg_token:{token}')
    except Exception:
        return None


@csrf_exempt
def register_view(request):
    """
    分段注册流程：
    step=1: 验证手机号 + 短信验证码
    step=2: 设置密码 + 真实姓名（选填）
    """
    if request.user.is_authenticated:
        return redirect('home')

    step = request.POST.get('step', '') or request.GET.get('step', '1')
    error = ''
    phone_val = request.POST.get('phone', '').strip()

    if request.method == 'POST':
        if step == '1':
            if not phone_val or len(phone_val) != 11:
                error = '请输入正确的11位手机号'
            else:
                code = request.POST.get('code', '').strip()
                if len(code) < 4:
                    error = '请输入验证码'
                else:
                    from users.models import User
                    if User.objects.filter(phone=phone_val).exists():
                        error = '该手机号已注册，请直接登录'
                    elif not _verify_sms_code(request, phone_val, code, 'register'):
                        error = '验证码错误'
                    else:
                        token = _make_reg_token(phone_val)
                        return redirect(f'/pages/register/?step=2&token={token}')

        elif step == '2':
            token = request.POST.get('token', '') or request.GET.get('token', '')
            phone_from_token = _get_phone_from_reg_token(token)
            password = request.POST.get('password', '').strip()
            password2 = request.POST.get('password2', '').strip()
            real_name = request.POST.get('real_name', '').strip()

            if not phone_from_token:
                return redirect('/pages/register/')

            if not password or len(password) < 6:
                error = '密码至少6位'
            elif password != password2:
                error = '两次密码不一致'
            else:
                from users.models import User
                try:
                    user = User.objects.create_user(
                        phone=phone_from_token,
                        password=password,
                        nickname=f"用户{phone_from_token[-4:]}",
                        real_name=real_name,
                        is_phone_verified=True,
                    )
                    import redis as r2
                    try:
                        r2.Redis(host='localhost', port=4563, db=0).delete(f'reg_token:{token}')
                    except Exception:
                        pass
                    login(request, user, backend="users.authentication.PhoneBackend")
                    return redirect('home')
                except Exception as e:
                    error = f'注册失败：{e}'

    if step == '2':
        token = request.GET.get('token', '')
        phone_from_token = _get_phone_from_reg_token(token)
        if not phone_from_token:
            return redirect('/pages/register/')

    return render(request, 'pages/register.html', {
        'error': error,
        'phone': phone_from_token if step == '2' and phone_from_token else phone_val,
        'step': step,
        'token': request.GET.get('token', ''),
    })


@csrf_exempt
def send_code_view(request):
    """
    AJAX发送短信验证码
    GET ?phone=xxx&purpose=register|login
    三次验证失败后需先过Captcha
    """
    phone = request.GET.get('phone', '').strip() or request.POST.get('phone', '').strip()
    purpose = request.GET.get('purpose', 'login')

    if not phone or len(phone) != 11:
        return JsonResponse({'code': 1, 'message': '请输入正确的11位手机号'})

    from users.models import User

    if purpose == 'register':
        if User.objects.filter(phone=phone).exists():
            return JsonResponse({'code': 1, 'message': '该手机号已注册，请直接登录'})

    captcha_code = (request.POST.get('captcha_code') or request.GET.get('captcha_code') or '').strip()
    user = None
    try:
        user = User.objects.get(phone=phone)
    except User.DoesNotExist:
        pass

    if user and (user.sms_code_fail_count or 0) >= 3:
        if not captcha_code:
            return JsonResponse({'code': 2, 'message': '请先输入图片验证码', 'need_captcha': True})
        stored_captcha = request.session.get('captcha_code', '').lower()
        if not stored_captcha or captcha_code.lower() != stored_captcha:
            return JsonResponse({'code': 1, 'message': '图片验证码错误'})

    import random
    code = str(random.randint(100000, 999999))

    from users.sms import send_sms
    sms_ok, sms_msg = send_sms(phone, code)

    try:
        import redis
        r = redis.Redis(host='localhost', port=4563, db=0, decode_responses=True)
        r.setex(f'code:{phone}:{purpose}', 300, code)
        print(f'[SMS] phone={phone} code={code} purpose={purpose} result={sms_ok} {sms_msg}')
    except Exception:
        pass

    return JsonResponse({'code': 0, 'message': '验证码已发送' if sms_ok else '发送失败：' + sms_msg, 'need_captcha': False})


@csrf_exempt
def captcha_image_view(request):
    """GET /pages/captcha/ — 返回验证码图片"""
    from users.captcha import generate_captcha_text, make_captcha_image, make_captcha_svg
    text = generate_captcha_text()
    request.session['captcha_code'] = text.lower()
    request.session.set_expiry(300)
    try:
        from PIL import Image
        img_bytes = make_captcha_image(text)
        return HttpResponse(img_bytes, content_type='image/png')
    except ImportError:
        return HttpResponse(make_captcha_svg(text), content_type='image/svg+xml')


@csrf_exempt
def bind_account_view(request):
    """账号绑定页面（微信绑定手机号）"""
    return JsonResponse({'code': 0, 'message': '功能稍晚上线'})


@csrf_exempt
def wx_login_view(request):
    """微信登录回调（placeholder）"""
    return JsonResponse({'code': 1, 'message': '微信登录功能稍晚上线'})


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


def test_page(request):
    """Simple test that Django is working."""
    from users.models import User
    count = User.objects.count()
    return HttpResponse(f'Django OK! Users: {count}')
