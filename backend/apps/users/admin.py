# apps/users/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    # Kullanıcı listesinde görünecek alanları belirliyoruz
    list_display = ['username', 'email', 'first_name', 'last_name', 'rol', 'is_staff']
    
    # Kullanıcı düzenleme formuna kendi eklediğimiz alanları dahil ediyoruz
    # Orijinal fieldsets'in üzerine bizimkileri ekliyoruz
    fieldsets = UserAdmin.fieldsets + (
        ('Ek Bilgiler', {'fields': ('rol', 'telefon', 'adres')}),
    )

# CustomUser modelini, yukarıda tasarladığımız CustomUserAdmin görünümüyle kaydediyoruz
admin.site.register(CustomUser, CustomUserAdmin)