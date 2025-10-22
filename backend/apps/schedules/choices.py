# backend/apps/schedules/choices.py

from django.db import models

class Gunler(models.IntegerChoices):
    PAZARTESI = 1, 'Pazartesi'
    SALI = 2, 'Salı'
    CARSAMBA = 3, 'Çarşamba'
    PERSEMBE = 4, 'Perşembe'
    CUMA = 5, 'Cuma'
    CUMARTESI = 6, 'Cumartesi'
    PAZAR = 7, 'Pazar'

class MusaitlikDurum(models.TextChoices):
    MUSAIT_DEGIL = 'müsait değil', 'Müsait Değil'
    TUM_GUN = 'tüm gün', 'Tüm Gün'
    SAAT_11_SONRASI = '11 sonrası', '11:00 Sonrası'
    SAAT_14_SONRASI = '14 sonrası', '14:00 Sonrası'
    SAAT_17_SONRASI = '17 sonrası', '17:00 Sonrası'

class VardiyaDurum(models.TextChoices):
    PLANLANDI = 'planlandi', 'Planlandı'
    TAMAMLANDI = 'tamamlandi', 'Tamamlandı'
    IPTAL = 'iptal', 'İptal Edildi'
    TASLAK = 'taslak', 'Taslak'

class IstekTipi(models.TextChoices):
    TAKAS = 'takas', 'Takas'
    IPTAL = 'iptal', 'İptal'

class IstekDurum(models.TextChoices):
    HEDEF_ONAYI_BEKLIYOR = 'hedef_onayi_bekliyor', 'Hedef Onayı Bekliyor'
    ADMIN_ONAYI_BEKLIYOR = 'admin_onayi_bekliyor', 'Admin Onayı Bekliyor'
    ONAYLANDI = 'onaylandi', 'Onaylandı'
    REDDEDILDI = 'reddedildi', 'Reddedildi'

class KuralSart(models.TextChoices):
    CINSIYET_KADIN = 'cinsiyet_kadin', 'Cinsiyet: Kadın'
    CINSIYET_ERKEK = 'cinsiyet_erkek', 'Cinsiyet: Erkek'