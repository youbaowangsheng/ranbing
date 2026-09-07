"""Activities视图"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import Activity, ActivityEnrollment
from .serializers import ActivitySerializer, ActivityEnrollmentSerializer
from profiles.models import Profile


class ActivityViewSet(viewsets.GenericViewSet):
    # 列表/详情公开；报名/审核等需要登录
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

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

    @action(detail=True, methods=['post'])
    def unenroll(self, request, pk=None):
        """取消报名"""
        try:
            activity = Activity.objects.get(uuid=pk)
        except Activity.DoesNotExist:
            return Response({'code': 2001, 'message': '活动不存在'}, status=status.HTTP_404_NOT_FOUND)

        profile, _ = Profile.objects.get_or_create(user=request.user)
        try:
            enrollment = ActivityEnrollment.objects.get(activity=activity, profile=profile)
        except ActivityEnrollment.DoesNotExist:
            return Response({'code': 2004, 'message': '您尚未报名该活动'}, status=status.HTTP_400_BAD_REQUEST)

        if enrollment.enrollment_status == 3:
            return Response({'code': 2004, 'message': '您已取消报名'}, status=status.HTTP_400_BAD_REQUEST)

        enrollment.enrollment_status = 3  # 已取消
        enrollment.save(update_fields=['enrollment_status'])

        activity.current_attendees = max(0, activity.current_attendees - 1)
        activity.save(update_fields=['current_attendees'])
        return Response({'code': 0, 'message': '已取消报名'})

    @action(detail=True, methods=['get'], url_path='enrollment_status')
    def enrollment_status(self, request, pk=None):
        """当前用户是否已报名该活动"""
        try:
            activity = Activity.objects.get(uuid=pk)
        except Activity.DoesNotExist:
            return Response({'code': 2001, 'message': '活动不存在'}, status=status.HTTP_404_NOT_FOUND)

        if not request.user.is_authenticated:
            return Response({'code': 0, 'data': {'enrolled': False}})

        profile, _ = Profile.objects.get_or_create(user=request.user)
        enrollment = ActivityEnrollment.objects.filter(
            activity=activity, profile=profile, enrollment_status__in=[1, 2]
        ).first()
        return Response({'code': 0, 'data': {'enrolled': bool(enrollment)}})

    @action(detail=False, methods=['get'], url_path='mine')
    def mine(self, request):
        """我报名的活动列表"""
        profile, _ = Profile.objects.get_or_create(user=request.user)
        enrollments = ActivityEnrollment.objects.filter(
            profile=profile, enrollment_status__in=[1, 2]
        ).select_related('activity__organizer__user').order_by('-created_at')

        activities = [e.activity for e in enrollments if e.activity.status in [1, 2]]
        page = self.paginate_queryset(activities)
        if page is not None:
            return self.get_paginated_response(ActivitySerializer(page, many=True).data)
        return Response({'code': 0, 'data': ActivitySerializer(activities, many=True).data})

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
