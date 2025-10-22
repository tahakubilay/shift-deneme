# backend/apps/schedules/management/commands/create_schedule.py

from django.core.management.base import BaseCommand
from datetime import datetime, date, time, timedelta
import calendar
import math

from apps.users.models import CustomUser
from apps.branches.models import Sube, SubeCalismaSaati
from apps.schedules.models import Musaitlik, AylikSaatDengesi, Vardiya, CalisanTercihi, KisitlamaKurali

VARDİYA_MIN_SAAT = 3
VARDİYA_MAX_SAAT = 9
AYLIK_SAAT_LIMITI = 120 # Gerekirse esnetilebilir

class Command(BaseCommand):
    help = 'Nihai v13: Özyinelemeli, doğru kurallı motor.'

    def add_arguments(self, parser):
        parser.add_argument('donem', type=str, help='Planın oluşturulacağı dönem (YYYY-AA formatında)')

    def handle(self, *args, **options):
        donem = options['donem']
        self.stdout.write(self.style.SUCCESS(f'>>> {donem} dönemi için Nihai Planlama Motoru v13 başlatılıyor...'))

        # --- Veri Toplama ---
        self.aktif_calisanlar = list(CustomUser.objects.filter(is_active=True, rol='calisan'))
        self.kisitlama_kurallari = list(KisitlamaKurali.objects.all())
        self.calisan_tercihleri = list(CalisanTercihi.objects.select_related('calisan', 'sube'))
        self.musaitlik_sablonlari = self.get_musaitlik_dict(donem)
        try:
            prev_month_dt = datetime.strptime(donem, "%Y-%m") - timedelta(days=1)
            prev_month_str = prev_month_dt.strftime("%Y-%m")
            self.onceki_ay_dengeleri = {d.calisan.id: d.denge for d in AylikSaatDengesi.objects.filter(donem=prev_month_str)}
        except ValueError: self.onceki_ay_dengeleri = {}
            
        self.atanan_saatler = {calisan.id: 0 for calisan in self.aktif_calisanlar}
        self.atanan_mesai_saatler = {calisan.id: 0 for calisan in self.aktif_calisanlar}
        # Çakışma kontrolü için {calisan_id: [(baslangic, bitis)]}
        self.atanmis_vardiyalar = {calisan.id: [] for calisan in self.aktif_calisanlar}
        calisma_saatleri = self.get_calisma_saatleri_dict()

        # --- Plan Temizleme ---
        yil, ay = map(int, donem.split('-'))
        Vardiya.objects.filter(durum='taslak', baslangic_zamani__year=yil, baslangic_zamani__month=ay).delete()
        
        # --- Gün Bazlı Çözücüyü Çalıştırma ---
        aydaki_gunler = [d for d in calendar.Calendar().itermonthdates(yil, ay) if d.month == ay]
        for sube in Sube.objects.all():
            for gun_tarihi in aydaki_gunler:
                haftanin_gunu = gun_tarihi.isoweekday()
                sube_saatleri = calisma_saatleri.get(sube.id, {}).get(haftanin_gunu)
                
                if not sube_saatleri or sube_saatleri.get('kapalı'): continue

                self.stdout.write(self.style.HTTP_INFO(f"\nÇözülüyor: {sube.sube_adi} - {gun_tarihi.strftime('%d/%m/%Y')} ({sube_saatleri['acilis']} - {sube_saatleri['kapanis']})"))
                
                gun_baslangic = datetime.combine(gun_tarihi, sube_saatleri['acilis'])
                gun_bitis = datetime.combine(gun_tarihi, sube_saatleri['kapanis'])
                if gun_bitis <= gun_baslangic: gun_bitis += timedelta(days=1)

                self.solve_day_for_branch(sube, gun_baslangic, gun_bitis)

        self.stdout.write(self.style.SUCCESS('>>> Planlama tamamlandı!'))

    # --- ÖZYİNELEMELİ ÇÖZÜCÜ ---
    def solve_day_for_branch(self, sube, blok_baslangic, blok_bitis):
        kalan_sure = (blok_bitis - blok_baslangic).total_seconds() / 3600
        if kalan_sure < VARDİYA_MIN_SAAT:
            if kalan_sure > 0.1: self.stdout.write(self.style.WARNING(f" -> Doldurulamayan {kalan_sure:.1f} saatlik boşluk kaldı."))
            return

        aday_havuzu = self.find_candidates(sube, blok_baslangic)
        if not aday_havuzu:
            self.stdout.write(self.style.WARNING(f" -> {blok_baslangic.strftime('%H:%M')} başlangıcı için aday bulunamadı."))
            return
        
        sirali_adaylar = self.rank_candidates(aday_havuzu, sube, blok_baslangic)
        
        vardiya_atandi = False
        for aday_data in sirali_adaylar:
            aday = aday_data['aday']
            
            atanacak_sure = min(VARDİYA_MAX_SAAT, kalan_sure)
            
            # --- KISITLAMA İLE SÜRE AYARI (HEM BAŞLANGIÇ HEM BİTİŞ KONTROLÜ) ---
            kural_bitis_saati = self.check_restriction_end_time(aday, sube)
            potansiyel_bitis_zamani = blok_baslangic + timedelta(hours=atanacak_sure)

            if kural_bitis_saati:
                kural_bitis_datetime = datetime.combine(blok_baslangic.date(), kural_bitis_saati)
                if kural_bitis_datetime < blok_baslangic: kural_bitis_datetime += timedelta(days=1)

                # Eğer vardiyanın BİTİŞİ kuralı aşıyorsa, süreyi kısalt
                if potansiyel_bitis_zamani > kural_bitis_datetime:
                    self.stdout.write(self.style.WARNING(f"   -> Kısıtlama Nedeniyle Süre Kısaltıldı: {aday.username} {kural_bitis_saati}'de bitirecek."))
                    yeni_atanacak_sure = max(0, (kural_bitis_datetime - blok_baslangic).total_seconds() / 3600)
                    
                    if yeni_atanacak_sure < VARDİYA_MIN_SAAT:
                       self.stdout.write(self.style.WARNING(f"   -> {aday.username} için kısıtlama sonrası süre ({yeni_atanacak_sure:.1f} saat) minimumdan az. Bu aday atlanıyor."))
                       continue # Bu aday bu boşluğa uygun değil, sonraki adayı dene
                    
                    atanacak_sure = yeni_atanacak_sure # Süreyi kurala göre ayarla
            #----------------------------------------------------

            yeni_bosluk_suresi = kalan_sure - atanacak_sure
            if 0 < yeni_bosluk_suresi < VARDİYA_MIN_SAAT:
                 if kalan_sure <= VARDİYA_MAX_SAAT + VARDİYA_MIN_SAAT:
                    atanacak_sure = kalan_sure
                    self.stdout.write(self.style.NOTICE(f"   -> Zorunlu Mesai: {aday.get_full_name()} {yeni_bosluk_suresi:.1f} saat mesai yapacak."))
                 # else: # Eğer kalan süre büyükse (örn 13 saat), zaten atanacak_sure = 9 idi, dokunma

            vardiya_bitis_zamani = blok_baslangic + timedelta(hours=atanacak_sure)

            # Son Çakışma Kontrolü
            if not self.has_conflicting_shift(aday, blok_baslangic, vardiya_bitis_zamani):
                self.create_shift(aday, sube, blok_baslangic, vardiya_bitis_zamani)
                vardiya_atandi = True
                
                # ÖZYİNELEME: Kalan boşluk için tekrar çöz
                kalan_blok_baslangic = vardiya_bitis_zamani
                if (blok_bitis - kalan_blok_baslangic).total_seconds() / 3600 >= VARDİYA_MIN_SAAT:
                    self.solve_day_for_branch(sube, kalan_blok_baslangic, blok_bitis)
                break # Bu blok parçası için atama yapıldı, sonraki boşluğa geç (özyineleme halledecek)
        
        if not vardiya_atandi:
            self.stdout.write(self.style.WARNING(f" -> {blok_baslangic.strftime('%H:%M')} için çakışmasız uygun aday bulunamadı."))

    # --- FİLTRELEME FONKSİYONLARI ---
    def find_candidates(self, sube, baslangic_zamani):
        """Sadece temel uygunlukları kontrol eder."""
        adaylar = []
        for calisan in self.aktif_calisanlar:
            if not self.is_available(calisan, baslangic_zamani): continue
            # GÜN İÇİNDE BAŞKA VARDİYASI OLUP OLMADIĞINA BAKMIYORUZ!
            if self.atanan_saatler[calisan.id] >= AYLIK_SAAT_LIMITI: continue
            if self.violates_restriction_at_start(calisan, sube, baslangic_zamani): continue
            adaylar.append(calisan)
        return adaylar

    def violates_restriction_at_start(self, calisan, sube, baslangic_zamani):
        """Bir adayın vardiya BAŞLANGICINDA kural ihlal edip etmediğini kontrol eder."""
        for kural in self.kisitlama_kurallari:
            if kural.sube_id == sube.id:
                if baslangic_zamani.time() >= kural.baslangic_saati:
                    if kural.sart == 'cinsiyet_kadin' and calisan.cinsiyet == 'kadin':
                        return True
        return False

    def check_restriction_end_time(self, calisan, sube):
        """Bir çalışanın o şubede uyması gereken en erken bitiş saatini döndürür (varsa)."""
        earliest_end_time = None
        for kural in self.kisitlama_kurallari:
            if kural.sube_id == sube.id:
                 if (kural.sart == 'cinsiyet_kadin' and calisan.cinsiyet == 'kadin'):
                     return kural.baslangic_saati
        return None

    def has_conflicting_shift(self, calisan, yeni_baslangic, yeni_bitis):
        """Çakışma kontrolü."""
        yeni_baslangic_check = yeni_baslangic + timedelta(microseconds=1)
        yeni_bitis_check = yeni_bitis - timedelta(microseconds=1)
        for mevcut_baslangic, mevcut_bitis in self.atanmis_vardiyalar.get(calisan.id, []):
            if yeni_baslangic_check < mevcut_bitis and mevcut_baslangic < yeni_bitis_check:
                return True
        return False

    # --- SIRALAMA VE ATAMA ---
    def rank_candidates(self, aday_havuzu, sube, baslangic_zamani):
        """Adayları sıralar (Favori önceliği dahil)."""
        adaylar_ve_puanlar = []
        haftanin_gunu = baslangic_zamani.isoweekday()
        
        for aday in aday_havuzu:
            puan = 0
            is_favorite = False
            for tercih in self.calisan_tercihleri:
                if tercih.calisan_id == aday.id and tercih.sube_id == sube.id and tercih.gun == haftanin_gunu:
                    puan += 1000 # Favorilere devasa bonus
                    is_favorite = True
                    break
            
            puan += abs(min(0, self.onceki_ay_dengeleri.get(aday.id, 0))) * 10
            if aday.enlem and sube.enlem:
                puan += max(0, 50 - self.calculate_distance(aday.enlem, aday.boylam, sube.enlem, sube.boylam))
            puan -= self.atanan_mesai_saatler[aday.id] * 5
            
            adaylar_ve_puanlar.append({'aday': aday, 'puan': puan, 'is_favorite': is_favorite})
        
        return sorted(adaylar_ve_puanlar, key=lambda x: (x['is_favorite'], x['puan']), reverse=True)

    def create_shift(self, calisan, sube, baslangic, bitis):
        vardiya_suresi = (bitis - baslangic).total_seconds() / 3600
        if vardiya_suresi < VARDİYA_MIN_SAAT - 0.1: # Min sürenin altındaysa kaydetme
            self.stdout.write(self.style.ERROR(f"   -> HATA: Oluşturulan vardiya süresi ({vardiya_suresi:.1f}) minimumdan az! Atama yapılmadı."))
            return

        self.atanmis_vardiyalar[calisan.id].append((baslangic, bitis))
        Vardiya.objects.create(sube=sube, calisan=calisan, baslangic_zamani=baslangic, bitis_zamani=bitis, durum='taslak')
        
        mesai_suresi = max(0, vardiya_suresi - VARDİYA_MAX_SAAT)
        self.atanan_saatler[calisan.id] += vardiya_suresi
        self.atanan_mesai_saatler[calisan.id] += mesai_suresi
        self.stdout.write(f"   -> Atama: {calisan.get_full_name() or calisan.username} -> {sube.sube_adi} [{baslangic.strftime('%H:%M')}-{bitis.strftime('%H:%M')}] ({vardiya_suresi:.1f} saat){' (MESAI)' if mesai_suresi > 0 else ''}")

    # --- DİĞER YARDIMCI FONKSİYONLAR (DEĞİŞİKLİK YOK) ---
    def is_available(self, calisan, baslangic_zamani):
        haftanin_gunu = baslangic_zamani.isoweekday()
        calisan_musaitlik = self.musaitlik_sablonlari.get(calisan.id, {})
        gun_durumu = calisan_musaitlik.get(haftanin_gunu, 'müsait değil')
        if gun_durumu == 'müsait değil': return False

        vardiya_baslangic_saati = baslangic_zamani.hour
        # Doğru değişken adını kullanalım: baslangic_zamani
        if (gun_durumu == '11 sonrası' and vardiya_baslangic_saati < 11 and baslangic_zamani.date() == baslangic_zamani.date()): return False
        if (gun_durumu == '14 sonrası' and vardiya_baslangic_saati < 14 and baslangic_zamani.date() == baslangic_zamani.date()): return False
        if (gun_durumu == '17 sonrası' and vardiya_baslangic_saati < 17 and baslangic_zamani.date() == baslangic_zamani.date()): return False

        return True

    def get_musaitlik_dict(self, donem):
        musaitlik_sablonlari = {}
        for m in Musaitlik.objects.filter(donem=donem):
            if m.calisan.id not in musaitlik_sablonlari: musaitlik_sablonlari[m.calisan.id] = {}
            musaitlik_sablonlari[m.calisan.id][m.gun] = m.musaitlik_durumu
        return musaitlik_sablonlari

    def get_calisma_saatleri_dict(self):
        saatler = {}
        for scs in SubeCalismaSaati.objects.all():
            if scs.sube.id not in saatler: saatler[scs.sube.id] = {}
            saatler[scs.sube.id][scs.gun] = {
                'acilis': scs.acilis_saati if scs.acilis_saati else time(0, 0), 
                'kapanis': scs.kapanis_saati if scs.kapanis_saati else time(0, 0), 
                'kapali': scs.kapali
            }
        return saatler
        
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        if not all([lat1, lon1, lat2, lon2]): return 9999
        R = 6371; lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
        dlon = lon2 - lon1; dlat = lat2 - lat1
        a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c