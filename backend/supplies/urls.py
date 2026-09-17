from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import SupplyViewSet, FriendRequestViewSet, ConnectionViewSet, CardViewSet
from .upload_views import ImageUploadView

router = SimpleRouter()
router.register(r'supplies', SupplyViewSet, basename='supplies')
router.register(r'friend-requests', FriendRequestViewSet, basename='friend-requests')
router.register(r'connections', ConnectionViewSet, basename='connections')
router.register(r'cards', CardViewSet, basename='cards')

urlpatterns = [
    path('upload/image/', ImageUploadView.as_view(), name='upload-image'),
    path('', include(router.urls)),
]
