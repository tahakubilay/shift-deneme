# apps/schedules/views.py
from django.db.models import Q 
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated # <-- EKSİK OLAN IMPORT BU
from rest_framework.generics import ListAPIView # ListAPIView'ı import edelim
from rest_framework import generics, permissions, status # generics, permissions, status'u import edelim
from .models import Musaitlik, Vardiya, VardiyaIstegi # VardiyaIstegi'ni ekle
from .serializers import MusaitlikSerializer, VardiyaSerializer, VardiyaIstegiCreateSerializer, VardiyaIstegiListSerializer
class MusaitlikView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Örnek olarak şimdiki ayı alalım (örn: "2025-10")
        current_donem = "2025-10" 
        musaitlikler = Musaitlik.objects.filter(calisan=request.user, donem=current_donem)
        serializer = MusaitlikSerializer(musaitlikler, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        yeni_sablon = request.data.get('sablon', [])
        current_donem = "2025-10"
        
        Musaitlik.objects.filter(calisan=request.user, donem=current_donem).delete()
        
        for item in yeni_sablon:
            Musaitlik.objects.create(
                calisan=request.user,
                gun=item['gun'],
                musaitlik_durumu=item['musaitlik_durumu'],
                donem=current_donem
            )
        
        return Response({'message': 'Müsaitlik durumu başarıyla güncellendi.'}, status=status.HTTP_201_CREATED)
    
class VardiyaListAPIView(ListAPIView):
    queryset = Vardiya.objects.filter(durum='taslak').order_by('baslangic_zamani')
    serializer_class = VardiyaSerializer
    permission_classes = [IsAuthenticated]

class VardiyaIstekView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Giriş yapmış kullanıcıya gelen ve onun gönderdiği istekleri listeler."""
        user = request.user
        # Kullanıcının ya istek yapan ya da hedef çalışan olduğu tüm istekleri bul
        istekler = VardiyaIstegi.objects.filter(Q(istek_yapan=user) | Q(hedef_calisan=user)).order_by('-olusturulma_tarihi')
        
        serializer = VardiyaIstegiListSerializer(istekler, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        """Yeni bir takas isteği oluşturur."""
        serializer = VardiyaIstegiCreateSerializer(data=request.data)
        if serializer.is_valid():
            vardiya = serializer.validated_data['vardiya']
            if vardiya.calisan != request.user:
                return Response({'hata': 'Sadece kendi vardiyalarınız için takas isteği gönderebilirsiniz.'}, status=status.HTTP_403_FORBIDDEN)
            
            serializer.save(
                istek_yapan=request.user,
                istek_tipi=VardiyaIstegi.IstekTipi.TAKAS,
                durum=VardiyaIstegi.Durum.HEDEF_ONAYI_BEKLIYOR
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# --- 4. EN ALTA BU YENİ SINIFI EKLEYİN ---
class VardiyaIstegiYanitlaView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        """Bir takas isteğine yanıt verir (Onayla/Reddet)."""
        try:
            istek = VardiyaIstegi.objects.get(pk=pk)
        except VardiyaIstegi.DoesNotExist:
            return Response({'hata': 'İstek bulunamadı.'}, status=status.HTTP_404_NOT_FOUND)

        # Güvenlik Kontrolü: İsteğe sadece hedef çalışan yanıt verebilir.
        if istek.hedef_calisan != request.user:
            return Response({'hata': 'Bu isteğe yanıt verme yetkiniz yok.'}, status=status.HTTP_403_FORBIDDEN)

        yanit = request.data.get('yanit')
        if yanit == 'onayla':
            istek.durum = VardiyaIstegi.Durum.ADMIN_ONAYI_BEKLIYOR
            istek.save()
            return Response({'mesaj': 'İstek onaylandı ve admin onayına gönderildi.'})
        elif yanit == 'reddet':
            istek.durum = VardiyaIstegi.Durum.REDDEDILDI
            istek.save()
            return Response({'mesaj': 'İstek reddedildi.'})
        else:
            return Response({'hata': 'Geçersiz yanıt. Yanıt "onayla" veya "reddet" olmalıdır.'}, status=status.HTTP_400_BAD_REQUEST)