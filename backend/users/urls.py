from django.urls import path, include
from rest_framework.routers import SimpleRouter
from . import captcha
from .views import AuthViewSet, UserMeView
from .user_views import UserViewSet

router = SimpleRouter()
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('me/', UserMeView.as_view(), name='user-me'),
    path('captcha/', captcha.captcha_image, name='captcha_image'),
]
