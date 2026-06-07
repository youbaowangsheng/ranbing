"""全局异常处理"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """统一错误响应格式"""
    response = exception_handler(exc, context)

    if response is not None:
        import sys
        exc_type = exc.__class__.__name__ if exc else 'Unknown'
        print(f'[Exception] {exc_type}: {exc}', file=sys.stderr)
        print(f'[Response data] {response.data}', file=sys.stderr)
        # DRF标准错误
        if isinstance(response.data, dict):
            code = response.status_code
            # 提取详细错误信息
            if 'detail' in response.data:
                message = str(response.data['detail'])
            else:
                # 收集所有字段错误
                messages = []
                for field, errors in response.data.items():
                    if isinstance(errors, list):
                        for e in errors:
                            messages.append(f'{field}: {e}')
                    else:
                        messages.append(f'{field}: {errors}')
                message = '; '.join(messages) if messages else str(response.data)
            response.data = {
                'code': code,
                'message': message,
                'data': None
            }
        elif isinstance(response.data, list):
            response.data = {
                'code': response.status_code,
                'message': response.data[0] if response.data else '请求错误',
                'data': None
            }
    else:
        # 未捕获的异常
        import traceback
        print(f'[Server Error] {traceback.format_exc()}')
        response = Response({
            'code': 3001,
            'message': '系统繁忙，请稍后重试',
            'data': None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return response
