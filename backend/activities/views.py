"""Activities视图"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Activity, ActivityEnrollment
from .serializers import ActivitySerializer, ActivityEnrollmentSerializer
from profiles.models import Profile


class ActivityViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Activity.objects.select_related('organizer__user').filter(
            audit_status=1, status__in=[1, 2]
        )

    def list(self, request):
        qs = self.get_queryset()
        act_type = request.query_params.get('type')
        school = request.query_params.get('school', '')

        if act_type:
            qs = qs.filter(activity_type=int(act_type))
        if school:
            qs = qs.filter(host_school__icontains=school)

        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(ActivitySerializer(page, many=True).data)
        return Response({'code': 0, 'data': ActivitySerializer(qs, many=True).data})

    def retrieve(self, request, pk=None):
        try:
            activity = self.get_queryset().get(uuid=pk)
        except Activity.DoesNotExist:
            return Response({'code': 2001, 'message': '活动不存在'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'code': 0, 'data': ActivitySerializer(activity).data})

    @action(detail=True, methods=['post'])
    def enroll(self, request, pk=None):
        try:
            activity = Activity.objects.get(uuid=pk)
        except Activity.DoesNotExist:
            return Response({'code': 2001, 'message': '活动不存在'}, status=status.HTTP_404_NOT_FOUND)

        profile, _ = Profile.objects.get_or_create(user=request.user)
        enrollment, created = ActivityEnrollment.objects.get_or_create(
            activity=activity, profile=profile, defaults={'enrollment_status': 1}
        )
        if not created:
            return Response({'code': 2003, 'message': '您已报名过该活动'}, status=status.HTTP_400_BAD_REQUEST)

        activity.current_attendees += 1
        activity.save(update_fields=['current_attendees'])
        return Response({'code': 0, 'message': '报名成功'}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """待审核活动列表"""
        qs = Activity.objects.select_related('organizer__user').filter(audit_status=0)
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(ActivitySerializer(page, many=True).data)
        return Response({'code': 0, 'data': ActivitySerializer(qs, many=True).data})

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """审核通过"""
        try:
            activity = Activity.objects.get(uuid=pk)
        except Activity.DoesNotExist:
            return Response({'code': 2001, 'message': '活动不存在'}, status=status.HTTP_404_NOT_FOUND)
        activity.audit_status = 1
        activity.save(update_fields=['audit_status'])
        return Response({'code': 0, 'message': '审核通过'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """审核拒绝"""
        try:
            activity = Activity.objects.get(uuid=pk)
        except Activity.DoesNotExist:
            return Response({'code': 2001, 'message': '活动不存在'}, status=status.HTTP_404_NOT_FOUND)
        comment = request.data.get('comment', '')
        activity.audit_status = 2
        activity.audit_comment = comment
        activity.save(update_fields=['audit_status', 'audit_comment'])
        return Response({'code': 0, 'message': '审核拒绝'})

    @action(detail=True, methods=['get'])
    def attendees(self, request, pk=None):
        try:
            activity = Activity.objects.get(uuid=pk)
        except Activity.DoesNotExist:
            return Response({'code': 2001, 'message': '活动不存在'}, status=status.HTTP_404_NOT_FOUND)

        enrollments = ActivityEnrollment.objects.filter(
            activity=activity, enrollment_status__in=[1, 2]
        ).select_related('profile__user').order_by('-ai_recommended', '-ai_match_score')

        page = self.paginate_queryset(enrollments)
        if page is not None:
            return self.get_paginated_response(ActivityEnrollmentSerializer(page, many=True).data)
        return Response({'code': 0, 'data': []})
