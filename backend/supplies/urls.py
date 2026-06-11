from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import SupplyViewSet, FriendRequestViewSet, ConnectionViewSet, CardViewSet

router = SimpleRouter()
router.register(r'supplies', SupplyViewSet, basename='supplies')
router.register(r'friend-requests', FriendRequestViewSet, basename='friend-requests')
router.register(r'connections', ConnectionViewSet, basename='connections')
router.register(r'cards', CardViewSet, basename='cards')

urlpatterns = [
    path('', include(router.urls)),
]
