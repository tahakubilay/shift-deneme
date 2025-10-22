# backend/apps/users/apps.py dosyasındaki doğru kod

from django.apps import AppConfig

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users' # <-- Bakın, bu doğru yapılandırma burada duruyor.