from django.db import models

# Choices sınıflarımızı yeni choices.py dosyasından import ediyoruz
from .choices import Gunler, MusaitlikDurum, VardiyaDurum, IstekTipi, IstekDurum, KuralSart

class Vardiya(models.Model):
    # Artık Choices sınıfı dışarıdan geliyor: VardiyaDurum
    durum = models.CharField(max_length=20, choices=VardiyaDurum.choices, default=VardiyaDurum.TASLAK)
    
    # Metin tabanlı (string) referansları koruyoruz
    sube = models.ForeignKey('branches.Sube', on_delete=models.CASCADE, verbose_name="Şube")
    calisan = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Çalışan")
    baslangic_zamani = models.DateTimeField(verbose_name="Başlangıç Zamanı")
    bitis_zamani = models.DateTimeField(verbose_name="Bitiş Zamanı")

    def __str__(self):
        calisan_adi = (self.calisan.get_full_name() or self.calisan.username) if self.calisan else "Atanmamış"
        return f"{self.sube.sube_adi} - {calisan_adi} - {self.baslangic_zamani.strftime('%d %b %Y %H:%M')}"


class Musaitlik(models.Model):
    calisan = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='musaitlikleri')
    gun = models.IntegerField(choices=Gunler.choices, verbose_name="Haftanın Günü")
    musaitlik_durumu = models.CharField(max_length=20, choices=MusaitlikDurum.choices, default=MusaitlikDurum.MUSAIT_DEGIL)
    donem = models.CharField(max_length=7, verbose_name="Dönem (YYYY-AA)")

    class Meta:
        unique_together = ('calisan', 'gun', 'donem')

    def __str__(self):
        return f"{self.calisan.get_full_name()} - {self.get_gun_display()} - {self.get_musaitlik_durumu_display()}"


class CalisanTercihi(models.Model):
    calisan = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='tercihleri')
    sube = models.ForeignKey('branches.Sube', on_delete=models.CASCADE)
    gun = models.IntegerField(choices=Gunler.choices)
    
    def __str__(self):
        return f"{self.calisan.get_full_name()} - {self.sube.sube_adi} tercihi"


class AylikSaatDengesi(models.Model):
    calisan = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='saat_dengeleri')
    donem = models.CharField(max_length=7, verbose_name="Dönem (YYYY-AA)")
    denge = models.FloatField(default=0, verbose_name="Saat Dengesi (+/-)")

    class Meta:
        unique_together = ('calisan', 'donem')

    def __str__(self):
        return f"{self.calisan.get_full_name()} - {self.donem} - Denge: {self.denge}"
        

class KisitlamaKurali(models.Model):
    sube = models.ForeignKey('branches.Sube', on_delete=models.CASCADE, related_name='kisitlama_kurallari')
    sart = models.CharField(max_length=50, choices=KuralSart.choices, verbose_name="Kısıtlama Şartı")
    baslangic_saati = models.TimeField(verbose_name="Kısıtlamanın Başladığı Saat (bu saatten sonra)")

    def __str__(self):
        return f"{self.sube.sube_adi} - {self.get_sart_display()} {self.baslangic_saati}'den sonra çalışamaz"


class VardiyaIstegi(models.Model):
    istek_tipi = models.CharField(max_length=10, choices=IstekTipi.choices)
    istek_yapan_vardiya = models.ForeignKey(Vardiya, on_delete=models.CASCADE, related_name='teklif_edilen_istekler')
    hedef_vardiya = models.ForeignKey(Vardiya, on_delete=models.CASCADE, related_name='alinmak_istenen_istekler', null=True, blank=True)
    istek_yapan = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='gonderdigi_istekler')
    hedef_calisan = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='aldigi_istekler', null=True, blank=True)
    yedek_calisan = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='yedek_atandigi_istekler')
    durum = models.CharField(max_length=30, choices=IstekDurum.choices, default=IstekDurum.HEDEF_ONAYI_BEKLIYOR)
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True)
    guncellenme_tarihi = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.istek_tipi == IstekTipi.IPTAL:
            return f"{self.istek_yapan.username} vardiya iptal isteği. Durum: {self.get_durum_display()}"
        return f"{self.istek_yapan.username}, {self.hedef_calisan.username}'in vardiyasını istiyor. Durum: {self.get_durum_display()}"