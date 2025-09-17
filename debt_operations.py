import sqlite3
import json
from datetime import date
from database_operations import baglanti_olustur

def borclu_ekle_db(isim):
    """
    'borclular' tablosuna yeni bir kişi ekler.
    İsimler benzersiz (UNIQUE) olmalıdır.
    """
    # Girilen ismin başındaki ve sonundaki boşlukları temizle
    temiz_isim = isim.strip()
    if not temiz_isim:
        print("Hata: Borçlu ismi boş olamaz.")
        return False, "İsim boş olamaz."

    conn = baglanti_olustur()
    if conn is None:
        return False, "Veritabanı bağlantı hatası."

    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO borclular (isim) VALUES (?)", (temiz_isim,))
        conn.commit()
        # Başarılı ekleme durumunda True ve yeni eklenen kişinin ID'sini döndür
        return True, cursor.lastrowid
    except sqlite3.IntegrityError:
        # Bu hata, aynı isimde bir kişi zaten var olduğunda oluşur (UNIQUE kısıtlaması sayesinde).
        print(f"Hata: '{temiz_isim}' adında bir borçlu zaten mevcut.")
        return False, "Bu isimde bir borçlu zaten kayıtlı."
    except sqlite3.Error as e:
        print(f"Borçlu eklenirken veritabanı hatası: {e}")
        return False, f"Veritabanı hatası: {e}"
    finally:
        conn.close()

def tum_borclulari_getir_db():
    """
    'borclular' tablosundaki tüm kişileri (id, isim) olarak getirir.
    İsme göre alfabetik sıralar.
    """
    conn = baglanti_olustur()
    if conn is None:
        return [] # Hata durumunda boş liste döndür

    try:
        cursor = conn.cursor()
        # İsimlerin alfabetik olarak gelmesi kullanıcı deneyimini iyileştirir.
        cursor.execute("SELECT id, isim FROM borclular ORDER BY isim COLLATE NOCASE")   ##COLLATE NOCASE büyük küçük harf ayrımını ortadan kaldırır
        borclular = cursor.fetchall()
        return borclular
    except sqlite3.Error as e:
        print(f"Borçlular getirilirken hata: {e}")
        return [] # Hata durumunda boş liste döndür
    finally:
        conn.close()

