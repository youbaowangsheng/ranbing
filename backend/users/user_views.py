"""
用户管理视图 - 后端运营控制台
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from .models import User
from .serializers import UserSerializer, UserListSerializer


class UserViewSet(viewsets.GenericViewSet):
    """用户管理API"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = User.objects.all()
        search = self.request.query_params.get('search', '')
        if search:
            qs = qs.filter(
                Q(nickname__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search)
            )
        return qs.order_by('-id')

    def get_serializer_class(self):
        if self.action == 'list':
            return UserListSerializer
        return UserSerializer

    def list(self, request):
        qs = self.get_queryset()
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(UserListSerializer(page, many=True).data)
        return Response({'code': 0, 'data': UserListSerializer(qs, many=True).data})

    def retrieve(self, request, pk=None):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'code': 2001, 'message': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'code': 0, 'data': UserSerializer(user).data})

    @action(detail=True, methods=['post'])
    def disable(self, request, pk=None):
        """禁用/启用用户"""
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'code': 2001, 'message': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)
        disable = request.data.get('disable', True)
        user.status = 9 if disable else 1
        user.save(update_fields=['status'])
        return Response({'code': 0, 'message': '操作成功'})

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """用户统计摘要"""
        total = User.objects.count()
        verified = User.objects.filter(is_verified=True).count()
        active = User.objects.filter(status=1).count()
        return Response({
            'code': 0,
            'data': {
                'total': total,
                'verified': verified,
                'active': active
            }
        })