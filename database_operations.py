import sqlite3
import json
from datetime import date

VERITABANI_ADI = 'kantin.db'

def baglanti_olustur():
    conn = None
    try:
        conn = sqlite3.connect(VERITABANI_ADI)
        return conn
    except sqlite3.Error as e:
        print(e)
    return conn

def tablo_olustur():
    conn = baglanti_olustur()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS urunler (
                    barkod TEXT PRIMARY KEY,
                    urun_adi TEXT NOT NULL,
                    fiyat REAL NOT NULL,
                    stok INTEGER NOT NULL DEFAULT 0
                )
            """)
            # YENİ EKLENEN SATIŞLAR TABLOSU
            # Bu tablo, her bir sepet satışını tek bir kayıt olarak tutar.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS satislar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    satis_tarihi DATE NOT NULL,
                    sepet_icerigi TEXT NOT NULL, -- Sepeti JSON formatında saklayacağız
                    toplam_tutar REAL NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS borclular (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    isim TEXT NOT NULL UNIQUE
                )
            """)

            # 2. Borç işlemlerini tutan tablo. 'debtor_name' yerine 'borclu_id' kullanıyoruz.
            # Bu, 'borclular' tablosuna bir referanstır (Foreign Key).
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS borc_islemleri (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    borclu_id INTEGER NOT NULL,
                    tarih DATE NOT NULL,
                    sepet_icerigi TEXT NOT NULL,
                    toplam_tutar REAL NOT NULL,
                    FOREIGN KEY (borclu_id) REFERENCES borclular (id)
                )
            """)
            conn.commit()
        except sqlite3.Error as e:
            print(e)
        finally:
            conn.close()

def save_debt_db(debtor_name, cart, total_amount):
    """Verilen borcu 'debts' tablosuna kaydeder."""
    conn = baglanti_olustur()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cart_json = json.dumps(cart, ensure_ascii=False)
            today_date = date.today().strftime('%Y-%m-%d')
            cursor.execute(
                "INSERT INTO debts (debtor_name, debt_date, cart_contents, total_amount) VALUES (?, ?, ?, ?)",
                (debtor_name, today_date, cart_json, total_amount)
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Debt recording error: {e}")
            return False
        finally:
            conn.close()
    return False

def get_all_debts_db():
    """Tüm borçları, borçlu adına göre sıralayarak getirir."""
    conn = baglanti_olustur()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, debtor_name, total_amount, debt_date FROM debts ORDER BY debtor_name, id DESC")
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error fetching debts: {e}")
            return []
        finally:
            conn.close()
    return []

def delete_debt_db(debt_id):
    """Verilen ID'ye sahip borcu siler."""
    conn = baglanti_olustur()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM debts WHERE id=?", (debt_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Database delete error (debt): {e}")
            return False
        finally:
            conn.close()
    return False


