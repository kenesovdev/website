from django.contrib import admin
from django.urls import include, path

from apps.core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', core_views.health),
    path('api/v1/', include('apps.users.urls')),
    path('api/v1/', include('apps.problems.urls.admin_urls')),
    path('api/v1/', include('apps.problems.urls.public_urls')),
    path('api/v1/', include('apps.submissions.urls')),
    path('api/v1/', include('apps.contests.urls')),
]
