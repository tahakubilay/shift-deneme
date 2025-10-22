# apps/branches/views.py

# 1. 'ListAPIView' yerine 'ListCreateAPIView' import ediyoruz.
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView 
from rest_framework.permissions import IsAuthenticated
from .models import Sube
from .serializers import SubeSerializer


# 2. Sınıfımızın adını ve miras aldığı sınıfı güncelliyoruz.
class SubeListCreateAPIView(ListCreateAPIView): 
    queryset = Sube.objects.all()
    serializer_class = SubeSerializer
    permission_classes = [IsAuthenticated]  # Sadece doğrulanmış kullanıcılar erişebilir

class SubeDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Sube.objects.all()
    serializer_class = SubeSerializer
    permission_classes = [IsAuthenticated]  # Sadece doğrulanmış kullanıcılar erişebilir