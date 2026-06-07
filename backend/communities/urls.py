from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import CommunityViewSet

router = SimpleRouter()
router.register(r'communities', CommunityViewSet, basename='communities')

urlpatterns = [
    path('', include(router.urls)),
]
