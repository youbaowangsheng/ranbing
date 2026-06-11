"""
内容统计API
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from activities.models import Activity
from communities.models import Community, Message
from supplies.models import Supply


class ContentStatsView(APIView):
    """内容统计"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        activities_pending = Activity.objects.filter(audit_status=0).count()
        activities_approved = Activity.objects.filter(audit_status=1).count()
        activities_rejected = Activity.objects.filter(audit_status=2).count()

        communities_approved = Community.objects.filter(status__in=[1, 2]).count()

        supplies_pending = Supply.objects.filter(audit_status=0).count()
        supplies_approved = Supply.objects.filter(audit_status=1).count()
        supplies_rejected = Supply.objects.filter(audit_status=2).count()

        messages_pending = Message.objects.filter(audit_status=0).count()
        messages_approved = Message.objects.filter(audit_status=1).count()
        messages_rejected = Message.objects.filter(audit_status=2).count()

        return Response({
            'code': 0,
            'data': {
                'activities': {
                    'pending': activities_pending,
                    'approved': activities_approved,
                    'rejected': activities_rejected,
                },
                'communities': {
                    'pending': 0,
                    'approved': communities_approved,
                    'rejected': 0,
                },
                'supplies': {
                    'pending': supplies_pending,
                    'approved': supplies_approved,
                    'rejected': supplies_rejected,
                },
                'messages': {
                    'pending': messages_pending,
                    'approved': messages_approved,
                    'rejected': messages_rejected,
                },
            }
        })