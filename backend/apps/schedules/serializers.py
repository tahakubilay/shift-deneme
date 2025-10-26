# apps/schedules/serializers.py
from rest_framework import serializers
from .models import Musaitlik, Vardiya, VardiyaIstegi

class MusaitlikSerializer(serializers.ModelSerializer):
    class Meta:
        model = Musaitlik
        fields = ['gun', 'musaitlik_durumu']
    
# apps/schedules/serializers.py

# apps/schedules/serializers.py

# ... (other imports and serializers) ...

class VardiyaSerializer(serializers.ModelSerializer):
    # These are the fields you defined directly
    calisan_adi = serializers.StringRelatedField(source='calisan')
    sube_adi = serializers.StringRelatedField(source='sube')

    class Meta:
        model = Vardiya
        # --- MAKE SURE THIS LIST INCLUDES YOUR DEFINED FIELDS ---
        fields = ['id', 'sube', 'sube_adi', 'calisan', 'calisan_adi', 'baslangic_zamani', 'bitis_zamani', 'durum']
        # --------------------------------------------------------

class VardiyaIstegiCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VardiyaIstegi
        # Modelimizdeki yeni alan adlarını kullanıyoruz
        fields = ['istek_yapan_vardiya', 'hedef_vardiya', 'istek_yapan', 'hedef_calisan']

class VardiyaIstegiListSerializer(serializers.ModelSerializer):
    # İsimleri göstermek için
    istek_yapan_adi = serializers.StringRelatedField(source='istek_yapan', read_only=True)
    hedef_calisan_adi = serializers.StringRelatedField(source='hedef_calisan', read_only=True)
    
    # --- DÜZELTME BURADA ---
    # Artık iki vardiyanın da detaylarını gönderiyoruz
    istek_yapan_vardiya_detay = VardiyaSerializer(read_only=True, source='istek_yapan_vardiya')
    hedef_vardiya_detay = VardiyaSerializer(read_only=True, source='hedef_vardiya')
    
    class Meta:
        model = VardiyaIstegi
        # Alan listesini de güncelliyoruz (artık 'vardiya' yok)
        fields = [
            'id',
            'istek_tipi',
            'durum',
            'olusturulma_tarihi',
            
            # ID Alanları (Filtreleme için)
            'istek_yapan',
            'hedef_calisan',
            'istek_yapan_vardiya', # ID
            'hedef_vardiya',     # ID

            # İsim Alanları (Gösterim için)
            'istek_yapan_adi',
            'hedef_calisan_adi',

            # Detay Alanları (Frontend'de bilgileri göstermek için)
            'istek_yapan_vardiya_detay',
            'hedef_vardiya_detay'
        ]

class VardiyaIptalCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VardiyaIstegi
        fields = ['istek_yapan_vardiya']

class AdminIptalActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['onayla', 'reddet'])
    yedek_calisan_id = serializers.IntegerField(required=False, allow_null=True)