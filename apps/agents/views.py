from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count
from apps.core.models import AgentConfig
from .serializers import AgentConfigSerializer
from apps.fipai_client import get_fipai_client


class BusinessAgentViewSet(viewsets.ModelViewSet):
    """Agent业务配置 API - 核心功能"""

    serializer_class = AgentConfigSerializer

    def get_queryset(self):
        """获取当前用户的Agent配置"""
        user = self.request.user
        if not user.is_authenticated:
            return AgentConfig.objects.none()
        return AgentConfig.objects.filter(user=user)

    def create(self, request, *args, **kwargs):
        """创建Agent：在FIPAI创建 + 本地保存配置"""
        user = request.user
        if not user.is_authenticated:
            return Response({'error': '需要登录'}, status=status.HTTP_401_UNAUTHORIZED)

        # 调用FIPAI API创建Agent
        fipai_data = {
            'name': request.data.get('agent_name', ''),
            'agent_type': request.data.get('agent_type', 'custom'),
            'description': request.data.get('description', ''),
            'capabilities': request.data.get('capabilities', []),
        }

        try:
            fipai_client = get_fipai_client()
            fipai_agent = fipai_client.create_agent(fipai_data)
        except Exception as e:
            return Response({'error': f'创建FIPAI Agent失败: {str(e)}'}, status=status.HTTP_502_BAD_GATEWAY)

        # 本地保存业务配置
        agent_config = AgentConfig.objects.create(
            user=user,
            fipai_agent_id=fipai_agent.get('id'),
            agent_name=request.data.get('agent_name', ''),
            agent_type=request.data.get('agent_type', 'custom'),
            config=request.data.get('config', {}),
        )

        return Response(AgentConfigSerializer(agent_config).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """更新Agent：更新本地配置 + 可选同步FIPAI"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # 如果改了名字或类型，同步到FIPAI
        if 'agent_name' in request.data or 'agent_type' in request.data or 'description' in request.data:
            try:
                fipai_client = get_fipai_client()
                fipai_data = {}
                if 'agent_name' in request.data:
                    fipai_data['name'] = request.data['agent_name']
                if 'agent_type' in request.data:
                    fipai_data['agent_type'] = request.data['agent_type']
                if 'description' in request.data:
                    fipai_data['description'] = request.data['description']
                if 'is_active' in request.data:
                    fipai_data['is_active'] = request.data['is_active']

                if fipai_data and instance.fipai_agent_id:
                    fipai_client.update_agent(instance.fipai_agent_id, fipai_data)
            except Exception as e:
                return Response({'error': f'同步FIPAI失败: {str(e)}'}, status=status.HTTP_502_BAD_GATEWAY)

        # 更新本地
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """删除Agent：删除FIPAI Agent + 清理本地配置"""
        instance = self.get_object()

        # 删除FIPAI Agent
        if instance.fipai_agent_id:
            try:
                fipai_client = get_fipai_client()
                fipai_client.delete_agent(instance.fipai_agent_id)
            except Exception:
                pass  # 忽略FIPAI删除失败，继续清理本地

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def types(self, request):
        """获取支持的Agent类型"""
        return Response([
            {'value': 'community', 'label': '社群助手', 'description': '社群内容管理、自动回复'},
            {'value': 'matching', 'label': '匹配助手', 'description': '供需匹配、精准推送'},
            {'value': 'publish', 'label': '发布助手', 'description': '多平台内容发布'},
            {'value': 'supply_demand', 'label': '供需助手', 'description': '供应需求撮合'},
            {'value': 'network', 'label': '人脉助手', 'description': '人脉拓展、关系管理'},
            {'value': 'event', 'label': '活动助手', 'description': '活动策划、日程管理'},
            {'value': 'custom', 'label': '自定义', 'description': '自定义Agent类型'},
        ])

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """获取单个Agent的使用统计"""
        instance = self.get_object()
        from django.db.models import Sum
        from apps.core.models import UsageRecord

        stats = UsageRecord.objects.filter(agent=instance).aggregate(
            total_tokens=Sum('tokens'),
            total_requests=Sum('request_count'),
            total_cost=Sum('cost')
        )
        return Response({
            'agent_name': instance.agent_name,
            'total_tokens': stats['total_tokens'] or 0,
            'total_requests': stats['total_requests'] or 0,
            'total_cost': float(stats['total_cost'] or 0),
        })