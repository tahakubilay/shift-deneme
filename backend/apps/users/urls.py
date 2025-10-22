# apps/users/urls.py
from django.urls import path
from .views import UserListAPIView

urlpatterns = [
    path('', UserListAPIView.as_view(), name='user-list'),
]