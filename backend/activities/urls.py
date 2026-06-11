from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import ActivityViewSet

router = SimpleRouter()
router.register(r'activities', ActivityViewSet, basename='activities')

urlpatterns = [
    path('', include(router.urls)),
]
