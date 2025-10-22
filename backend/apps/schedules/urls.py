from django.urls import path
# Yeni view'ımızı import edelim
from .views import MusaitlikView, VardiyaListAPIView, VardiyaIstekView, VardiyaIstegiYanitlaView

urlpatterns = [
    path('musaitlik/', MusaitlikView.as_view(), name='musaitlik'),
    path('vardiyalar/', VardiyaListAPIView.as_view(), name='vardiya-list'), # <-- BU SATIRI EKLEYİN
   # Hem listeleme hem oluşturma için tek adres
    path('istekler/', VardiyaIstekView.as_view(), name='istek-list-create'),
    
    # İsteğe yanıt verme adresi (ID ile)
    path('istekler/<int:pk>/yanitla/', VardiyaIstegiYanitlaView.as_view(), name='istek-yanitla'),
]