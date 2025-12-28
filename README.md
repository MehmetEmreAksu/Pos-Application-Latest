# KantinPOS - Envanter ve Veresiye Takip Sistemi

KantinPOS, küçük ölçekli işletmeler (kantin, kırtasiye vb.) için geliştirilmiş, Python tabanlı bir masaüstü Satış Noktası (POS) uygulamasıdır. Ürün yönetimi, stok takibi ve özellikle veresiye (borç) defteri yönetimini dijitalleştirmek amacıyla tasarlanmıştır.

## 🎯 Proje Özellikleri

Uygulama temel olarak üç ana modülden oluşmaktadır:

- **Hızlı Satış Ekranı:** Barkod okuyucu (klavye emülasyonu) ile entegre çalışabilen, sepet mantığına dayalı satış arayüzü.
- **Veresiye (Cari Hesap) Yönetimi:** Müşterilere özel borç kaydı açma, parçalı veya toplu ödeme alma ve bakiye takibi.
- **Stok ve Raporlama:** Ürünlerin CRUD (Ekle/Sil/Güncelle) işlemleri ve tarih bazlı satış raporları.

## 🛠 Teknik Altyapı ve Mimari

Proje, iş mantığı (Business Logic) ve arayüz (GUI) katmanlarını modüler tutmak adına parçalı bir dosya yapısıyla geliştirilmiştir.

- **Dil:** Python 3.x
- **Veritabanı:** SQLite3
- **Arayüz:** CustomTkinter (Modern UI), Tkinter
- **Veri Formatı:** JSON (İlişkisel veritabanı içinde NoSQL benzeri veri saklama)

### Öne Çıkan Teknik Detaylar

- **ACID Transaction Yönetimi:** Veri bütünlüğünü sağlamak adına, özellikle stok düşümü ve satış kaydı gibi kritik işlemlerde `commit` ve `rollback` mekanizmaları kullanılmıştır.
- **Hibrit Veri Yapısı:** Satış detayları ve sepet içerikleri, sorgu performansını artırmak ve esneklik sağlamak amacıyla SQLite içerisinde `JSON` formatında serialize edilerek saklanmaktadır.
- **Event-Driven UX:** Kullanıcı deneyimini hızlandırmak için barkod okutma sonrası otomatik odaklanma (focus handling) ve klavye kısayolları (Enter, Space) entegre edilmiştir.
- **SQL Enjeksiyon Koruması:** Tüm veritabanı sorguları parametrik yapıda (placeholder kullanımı) yazılarak güvenlik sağlanmıştır.

## 📂 Dosya Yapısı

- `main.py`: Uygulamanın giriş noktası ve ana GUI döngüsü.
- `database_operations.py`: Veritabanı bağlantısı, tablo oluşturma ve temel CRUD işlemleri.
- `debt_operations.py`: Borçlanma, ödeme alma ve cari hesap sorguları için özelleşmiş veritabanı fonksiyonları.
- `debt_gui.py`: Borç yönetimi için özelleştirilmiş, callback mekanizması ile ana pencereyle haberleşen arayüz modülü.

## 🚀 Kurulum ve Çalıştırma

Gerekli kütüphanelerin yüklenmesi:

```bash
pip install customtkinter tkcalendar
