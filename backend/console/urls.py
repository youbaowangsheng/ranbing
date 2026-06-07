from django.urls import path
from rest_framework.routers import SimpleRouter
from .views import (
    DashboardStatsView, DailyStatsView, UsageReportView, AgentsRankView,
    BusinessAgentViewSet, MatchingRecordViewSet, PublishTaskViewSet
)

router = SimpleRouter()
router.register(r'business/agents', BusinessAgentViewSet, basename='business-agents')
router.register(r'matching/records', MatchingRecordViewSet, basename='matching-records')
router.register(r'publish/tasks', PublishTaskViewSet, basename='publish-tasks')

urlpatterns = [
    path('stats/dashboard/', DashboardStatsView.as_view(), name='stats-dashboard'),
    path('stats/daily/', DailyStatsView.as_view(), name='stats-daily'),
    path('stats/usage/', UsageReportView.as_view(), name='stats-usage'),
    path('stats/agents_rank/', AgentsRankView.as_view(), name='stats-agents-rank'),
] + router.urls
