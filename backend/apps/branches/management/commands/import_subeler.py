# apps/branches/management/commands/import_subeler.py

import pandas as pd
from django.core.management.base import BaseCommand
from apps.branches.models import Sube, SubeCalismaSaati

class Command(BaseCommand):
    help = 'Excel dosyasından şube ve günlük çalışma saatlerini içe aktarır.'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='İçe aktarılacak Excel dosyasının yolu')

    def handle(self, *args, **options):
        # Import'u fonksiyonun içine taşıyoruz
        from apps.branches.models import Sube, SubeCalismaSaati

        file_path = options['file_path']
        
        try:
            # --- DÜZELTİLMİŞ KISIM ---
            # 1. Adım: Önce dosyayı oku
            df = pd.read_excel(file_path)
            # 2. Adım: Sonra boş hücreleri (NaN) None ile değiştir
            df = df.where(pd.notnull(df), None)
            # --------------------------
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Hata: '{file_path}' dosyası bulunamadı."))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Excel dosyası okunurken bir hata oluştu: {e}"))
            return

        gun_map = {
            'pzt': 1, 'sali': 2, 'cars': 3, 'pers': 4,
            'cuma': 5, 'cmt': 6, 'pzr': 7
        }

        for index, row in df.iterrows():
            if pd.isna(row['sube_adi']):
                continue

            sube, created = Sube.objects.update_or_create(
                sube_adi=row['sube_adi'],
                defaults={'adres': row['adres'], 'enlem': row.get('enlem'), 'boylam': row.get('boylam')}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"'{sube.sube_adi}' oluşturuldu."))
            else:
                self.stdout.write(self.style.WARNING(f"'{sube.sube_adi}' güncellendi."))

            for prefix, gun_numarasi in gun_map.items():
                acilis_col = f'{prefix}_acilis'
                kapanis_col = f'{prefix}_kapanis'

                acilis = row.get(acilis_col)
                kapanis = row.get(kapanis_col)

                if acilis is None or kapanis is None:
                    SubeCalismaSaati.objects.update_or_create(
                        sube=sube, gun=gun_numarasi,
                        defaults={'kapali': True, 'acilis_saati': None, 'kapanis_saati': None}
                    )
                else:
                    SubeCalismaSaati.objects.update_or_create(
                        sube=sube, gun=gun_numarasi,
                        defaults={'kapali': False, 'acilis_saati': acilis, 'kapanis_saati': kapanis}
                    )
            self.stdout.write(f" -> '{sube.sube_adi}' için 7 günlük çalışma saatleri ayarlandı.")

        self.stdout.write(self.style.SUCCESS('İçe aktarma tamamlandı.'))