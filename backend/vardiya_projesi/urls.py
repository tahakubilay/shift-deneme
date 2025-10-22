# vardiya_projesi/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('dj_rest_auth.urls')),

    # Her uygulama için kendi benzersiz yolunu tanımlıyoruz
    path('api/subeler/', include('apps.branches.urls')),
    path('api/kullanicilar/', include('apps.users.urls')),
    path('api/schedules/', include('apps.schedules.urls')),
]