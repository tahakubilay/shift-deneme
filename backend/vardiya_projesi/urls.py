# backend/vardiya_projesi/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/subeler/', include('apps.branches.urls')),
    path('api/kullanicilar/', include('apps.users.urls')),
    # --- BU SATIRIN DOĞRU OLDUĞUNDAN EMİN OLUN ---
    path('api/schedules/', include('apps.schedules.urls')),
    # ----------------------------------------------
]