def satis_kaydet_db(sepet, toplam_tutar):
    """Onaylanan sepeti 'satislar' tablosuna tek bir kayıt olarak ekler."""
    conn = baglanti_olustur()
    if conn is not None:
        try:
            cursor = conn.cursor()

            # Python sözlüğünü (sepet) JSON formatında bir metne çevir
            sepet_json = json.dumps(sepet, ensure_ascii=False)

            # Bugünün tarihini al (YYYY-AA-GG formatında)
            bugunun_tarihi = date.today().strftime('%Y-%m-%d')

            cursor.execute(
                "INSERT INTO satislar (satis_tarihi, sepet_icerigi, toplam_tutar) VALUES (?, ?, ?)",
                (bugunun_tarihi, sepet_json, toplam_tutar)
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Satış kaydı hatası: {e}")
            return False
        finally:
            conn.close()
    return False

def urun_ekle_db(barkod, urun_adi, fiyat, stok=0):
    conn = baglanti_olustur()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO urunler (barkod, urun_adi, fiyat, stok) VALUES (?, ?, ?, ?)", (barkod, urun_adi, fiyat, stok))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # Barkod zaten var
        except sqlite3.Error as e:
            print(f"Veritabanı hatası: {e}")
            return False
        finally:
            conn.close()
    return False

def urun_bilgisi_getir_db(barkod):
    conn = baglanti_olustur()
    if conn is not None:
        try:
            cursor = conn.cursor()
            # Sorguya 'stok' bilgisini ekliyoruz
            cursor.execute("SELECT barkod, urun_adi, fiyat, stok FROM urunler WHERE barkod=?", (barkod,))
            return cursor.fetchone() # Artık 4 değer döndürecek: (barkod, ad, fiyat, stok)
        except sqlite3.Error as e:
            print(f"Veritabanı hatası: {e}")
            return None
        finally:
            conn.close()
    return None

def tum_urunleri_getir_db():
    conn = baglanti_olustur()
    if conn is not None:
        try:
            cursor = conn.cursor()
            # Sorguya 'stok' sütununu ekliyoruz
            cursor.execute("SELECT barkod, urun_adi, fiyat, stok FROM urunler")
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Veritabanı hatası: {e}")
            return None
        finally:
            conn.close()
    return None

# database_operations.py dosyasına ekleyin

def urun_guncelle_db(barkod, urun_adi=None, fiyat=None, stok=None):
    conn = baglanti_olustur()
    if conn is not None:
        try:
            cursor = conn.cursor()
            guncellenecekler = []
            parametreler = []
            if urun_adi is not None:
                guncellenecekler.append("urun_adi=?")
                parametreler.append(urun_adi)
            if fiyat is not None:
                guncellenecekler.append("fiyat=?")
                parametreler.append(fiyat)
            if stok is not None:
                guncellenecekler.append("stok=?")
                parametreler.append(stok)

            if guncellenecekler:
                sorgu = f"UPDATE urunler SET {', '.join(guncellenecekler)} WHERE barkod=?"
                parametreler.append(barkod)
                cursor.execute(sorgu, tuple(parametreler))
                conn.commit()
                return True
            return False # Güncellenecek bir alan yoksa
        except sqlite3.Error as e:
            print(f"Veritabanı güncelleme hatası: {e}")
            return False
        finally:
            conn.close()
    return False

# database_operations.py dosyasına bu yeni fonksiyonu ekleyin

def urun_sil_db(barkod):
    conn = baglanti_olustur()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM urunler WHERE barkod=?", (barkod,))
            conn.commit()
            # Değişiklikten etkilenen satır sayısını kontrol et
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Veritabanı silme hatası: {e}")
            return False
        finally:
            conn.close()
    return False

def tum_satislari_getir_db():
    """satislar tablosundaki tüm ana satış kayıtlarını getirir."""
    conn = baglanti_olustur()
    if conn is not None:
        try:
            cursor = conn.cursor()
            # En son satışı en üstte görmek için ID'ye göre tersten sırala
            cursor.execute("SELECT id, satis_tarihi, toplam_tutar FROM satislar ORDER BY id DESC")
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Satışlar getirilirken hata: {e}")
            return []
        finally:
            conn.close()
    return []

def satis_detayini_getir_db(satis_id):
    """Verilen ID'ye sahip satışın JSON formatındaki sepet içeriğini döndürür."""
    conn = baglanti_olustur()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT sepet_icerigi FROM satislar WHERE id=?", (satis_id,))
            sonuc = cursor.fetchone()
            # fetchone() bir demet (tuple) döndürür, ör: ('{"json...}',), biz sadece içindeki metni istiyoruz.
            return sonuc[0] if sonuc else None
        except sqlite3.Error as e:
            print(f"Satış detayı getirilirken hata: {e}")
            return None
        finally:
            conn.close()
    return None


def urun_bazli_rapor_getir_db(baslangic_tarihi, bitis_tarihi):
    """
    Belirtilen tarih aralığında, her bir ürünün toplam satış adedini ve
    toplam gelirini hesaplar.
    """
    conn = baglanti_olustur()
    if conn is None:
        return []

    # Bu SQL sorgusu, JSON içindeki verileri parçalayıp analiz eder.
    sorgu = """
        SELECT
            urun_detay.value ->> '$.isim' AS urun_adi,
            SUM(CAST(urun_detay.value ->> '$.adet' AS INTEGER)) AS toplam_adet,
            SUM( (CAST(urun_detay.value ->> '$.adet' AS REAL)) * (CAST(urun_detay.value ->> '$.fiyat' AS REAL)) ) AS toplam_gelir
        FROM
            satislar,
            json_each(sepet_icerigi) AS urun_detay
        WHERE
            satis_tarihi BETWEEN ? AND ?
        GROUP BY
            urun_adi
        ORDER BY
            toplam_gelir DESC;
    """

    try:
        cursor = conn.cursor()
        cursor.execute(sorgu, (baslangic_tarihi, bitis_tarihi))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Ürün bazlı rapor hatası: {e}")
        # Hata genellikle eski SQLite sürümünden kaynaklanır.
        # Bu durumda kullanıcıya bir uyarı göstermek iyi olabilir.
        return f"HATA: {e}"
    finally:
        conn.close()


