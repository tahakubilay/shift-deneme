# backend/apps/schedules/urls.py

from django.urls import path
from .views import (
    MusaitlikView, VardiyaListAPIView,
    VardiyaIstekView, VardiyaIstegiYanitlaView,
    PlanOlusturView, AdminIstekListView, AdminIstekActionView,
    PlanOlusturView, BenimVardiyalarimListView, AdminIstekActionView, VardiyaIptalView
)

urlpatterns = [
    # Bu yollar '/api/schedules/' adresine eklenir
    path('musaitlik/', MusaitlikView.as_view(), name='musaitlik'),
    path('vardiyalar/', VardiyaListAPIView.as_view(), name='vardiya-list'),
    path('istekler/', VardiyaIstekView.as_view(), name='istek-list-create'),
    path('istekler/<int:pk>/yanitla/', VardiyaIstegiYanitlaView.as_view(), name='istek-yanitla'),
    path('plan-olustur/', PlanOlusturView.as_view(), name='plan-olustur'),
    path('admin/istekler/', AdminIstekListView.as_view(), name='admin-istek-list'),
    path('admin/istekler/<int:pk>/aksiyon/', AdminIstekActionView.as_view(), name='admin-istek-aksiyon'),
    path('vardiyalarim/', BenimVardiyalarimListView.as_view(), name='benim-vardiyalarim'),
    path('admin/istekler/<int:pk>/aksiyon/', AdminIstekActionView.as_view(), name='admin-istek-aksiyon'),
    path('istekler/iptal/', VardiyaIptalView.as_view(), name='istek-iptal-olustur'),
]