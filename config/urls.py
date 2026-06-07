from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.users.views import UserViewSet
from apps.accounts.views import AccountViewSet
from apps.agents.views import BusinessAgentViewSet
from apps.stats.views import StatsViewSet
from apps.community.views import CommunityPostViewSet
from apps.matching.views import MatchingRecordViewSet
from apps.publish.views import PublishTaskViewSet
from apps.admin_views import (
    activities_pending, activities_approve, activities_reject,
    communities_pending, communities_approve, communities_reject,
    supplies_pending, supplies_approve, supplies_reject,
    messages_pending, messages_audit
)
from apps.auth_views import login, logout, userinfo, register

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'accounts', AccountViewSet, basename='account')
router.register(r'business/agents', BusinessAgentViewSet, basename='business-agent')
router.register(r'stats', StatsViewSet, basename='stats')
router.register(r'community/posts', CommunityPostViewSet, basename='community-post')
router.register(r'matching/records', MatchingRecordViewSet, basename='matching-record')
router.register(r'publish/tasks', PublishTaskViewSet, basename='publish-task')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    # Auth API
    path('api/auth/login/', login),
    path('api/auth/logout/', logout),
    path('api/auth/userinfo/', userinfo),
    path('api/auth/register/', register),
    # Admin 审核 API (调用 backend)
    path('api/admin/activities/pending/', activities_pending),
    path('api/admin/activities/<uuid>/approve/', activities_approve),
    path('api/admin/activities/<uuid>/reject/', activities_reject),
    path('api/admin/communities/pending/', communities_pending),
    path('api/admin/communities/<uuid>/approve/', communities_approve),
    path('api/admin/communities/<uuid>/reject/', communities_reject),
    path('api/admin/supplies/pending/', supplies_pending),
    path('api/admin/supplies/<uuid>/approve/', supplies_approve),
    path('api/admin/supplies/<uuid>/reject/', supplies_reject),
    path('api/admin/messages/pending/', messages_pending),
    path('api/admin/communities/<community_uuid>/messages/<int:msg_id>/audit/', messages_audit),
]