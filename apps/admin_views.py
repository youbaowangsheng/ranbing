"""
Console Admin API - 调用 backend 审核 API
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from apps.admin_client import get_admin_client


@api_view(['GET', 'POST'])
def activities_pending(request):
    """待审核活动列表"""
    client = get_admin_client()
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 20))
    return Response(client.get_activities_pending(page, page_size))


@api_view(['POST'])
def activities_approve(request, uuid):
    """审核通过活动"""
    client = get_admin_client()
    return Response(client.approve_activity(uuid))


@api_view(['POST'])
def activities_reject(request, uuid):
    """审核拒绝活动"""
    client = get_admin_client()
    comment = request.data.get('comment', '')
    return Response(client.reject_activity(uuid, comment))


@api_view(['GET'])
def communities_pending(request):
    """待审核社群列表"""
    client = get_admin_client()
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 20))
    return Response(client.get_communities_pending(page, page_size))


@api_view(['POST'])
def communities_approve(request, uuid):
    """审核通过社群"""
    client = get_admin_client()
    return Response(client.approve_community(uuid))


@api_view(['POST'])
def communities_reject(request, uuid):
    """审核拒绝社群"""
    client = get_admin_client()
    return Response(client.reject_community(uuid))


@api_view(['GET'])
def supplies_pending(request):
    """待审核供需列表"""
    client = get_admin_client()
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 20))
    return Response(client.get_supplies_pending(page, page_size))


@api_view(['POST'])
def supplies_approve(request, uuid):
    """审核通过供需"""
    client = get_admin_client()
    return Response(client.approve_supply(uuid))


@api_view(['POST'])
def supplies_reject(request, uuid):
    """审核拒绝供需"""
    client = get_admin_client()
    return Response(client.reject_supply(uuid))


@api_view(['GET'])
def messages_pending(request):
    """待审核消息列表"""
    client = get_admin_client()
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 20))
    return Response(client.get_messages_pending(page, page_size))


@api_view(['POST'])
def messages_audit(request, community_uuid, msg_id):
    """审核消息"""
    client = get_admin_client()
    action = request.data.get('action', 'approve')
    return Response(client.audit_message(community_uuid, int(msg_id), action))