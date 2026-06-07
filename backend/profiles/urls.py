from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import ProfileViewSet, TagViewSet

router = SimpleRouter()
router.register(r'profiles', ProfileViewSet, basename='profiles')
router.register(r'tags', TagViewSet, basename='tags')

urlpatterns = [
    path('', include(router.urls)),
]
