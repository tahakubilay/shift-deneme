# apps/schedules/management/commands/import_musaitlik.py

import pandas as pd
from django.core.management.base import BaseCommand
from apps.users.models import CustomUser
from apps.schedules.models import Musaitlik
# Choices dosyasını import ediyoruz
from apps.schedules.choices import MusaitlikDurum

class Command(BaseCommand):
    help = 'Excel dosyasından belirli bir dönem için çalışanların haftalık müsaitlik şablonunu içe aktarır.'

    def add_arguments(self, parser):
        parser.add_argument('donem', type=str, help='Müsaitliğin geçerli olacağı dönem (YYYY-AA formatında)')
        parser.add_argument('file_path', type=str, help='İçe aktarılacak Excel dosyasının yolu')

    def handle(self, *args, **options):
        donem = options['donem']
        file_path = options['file_path']

        try:
            df = pd.read_excel(file_path)
            df = df.where(pd.notnull(df), None)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Hata: '{file_path}' dosyası bulunamadı."))
            return

        self.stdout.write(f"'{donem}' dönemi için '{file_path}' dosyasından müsaitlik verileri okunuyor...")

        gun_map = {
            'pazartesi': 1, 'sali': 2, 'carsamba': 3, 'persembe': 4,
            'cuma': 5, 'cumartesi': 6, 'pazar': 7
        }
        
        # Geçerli durumları artık MusaitlikDurum'dan alıyoruz
        gecerli_durumlar = MusaitlikDurum.values

        for index, row in df.iterrows():
            username = row.get('username')
            if not username:
                continue

            try:
                calisan = CustomUser.objects.get(username=username)
            except CustomUser.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"'{username}' adında bir kullanıcı bulunamadı, bu satır atlanıyor."))
                continue

            Musaitlik.objects.filter(calisan=calisan, donem=donem).delete()

            for gun_str, gun_numarasi in gun_map.items():
                durum = row.get(gun_str)
                if durum and durum in gecerli_durumlar:
                    Musaitlik.objects.create(
                        calisan=calisan,
                        gun=gun_numarasi,
                        musaitlik_durumu=durum,
                        donem=donem
                    )
                else:
                     Musaitlik.objects.create(
                        calisan=calisan,
                        gun=gun_numarasi,
                        musaitlik_durumu=MusaitlikDurum.MUSAIT_DEGIL,
                        donem=donem
                    )
            
            self.stdout.write(self.style.SUCCESS(f"-> '{calisan.username}' için haftalık müsaitlik şablonu oluşturuldu."))

        self.stdout.write(self.style.SUCCESS('Müsaitlik içe aktarma tamamlandı.'))