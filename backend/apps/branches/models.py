# backend/apps/branches/models.py

from django.db import models
# DİKKAT: Artık 'Musaitlik' modelini değil, 'choices' dosyasından 'Gunler'i import ediyoruz
from apps.schedules.choices import Gunler 

class Sube(models.Model):
    sube_adi = models.CharField(max_length=100, verbose_name="Şube Adı")
    adres = models.TextField(verbose_name="Adres")
    enlem = models.DecimalField(max_digits=10, decimal_places=8, blank=True, null=True, verbose_name="Enlem")
    boylam = models.DecimalField(max_digits=11, decimal_places=8, blank=True, null=True, verbose_name="Boylam")

    def __str__(self):
        return self.sube_adi

class SubeCalismaSaati(models.Model):
    sube = models.ForeignKey(Sube, on_delete=models.CASCADE, related_name='calisma_saatleri')
    # DİKKAT: Artık 'Musaitlik.Gunler.choices' yerine doğrudan 'Gunler.choices' kullanıyoruz
    gun = models.IntegerField(choices=Gunler.choices, verbose_name="Haftanın Günü") 
    acilis_saati = models.TimeField(blank=True, null=True)
    kapanis_saati = models.TimeField(blank=True, null=True)
    kapali = models.BooleanField(default=False, verbose_name="O gün kapalı mı?")

    class Meta:
        unique_together = ('sube', 'gun')

    def __str__(self):
        if self.kapali:
            return f"{self.sube.sube_adi} - {self.get_gun_display()} - Kapalı"
        return f"{self.sube.sube_adi} - {self.get_gun_display()} ({self.acilis_saati}-{self.kapanis_saati})"