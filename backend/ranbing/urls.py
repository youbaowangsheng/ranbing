"""燃冰 URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import StatsView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('users.urls')),
    path('api/v1/', include('profiles.urls')),
    path('api/v1/', include('supplies.urls')),
    path('api/v1/', include('activities.urls')),
    path('api/v1/', include('communities.urls')),
    path('api/v1/ai/', include('ai.urls')),
    path('api/v1/stats/content/', StatsView.as_view(), name='stats-content'),
    path('api/v1/', include('console.urls')),
    path('', include('pages.urls')),  # root → pages
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
