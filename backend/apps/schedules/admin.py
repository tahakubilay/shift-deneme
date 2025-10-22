# backend/apps/schedules/admin.py

from django.contrib import admin
from .models import Vardiya, Musaitlik, CalisanTercihi, AylikSaatDengesi, KisitlamaKurali, VardiyaIstegi

class VardiyaAdmin(admin.ModelAdmin):
    # Liste sayfasında hangi sütunların görüneceğini belirtir
    list_display = ('sube', 'calisan', 'baslangic_zamani', 'bitis_zamani', 'durum')

    # Sağ tarafta bir filtreleme çubuğu ekler
    list_filter = ('sube', 'calisan', 'durum', 'baslangic_zamani')

    # Üstte bir arama çubuğu ekler
    search_fields = ('calisan__username', 'calisan__first_name', 'sube__sube_adi')

    # Tarihe göre hiyerarşik gezinme ekler
    date_hierarchy = 'baslangic_zamani'

# Vardiya modelini, yukarıda tasarladığımız özel VardiyaAdmin görünümüyle kaydediyoruz.
# Gereksiz olan 'unregister' satırını sildik.
admin.site.register(Vardiya, VardiyaAdmin)

# Diğer modelleri de kaydediyoruz
admin.site.register(Musaitlik)
admin.site.register(CalisanTercihi)
admin.site.register(AylikSaatDengesi)
admin.site.register(KisitlamaKurali)
admin.site.register(VardiyaIstegi)