def borc_kaydet_db(borclu_id, sepet, toplam_tutar):
    """
    Belirli bir borclu_id'ye ait yeni bir borç işlemini kaydeder.
    """
    conn = baglanti_olustur()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()
        sepet_json = json.dumps(sepet, ensure_ascii=False)
        bugunun_tarihi = date.today().strftime('%Y-%m-%d')

        cursor.execute(
            """INSERT INTO borc_islemleri (borclu_id, tarih, sepet_icerigi, toplam_tutar)
               VALUES (?, ?, ?, ?)""",
            (borclu_id, bugunun_tarihi, sepet_json, toplam_tutar)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Borç kaydedilirken hata: {e}")
        return False
    finally:
        conn.close()

def borclunun_borclarini_getir_db(borclu_id):
    conn = baglanti_olustur()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, tarih, toplam_tutar, sepet_icerigi
            FROM borc_islemleri
            WHERE borclu_id = ?
            ORDER BY tarih DESC, id DESC""",
            (borclu_id,)
        )
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Kisinin borclari getirilirken hata:{e}")
        return []
    finally:
        conn.close()

def borc_ode_db(borc_islem_id):
    conn = baglanti_olustur()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        ## borlcu alma islemi
        cursor.execute("SELECT sepet_icerigi, toplam_tutar FROM borc_islemleri WHERE id = ? ", (borc_islem_id,))
        borc_detayi = cursor.fetchone()
        if borc_detayi is None:
            print(f"Hata: {borc_islem_id} ID'li borc islemi bulunamadi")
            return False
        sepet_icerigi, toplam_tutar = borc_detayi
        tarih = date.today().strftime("%Y-%m-%d")
        cursor.execute(
            "INSERT INTO satislar (satis_tarihi, sepet_icerigi, toplam_tutar) VALUES (?,?,?)",
            (tarih, sepet_icerigi, toplam_tutar)
        )

        #BORCU BORC TABLOSUNDAN SİLME
        cursor.execute("DELETE FROM borc_islemleri WHERE id= ?", (borc_islem_id,))

        conn.commit() #degisiklik onaylama
        return True
    except sqlite3.Error as e:
        conn.rollback()  # Herhangi bir hata olursa, tüm işlemleri geri al
        print(f"Borc odeme islemi sirasinda hata olustu: {e}")
        return False
    finally:
        conn.close()


##bu direk olarak borcu silme işlemi icin
def borc_sil_db(borc_islem_id):
    conn = baglanti_olustur()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM borc_islemleri WHERE id= ? ", (borc_islem_id,))
        # cursor.rowcount > 0, silme işleminin başarılı olup olmadığını (en az 1 satır etkilendi mi) kontrol eder.
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Borç silme hatası: {e}")
        return False
    finally:
        conn.close()

def borc_detayini_getir_db(borc_islem_id):
    """Verilen borç işlem ID'sine ait sepet içeriğini (JSON string) döndürür."""
    conn = baglanti_olustur()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT sepet_icerigi FROM borc_islemleri WHERE id=?", (borc_islem_id,))
        sonuc = cursor.fetchone()
        return sonuc[0] if sonuc else None
    except sqlite3.Error as e:
        print(f"Borç detayı getirilirken hata: {e}")
        return None
    finally:
        conn.close()

def borclunun_toplam_borcunu_getir_db(borclu_id):
    """
    Verilen borclu_id'ye ait tüm ödenmemiş borçların toplam tutarını hesaplar.
    """
    conn = baglanti_olustur()
    if conn is None:
        return 0.0 # Hata durumunda borcu 0 olarak kabul et

    try:
        cursor = conn.cursor()
        # 'borc_islemleri' tablosundaki 'toplam_tutar' sütununu,
        # sadece belirtilen 'borclu_id' için topluyoruz.
        cursor.execute(
            "SELECT SUM(toplam_tutar) FROM borc_islemleri WHERE borclu_id = ?",
            (borclu_id,)
        )
        sonuc = cursor.fetchone()[0]
        # Eğer kişinin hiç borcu yoksa sonuç None gelebilir, bunu 0'a çeviriyoruz.
        return sonuc if sonuc is not None else 0.0
    except sqlite3.Error as e:
        print(f"Kişinin toplam borcu getirilirken hata: {e}")
        return 0.0
    finally:
        conn.close()

def manuel_borc_ekle_db(borclu_id, tutar, aciklama = "Manuel Olarak Eklendi"):
    if not isinstance(tutar,(int,float)) or tutar < 0:
        print("Hata: Gecersiz Tutar")
        return False

    conn = baglanti_olustur()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        sepet_notu = json.dumps({"manuel_borc": True, "aciklama": aciklama})
        bugunun_tarihi = date.today().strftime("%Y-%m-%d")

        cursor.execute(
            """INSERT INTO borc_islemleri(borclu_id, tarih, sepet_icerigi, toplam_tutar)
               VALUES (?, ?, ?, ?)""",
            (borclu_id,bugunun_tarihi,sepet_notu,tutar)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Manuel borc eklenirken hata olustu: {e}")
        return False
    finally:
        conn.close()


def toplu_borc_ode_db(borc_islem_id_listesi):
    """
    Verilen ID listesindeki tüm borç işlemlerini ödenmiş olarak işaretler.
    Tüm işlemler tek bir transaction içinde yapılır.
    """
    if not borc_islem_id_listesi:
        return False, 0  # İşlenecek borç yoksa

    conn = baglanti_olustur()
    if conn is None:
        return False, 0

    odenen_borc_sayisi = 0
    try:
        cursor = conn.cursor()

        # Liste üzerindeki her bir ID için işlemleri tekrarla
        for borc_id in borc_islem_id_listesi:
            # 1. Adım: Borç detaylarını al
            cursor.execute("SELECT sepet_icerigi, toplam_tutar FROM borc_islemleri WHERE id = ?", (borc_id,))
            borc_detayi = cursor.fetchone()

            if borc_detayi:
                sepet_icerigi, toplam_tutar = borc_detayi
                bugunun_tarihi = date.today().strftime('%Y-%m-%d')

                # 2. Adım: Satışlar tablosuna ekle
                cursor.execute(
                    "INSERT INTO satislar (satis_tarihi, sepet_icerigi, toplam_tutar) VALUES (?, ?, ?)",
                    (bugunun_tarihi, sepet_icerigi, toplam_tutar)
                )

                # 3. Adım: Borçlar tablosundan sil
                cursor.execute("DELETE FROM borc_islemleri WHERE id = ?", (borc_id,))

                odenen_borc_sayisi += 1

        # 4. Adım: Döngü bittikten sonra TÜM değişiklikleri onayla
        conn.commit()
        return True, odenen_borc_sayisi

    except sqlite3.Error as e:
        # Herhangi bir hata olursa, o ana kadar yapılan TÜM işlemleri geri al
        conn.rollback()
        print(f"Toplu borç ödeme işlemi sırasında hata oluştu: {e}")
        return False, 0
    finally:
        conn.close()


