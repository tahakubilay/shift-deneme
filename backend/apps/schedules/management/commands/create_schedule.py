# backend/apps/schedules/management/commands/create_schedule.py

from django.core.management.base import BaseCommand
from datetime import datetime, date, time, timedelta
import calendar
import math

# Modelleri import edelim
from apps.users.models import CustomUser
from apps.branches.models import Sube, SubeCalismaSaati
from apps.schedules.models import Musaitlik, AylikSaatDengesi, Vardiya, CalisanTercihi, KisitlamaKurali
from apps.schedules.choices import Gunler # Choices dosyasından Gunler'i alalım (Eğer kullanıyorsanız, models.py'den alınmalı)

VARDİYA_MIN_SAAT = 3
VARDİYA_MAX_SAAT = 9
AYLIK_SAAT_LIMITI = 120

class Command(BaseCommand):
    help = 'Nihai v14: Gerçekten çalışan, vardiya bölen, mesai ve kısıtlama yöneten plan.'

    def add_arguments(self, parser):
        parser.add_argument('donem', type=str, help='Planın oluşturulacağı dönem (YYYY-AA formatında)')

    def handle(self, *args, **options):
        donem = options['donem']
        self.stdout.write(self.style.SUCCESS(f'>>> {donem} dönemi için Nihai Planlama Motoru v14 başlatılıyor...'))

        # --- Veri Toplama ---
        self.aktif_calisanlar = list(CustomUser.objects.filter(is_active=True, rol='calisan'))
        self.kisitlama_kurallari = list(KisitlamaKurali.objects.all())
        # --- EKSİK OLAN SATIR BURADA ---
        self.calisan_tercihleri = list(CalisanTercihi.objects.select_related('calisan', 'sube'))
        # -------------------------------
        self.musaitlik_sablonlari = self.get_musaitlik_dict(donem)
        try:
            prev_month_dt = datetime.strptime(donem, "%Y-%m") - timedelta(days=1)
            prev_month_str = prev_month_dt.strftime("%Y-%m")
            self.onceki_ay_dengeleri = {d.calisan.id: d.denge for d in AylikSaatDengesi.objects.filter(donem=prev_month_str)}
        except ValueError: self.onceki_ay_dengeleri = {}
            
        self.atanan_saatler = {calisan.id: 0 for calisan in self.aktif_calisanlar}
        self.atanan_mesai_saatler = {calisan.id: 0 for calisan in self.aktif_calisanlar}
        self.atanmis_vardiyalar = {calisan.id: [] for calisan in self.aktif_calisanlar}
        calisma_saatleri = self.get_calisma_saatleri_dict()

        # --- Plan Temizleme ---
        yil, ay = map(int, donem.split('-'))
        Vardiya.objects.filter(durum='taslak', baslangic_zamani__year=yil, baslangic_zamani__month=ay).delete()
        
        # --- Doldurulacak vardiya bloklarını belirle ---
        aydaki_gunler = [d for d in calendar.Calendar().itermonthdates(yil, ay) if d.month == ay]
        doldurulacak_vardiyalar = []
        for sube in Sube.objects.all():
            for gun_tarihi in aydaki_gunler:
                haftanin_gunu = gun_tarihi.isoweekday()
                sube_saatleri = calisma_saatleri.get(sube.id, {}).get(haftanin_gunu)
                if sube_saatleri and not sube_saatleri.get('kapalı'):
                    baslangic = datetime.combine(gun_tarihi, sube_saatleri['acilis'])
                    bitis = datetime.combine(gun_tarihi, sube_saatleri['kapanis'])
                    if bitis <= baslangic: bitis += timedelta(days=1)
                    doldurulacak_vardiyalar.append({"sube": sube, "baslangic": baslangic, "bitis": bitis, "dolu_araliklar": []})
        
        # --- AŞAMA 1: FAVORİLERİ ATA ---
        self.stdout.write(self.style.HTTP_INFO('\nAŞAMA 1: Favori atamaları yapılıyor...'))
        self.assign_favorites(doldurulacak_vardiyalar)

        # --- AŞAMA 2: KALAN BOŞLUKLARI DOLDUR ---
        self.stdout.write(self.style.HTTP_INFO('\nAŞAMA 2: Kalan boşluklar dolduruluyor...'))
        self.fill_remaining_shifts(doldurulacak_vardiyalar)

        self.stdout.write(self.style.SUCCESS('>>> Planlama tamamlandı!'))

    # --- ATAMA FONKSİYONLARI ---

    def assign_favorites(self, tum_vardiya_bloklari):
        for tercih in self.calisan_tercihleri:
            calisan = tercih.calisan
            for blok in tum_vardiya_bloklari:
                if any(start < blok['bitis'] and end > blok['baslangic'] for start, end in blok.get('dolu_araliklar', [])): continue
                if tercih.sube_id == blok['sube'].id and tercih.gun == blok['baslangic'].isoweekday():
                    if self.is_candidate_valid_at_start(calisan, blok['sube'], blok['baslangic']):
                        self.stdout.write(f"  -> Favori Denemesi: {calisan.username} -> {blok['sube'].sube_adi} [{blok['baslangic'].strftime('%d/%m')}]")
                        self.solve_and_assign_gap(calisan, blok, blok['baslangic'], blok['bitis'])

    def fill_remaining_shifts(self, tum_vardiya_bloklari):
        tum_bosluklar = []
        for blok in tum_vardiya_bloklari:
            bosluklar = self.find_gaps_in_block(blok)
            for bosluk_bas, bosluk_bitis in bosluklar:
                tum_bosluklar.append({'sube': blok['sube'], 'baslangic': bosluk_bas, 'bitis': bosluk_bitis, 'blok_ref': blok})
        tum_bosluklar.sort(key=lambda x: x['baslangic'])

        for bosluk in tum_bosluklar:
            blok = bosluk['blok_ref']
            if any(start <= bosluk['baslangic'] and end >= bosluk['bitis'] for start, end in blok.get('dolu_araliklar', [])): continue

            self.stdout.write(self.style.HTTP_INFO(f"\nÇözülüyor: {bosluk['sube'].sube_adi} - {bosluk['baslangic'].strftime('%d/%m %H:%M')} -> {bosluk['bitis'].strftime('%H:%M')}"))
            
            aday_havuzu = self.find_candidates(bosluk['sube'], bosluk['baslangic'])
            if not aday_havuzu:
                self.stdout.write(self.style.WARNING(" -> Bu boşluk için uygun aday bulunamadı."))
                continue
            
            sirali_adaylar = self.rank_candidates(aday_havuzu, bosluk['sube'], bosluk['baslangic'])
            
            vardiya_atandi_mi = False
            for aday_data in sirali_adaylar:
                en_iyi_aday = aday_data['aday']
                if self.solve_and_assign_gap(en_iyi_aday, blok, bosluk['baslangic'], bosluk['bitis']):
                    vardiya_atandi_mi = True
                    break
            
            if not vardiya_atandi_mi:
                self.stdout.write(self.style.WARNING(f" -> {bosluk['baslangic'].strftime('%H:%M')} boşluğu için çakışmasız aday bulunamadı."))

    def find_gaps_in_block(self, blok):
        gaps = []; current_time = blok['baslangic']
        dolu_araliklar = sorted(blok.get('dolu_araliklar', []))
        for dolu_bas, dolu_bitis in dolu_araliklar:
            if current_time < dolu_bas:
                 if (dolu_bas - current_time).total_seconds() / 3600 >= VARDİYA_MIN_SAAT:
                    gaps.append((current_time, dolu_bas))
            current_time = max(current_time, dolu_bitis)
        if current_time < blok['bitis']:
            if (blok['bitis'] - current_time).total_seconds() / 3600 >= VARDİYA_MIN_SAAT:
                gaps.append((current_time, blok['bitis']))
        return gaps

    def solve_and_assign_gap(self, calisan, blok, bosluk_baslangic, bosluk_bitis):
        kalan_sure = (bosluk_bitis - bosluk_baslangic).total_seconds() / 3600
        atanacak_sure = min(VARDİYA_MAX_SAAT, kalan_sure)

        kural_bitis_saati = self.check_restriction_end_time(calisan, blok['sube'])
        potansiyel_bitis_zamani = bosluk_baslangic + timedelta(hours=atanacak_sure)

        if kural_bitis_saati:
            kural_bitis_datetime = datetime.combine(bosluk_baslangic.date(), kural_bitis_saati)
            if kural_bitis_datetime < bosluk_baslangic : kural_bitis_datetime += timedelta(days=1)
            
            if kural_bitis_datetime <= bosluk_baslangic: return False

            if potansiyel_bitis_zamani > kural_bitis_datetime:
                yeni_atanacak_sure = max(0, (kural_bitis_datetime - bosluk_baslangic).total_seconds() / 3600)
                if yeni_atanacak_sure < VARDİYA_MIN_SAAT: return False
                atanacak_sure = yeni_atanacak_sure
                self.stdout.write(self.style.NOTICE(f"   -> Kısıtlama: {calisan.username} vardiyası {kural_bitis_saati}'de bitecek."))

        yeni_bosluk_suresi = kalan_sure - atanacak_sure
        if 0 < yeni_bosluk_suresi < VARDİYA_MIN_SAAT:
             if kalan_sure <= VARDİYA_MAX_SAAT + VARDİYA_MIN_SAAT:
                atanacak_sure = kalan_sure
                self.stdout.write(self.style.NOTICE(f"   -> Zorunlu Mesai: {calisan.get_full_name()} {yeni_bosluk_suresi:.1f} saat mesai."))

        vardiya_bitis_zamani = bosluk_baslangic + timedelta(hours=atanacak_sure)
        
        if not self.has_conflicting_shift(calisan, bosluk_baslangic, vardiya_bitis_zamani):
            self.create_shift(calisan, blok['sube'], bosluk_baslangic, vardiya_bitis_zamani)
            blok.setdefault('dolu_araliklar', []).append((bosluk_baslangic, vardiya_bitis_zamani))
            return True
        else:
            self.stdout.write(self.style.WARNING(f"   -> Atama Denemesi Başarısız: {calisan.username} için {bosluk_baslangic.strftime('%H:%M')} ataması çakışıyor."))
            return False

    # --- KONTROL FONKSİYONLARI ---

    def is_candidate_valid_at_start(self, calisan, sube, baslangic_zamani):
        """Bir adayın vardiya başlangıcı için uygun olup olmadığını kontrol eder (Sadece favoriler için)."""
        if not self.is_available(calisan, baslangic_zamani): return False
        if self.atanan_saatler[calisan.id] >= AYLIK_SAAT_LIMITI: return False
        if self.violates_restriction_at_start(calisan, sube, baslangic_zamani): return False
        return True

    def find_candidates(self, sube, baslangic_zamani):
        """Sadece temel uygunlukları kontrol eder."""
        adaylar = []
        for calisan in self.aktif_calisanlar:
            if not self.is_available(calisan, baslangic_zamani): continue
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
        gun_tarihi = baslangic_zamani.date() # Günü alalım

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
        if vardiya_suresi < VARDİYA_MIN_SAAT - 0.1:
            self.stdout.write(self.style.ERROR(f"   -> HATA: Oluşturulan vardiya süresi ({vardiya_suresi:.1f}) minimumdan az! Atama yapılmadı."))
            return

        self.atanmis_vardiyalar[calisan.id].append((baslangic, bitis))
        Vardiya.objects.create(sube=sube, calisan=calisan, baslangic_zamani=baslangic, bitis_zamani=bitis, durum='taslak')
        
        mesai_suresi = max(0, vardiya_suresi - VARDİYA_MAX_SAAT)
        self.atanan_saatler[calisan.id] += vardiya_suresi
        self.atanan_mesai_saatler[calisan.id] += mesai_suresi
        self.stdout.write(f"   -> Atama: {calisan.get_full_name() or calisan.username} -> {sube.sube_adi} [{baslangic.strftime('%H:%M')}-{bitis.strftime('%H:%M')}] ({vardiya_suresi:.1f} saat){' (MESAI)' if mesai_suresi > 0 else ''}")


    # --- DİĞER YARDIMCI FONKSİYONLAR ---
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