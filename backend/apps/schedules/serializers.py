# apps/schedules/serializers.py
from rest_framework import serializers
from .models import Musaitlik, Vardiya, VardiyaIstegi

class MusaitlikSerializer(serializers.ModelSerializer):
    class Meta:
        model = Musaitlik
        fields = ['gun', 'musaitlik_durumu']
    
class VardiyaSerializer(serializers.ModelSerializer):
    # 'calisan' ve 'sube' alanlarının ID yerine isimlerini göstermek için
    calisan = serializers.StringRelatedField()
    sube = serializers.StringRelatedField()

    class Meta:
        model = Vardiya
        # Göstermek istediğimiz tüm alanları belirtiyoruz
        fields = ['id', 'sube', 'calisan', 'baslangic_zamani', 'bitis_zamani', 'durum']

class VardiyaIstegiCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VardiyaIstegi
        # Kullanıcının sadece bu iki alanı göndermesine izin veriyoruz
        fields = ['vardiya', 'hedef_calisan']

class VardiyaIstegiListSerializer(serializers.ModelSerializer):
    # İsimleri göstermeye devam edelim
    istek_yapan_adi = serializers.StringRelatedField(source='istek_yapan')
    hedef_calisan_adi = serializers.StringRelatedField(source='hedef_calisan')
    vardiya = VardiyaSerializer(read_only=True)
    
    class Meta:
        model = VardiyaIstegi
        # ID'leri de ekliyoruz
        fields = '__all__'