# apps/branches/urls.py
from django.urls import path
from .views import SubeListCreateAPIView, SubeDetailAPIView

urlpatterns = [
    path('', SubeListCreateAPIView.as_view(), name='sube-list-create'),
    path('<int:pk>/', SubeDetailAPIView.as_view(), name='sube-detail'),
]