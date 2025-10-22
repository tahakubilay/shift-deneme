# backend/apps/branches/admin.py

from django.contrib import admin
from .models import Sube, SubeCalismaSaati

class SubeCalismaSaatiInline(admin.TabularInline):
    model = SubeCalismaSaati
    extra = 7 

class SubeAdmin(admin.ModelAdmin):
    inlines = [SubeCalismaSaatiInline]
    list_display = ('sube_adi', 'adres')

# Sube modelini, yukarıda tasarladığımız özel SubeAdmin görünümüyle kaydediyoruz.
# Gereksiz olan 'unregister' satırını sildik.
admin.site.register(Sube, SubeAdmin)

# SubeCalismaSaati modelini de admin panelinde ayrı bir menüde görmek
# isterseniz bu satır kalabilir. İstemezseniz silebilirsiniz.
admin.site.register(SubeCalismaSaati)