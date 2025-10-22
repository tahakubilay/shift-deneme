# backend/apps/users/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        CALISAN = 'calisan', 'Çalışan'

    # --- EKSİK OLAN KISIM BURASI ---
    class Gender(models.TextChoices):
        KADIN = 'kadin', 'Kadın'
        ERKEK = 'erkek', 'Erkek'
    # --------------------------------

    # Standart User modelindeki email alanını zorunlu ve benzersiz yapalım
    email = models.EmailField(unique=True)
    
    # Eklediğimiz yeni alanlar
    rol = models.CharField(max_length=10, choices=Role.choices, default=Role.CALISAN, verbose_name="Kullanıcı Rolü")
    telefon = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefon Numarası")
    adres = models.TextField(blank=True, null=True, verbose_name="Adres")
    enlem = models.DecimalField(max_digits=10, decimal_places=8, blank=True, null=True, verbose_name="Enlem")
    boylam = models.DecimalField(max_digits=11, decimal_places=8, blank=True, null=True, verbose_name="Boylam")
    
    # --- EKSİK OLAN ALAN BURASI ---
    cinsiyet = models.CharField(max_length=10, choices=Gender.choices, blank=True, null=True, verbose_name="Cinsiyet")
    # -----------------------------
    
    # Django'nun admin panelinde güzel görünmesi için
    def __str__(self):
        full_name = self.get_full_name()
        return full_name if full_name else self.username