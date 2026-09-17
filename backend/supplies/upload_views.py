"""图片上传接口"""
import os
import uuid as uuid_lib

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser

ALLOWED_EXT = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
MAX_SIZE = 5 * 1024 * 1024  # 5MB


class ImageUploadView(APIView):
    """
    POST /api/v1/upload/image/
    表单字段：file
    返回：{"code": 0, "data": {"url": "https://.../media/uploads/xxx.jpg"}}
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        f = request.FILES.get('file')
        if not f:
            return Response({'code': 4001, 'message': '缺少文件'}, status=status.HTTP_400_BAD_REQUEST)

        if f.size > MAX_SIZE:
            return Response({'code': 4002, 'message': '图片不能超过 5MB'}, status=status.HTTP_400_BAD_REQUEST)

        ext = os.path.splitext(f.name)[1].lower()
        if ext not in ALLOWED_EXT:
            return Response({'code': 4003, 'message': '仅支持 jpg/png/gif/webp'}, status=status.HTTP_400_BAD_REQUEST)

        # 存到 media/uploads/，文件名用 uuid 防止冲突与路径穿越
        rel_dir = 'uploads'
        abs_dir = os.path.join(settings.MEDIA_ROOT, rel_dir)
        os.makedirs(abs_dir, exist_ok=True)

        filename = f'{uuid_lib.uuid4().hex}{ext}'
        abs_path = os.path.join(abs_dir, filename)
        with open(abs_path, 'wb') as dest:
            for chunk in f.chunks():
                dest.write(chunk)

        # 构造可访问 URL（反代后 request.build_absolute_uri 可能拿不到 host，用配置兜底）
        media_url = settings.MEDIA_URL.strip('/')
        path = f'/{media_url}/{rel_dir}/{filename}'
        url = request.build_absolute_uri(path)
        # 若反代未传 Host 导致 URL 不完整（如 http://media/...），用站点域名兜底
        if not url or '://' not in url or url.split('://', 1)[1].split('/', 1)[0] in ('media', ''):
            base = getattr(settings, 'SITE_BASE_URL', 'https://www.asiamlhk.com').rstrip('/')
            url = f'{base}{path}'
        elif url.startswith('http://'):
            # 强制 https
            url = 'https://' + url[len('http://'):]

        return Response({'code': 0, 'data': {'url': url}, 'url': url}, status=status.HTTP_201_CREATED)
