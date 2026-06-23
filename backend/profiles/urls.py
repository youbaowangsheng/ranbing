from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import ProfileViewSet, TagViewSet, ContactTagViewSet

router = SimpleRouter()
router.register(r'profiles', ProfileViewSet, basename='profiles')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'contact-tags', ContactTagViewSet, basename='contact-tags')

urlpatterns = [
    path('', include(router.urls)),
]
