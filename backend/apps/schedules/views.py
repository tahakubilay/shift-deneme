# backend/apps/schedules/views.py

from django.db.models import Q
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from .models import Musaitlik, Vardiya, VardiyaIstegi
from .serializers import MusaitlikSerializer, VardiyaSerializer, VardiyaIstegiCreateSerializer, VardiyaIstegiListSerializer, VardiyaIptalCreateSerializer, AdminIptalActionSerializer
from .choices import IstekTipi, IstekDurum
from django.core.management import call_command
from django.http import JsonResponse
from datetime import datetime, timedelta

class MusaitlikView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        current_donem = "2025-10" # Bu dönemi dinamik hale getirmek sonraki adım olabilir
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

class VardiyaListAPIView(generics.ListAPIView):
    queryset = Vardiya.objects.filter(durum='taslak').order_by('baslangic_zamani')
    serializer_class = VardiyaSerializer
    permission_classes = [permissions.IsAuthenticated]

class BenimVardiyalarimListView(generics.ListAPIView):
    """
    Sadece giriş yapmış olan kullanıcının,
    gelecekteki 'taslak' veya 'planlandi' durumundaki vardiyalarını listeler.
    """
    serializer_class = VardiyaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Vardiya.objects.filter(
            calisan=self.request.user,
            durum__in=['taslak', 'planlandi'], 
            baslangic_zamani__gte=datetime.now()
        ).order_by('baslangic_zamani')

