# backend/apps/users/management/commands/import_calisanlar.py

import pandas as pd
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Excel dosyasından çalışan verilerini içe aktarır.'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='İçe aktarılacak Excel dosyasının yolu')

    def handle(self, *args, **options):
        # 'AppRegistryNotReady' hatasını önlemek için import'u fonksiyon içine taşıyoruz.
        from apps.users.models import CustomUser

        file_path = options['file_path']
        
        try:
            df = pd.read_excel(file_path)
            df = df.where(pd.notnull(df), None) # Boş hücreleri None yap
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Hata: '{file_path}' dosyası bulunamadı. Lütfen dosyanın 'backend' klasöründe olduğundan emin olun."))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Excel dosyası okunurken bir hata oluştu: {e}"))
            return

        self.stdout.write(f"'{file_path}' dosyasından veriler okunuyor...")

        for index, row in df.iterrows():
            username = row.get('username')
            if not username:
                self.stdout.write(self.style.WARNING(f"{index + 2}. satırda 'username' boş olduğu için atlandı."))
                continue

            user, created = CustomUser.objects.update_or_create(
                username=username,
                defaults={
                    'first_name': row.get('first_name'),
                    'last_name': row.get('last_name'),
                    'email': row.get('email'),
                    'telefon': str(row.get('telefon', '')),
                    'adres': row.get('adres'),
                    'enlem': row.get('enlem'),
                    'boylam': row.get('boylam'),
                    'cinsiyet': row.get('cinsiyet'),
                    'rol': 'calisan',
                    'is_staff': False,
                    'is_superuser': False,
                }
            )
            
            if created:
                user.set_password('VardiyaSifre123')
                user.save()
                self.stdout.write(self.style.SUCCESS(f"-> '{user.username}' oluşturuldu ve varsayılan şifre atandı."))
            else:
                self.stdout.write(self.style.NOTICE(f"-> '{user.username}' güncellendi."))
                
        self.stdout.write(self.style.SUCCESS('İçe aktarma tamamlandı.'))