class VardiyaIstekView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Giriş yapmış kullanıcıya gelen ve onun gönderdiği istekleri listeler."""
        user = request.user
        istekler = VardiyaIstegi.objects.filter(Q(istek_yapan=user) | Q(hedef_calisan=user)).order_by('-olusturulma_tarihi')
        
        serializer = VardiyaIstegiListSerializer(istekler, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        """Yeni bir takas isteği oluşturur ve ÇAKIŞMA KONTROLÜ yapar."""
        serializer = VardiyaIstegiCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            istek_yapan_vardiya = serializer.validated_data['istek_yapan_vardiya']
            hedef_vardiya = serializer.validated_data['hedef_vardiya']
            istek_yapan = serializer.validated_data['istek_yapan']
            
            if (request.user != istek_yapan) or (istek_yapan_vardiya.calisan != request.user):
                return Response({'hata': 'Sadece kendi adınıza ve kendi vardiyalarınız için takas isteği gönderebilirsiniz.'}, status=status.HTTP_403_FORBIDDEN)

            # --- ÇAKIŞMA KONTROLÜ ---
            diger_vardiyalar = Vardiya.objects.filter(
                calisan=request.user,
                durum__in=['taslak', 'planlandi']
            ).exclude(id=istek_yapan_vardiya.id) # Kendi teklif ettiğini hariç tut

            hedef_baslangic = hedef_vardiya.baslangic_zamani
            hedef_bitis = hedef_vardiya.bitis_zamani

            for vardiya in diger_vardiyalar:
                if (vardiya.baslangic_zamani < hedef_bitis and 
                    hedef_baslangic < vardiya.bitis_zamani):
                    
                    return Response({
                        'hata': f'Bu takas, {vardiya.baslangic_zamani.strftime("%d/%m %H:%M")} vardiyanız ile çakışıyor. Teklif gönderilemez.'
                    }, status=status.HTTP_400_BAD_REQUEST)
            # --- ÇAKIŞMA KONTROLÜ BİTTİ ---

            serializer.save(
                istek_tipi=IstekTipi.TAKAS,
                durum=IstekDurum.HEDEF_ONAYI_BEKLIYOR
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VardiyaIstegiYanitlaView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        try:
            istek = VardiyaIstegi.objects.get(pk=pk)
        except VardiyaIstegi.DoesNotExist:
            return Response({'hata': 'İstek bulunamadı.'}, status=status.HTTP_404_NOT_FOUND)

        if istek.hedef_calisan != request.user:
            return Response({'hata': 'Bu isteğe yanıt verme yetkiniz yok.'}, status=status.HTTP_403_FORBIDDEN)

        yanit = request.data.get('yanit')
        
        if yanit == 'onayla':
            istek.durum = IstekDurum.ADMIN_ONAYI_BEKLIYOR
            istek.save()
            return Response({'mesaj': 'İstek onaylandı ve admin onayına gönderildi.'})
        elif yanit == 'reddet':
            istek.durum = IstekDurum.REDDEDILDI
            istek.save()
            return Response({'mesaj': 'İstek reddedildi.'})
        else:
            return Response({'hata': 'Geçersiz yanıt. Yanıt "onayla" veya "reddet" olmalıdır.'}, status=status.HTTP_400_BAD_REQUEST)

class AdminIstekListView(generics.ListAPIView):
    serializer_class = VardiyaIstegiListSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return VardiyaIstegi.objects.filter(
            durum=IstekDurum.ADMIN_ONAYI_BEKLIYOR
        ).order_by('olusturulma_tarihi')

class AdminIstekActionView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk, *args, **kwargs):
        try:
            istek = VardiyaIstegi.objects.get(pk=pk, durum=IstekDurum.ADMIN_ONAYI_BEKLIYOR)
        except VardiyaIstegi.DoesNotExist:
            return Response({'hata': 'İstek bulunamadı veya zaten işlenmiş.'}, status=status.HTTP_404_NOT_FOUND)

        action = request.data.get('action')

        if istek.istek_tipi == IstekTipi.IPTAL:
            if action == 'onayla':
                yedek_calisan_id = request.data.get('yedek_calisan_id')
                vardiya = istek.istek_yapan_vardiya

                try:
                    with transaction.atomic():
                        if yedek_calisan_id:
                            from apps.users.models import CustomUser
                            yedek_calisan = CustomUser.objects.get(id=yedek_calisan_id)
                            vardiya.calisan = yedek_calisan
                            vardiya.save()
                            istek.yedek_calisan = yedek_calisan
                        else:
                            vardiya.durum = 'iptal'
                            vardiya.save()

                        istek.durum = IstekDurum.ONAYLANDI
                        istek.save()
                except Exception as e:
                    return Response({'hata': f'İptal işlemi sırasında hata: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                return Response({'mesaj': 'İptal isteği onaylandı.'})

            elif action == 'reddet':
                istek.durum = IstekDurum.REDDEDILDI
                istek.save()
                return Response({'mesaj': 'İptal isteği reddedildi.'})

        elif istek.istek_tipi == IstekTipi.TAKAS:
            if action == 'onayla':
                vardiya1 = istek.istek_yapan_vardiya
                vardiya2 = istek.hedef_vardiya

                calisan1 = vardiya1.calisan
                calisan2 = vardiya2.calisan

                try:
                    with transaction.atomic():
                        vardiya1.calisan = calisan2
                        vardiya2.calisan = calisan1
                        vardiya1.save()
                        vardiya2.save()

                        istek.durum = IstekDurum.ONAYLANDI
                        istek.save()
                except Exception as e:
                    return Response({'hata': f'Takas sırasında bir veritabanı hatası oluştu: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                return Response({'mesaj': 'Takas başarıyla onaylandı ve vardiyalar değiştirildi.'})

            elif action == 'reddet':
                istek.durum = IstekDurum.REDDEDILDI
                istek.save()
                return Response({'mesaj': 'İstek reddedildi.'})

        return Response({'hata': 'Geçersiz eylem.'}, status=status.HTTP_400_BAD_REQUEST)

class PlanOlusturView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, *args, **kwargs):
        donem = request.data.get('donem')
        if not donem or len(donem.split('-')) != 2:
            return Response({'hata': 'Lütfen geçerli bir dönem belirtin (YYYY-AA).'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            call_command('create_schedule', donem)
            return Response({'mesaj': f'{donem} dönemi için plan başarıyla oluşturuldu.'})
        except Exception as e:
            return Response({'hata': f'Plan oluşturulurken bir hata oluştu: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class VardiyaIptalView(generics.CreateAPIView):
    queryset = VardiyaIstegi.objects.all()
    serializer_class = VardiyaIptalCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        vardiya_id = request.data.get('istek_yapan_vardiya')
        try:
            vardiya = Vardiya.objects.get(id=vardiya_id)
        except Vardiya.DoesNotExist:
            return Response({'hata': 'Böyle bir vardiya bulunamadı.'}, status=status.HTTP_404_NOT_FOUND)

        # Güvenlik Kontrolü: Kullanıcı, başkasının vardiyasını mı iptal etmeye çalışıyor?
        if vardiya.calisan != request.user:
            return Response({'hata': 'Sadece kendi vardiyalarınızı iptal edebilirsiniz.'}, status=status.HTTP_403_FORBIDDEN)

        # Zaten bu vardiya için bekleyen bir istek var mı?
        mevcut_istek = VardiyaIstegi.objects.filter(istek_yapan_vardiya=vardiya, durum__in=[IstekDurum.HEDEF_ONAYI_BEKLIYOR, IstekDurum.ADMIN_ONAYI_BEKLIYOR]).first()
        if mevcut_istek:
             return Response({'hata': 'Bu vardiya için zaten beklemede olan bir takas veya iptal isteğiniz mevcut.'}, status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        # İsteği yapanı, tipi ve durumu otomatik ayarla
        serializer.save(
            istek_yapan=self.request.user,
            istek_tipi=IstekTipi.IPTAL,
            durum=IstekDurum.ADMIN_ONAYI_BEKLIYOR # İptal istekleri doğrudan admine gider
        )