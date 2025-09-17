import customtkinter as ctk
import tkinter as tk
import tkinter.messagebox
from tkinter import ttk
from tkcalendar import DateEntry
import json

from debt_gui import BorcluSecimPenceresi, BorcDefteriPenceresi

# Veritabanı fonksiyonlarını import et
from database_operations import (
    urun_ekle_db, urun_bilgisi_getir_db, tum_urunleri_getir_db,
    urun_guncelle_db, urun_sil_db, tablo_olustur,
    satis_kaydet_db, tum_satislari_getir_db, satis_detayini_getir_db,
    urun_bazli_rapor_getir_db
)


class KantinArayuzu:
    def __init__(self, master):
        self.master = master
        master.title("Kantin Uygulaması")
        self.sutunlar = ("Barkod", "Ürün Adı", "Fiyat (TL)", "Stok")

        # Her Treeview'ın kendi sıralama durumunu (sütun ve yön) burada saklayacağız.
        self.sort_states = {}
        # ------------------------------------------

        # Butonları tutacak bir ana çerçeve
        main_frame = ctk.CTkFrame(master)
        main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        # Butonlar
        self.btn_urun_ekle = ctk.CTkButton(main_frame, text="Ürün Ekle / Yönet", command=self.urunleri_listele_arayuzu,
                                           height=40)
        self.btn_urun_ekle.pack(pady=10, padx=10, fill="x")

        self.btn_urun_sat = ctk.CTkButton(main_frame, text="Hızlı Satış Ekranı", command=self.urun_sat_arayuzu,
                                          height=50, fg_color="#4CAF50", hover_color="#45a049")
        self.btn_urun_sat.pack(pady=10, padx=10, fill="x")

        self.btn_satis_goruntule = ctk.CTkButton(main_frame, text="Satış Raporları",command=self.satis_goruntule_arayuzu, height=40)
        self.btn_satis_goruntule.pack(pady=10, padx=10, fill="x")

        self.btn_cikis = ctk.CTkButton(main_frame, text="Çıkış", command=master.quit, height=40, fg_color="#D32F2F",hover_color="#B71C1C")
        self.btn_cikis.pack(pady=10, padx=10, fill="x")

        self.btn_view_debts = ctk.CTkButton(main_frame, text="Borç Defteri", command=self.view_debts_interface, height=40, fg_color="#607D8B", hover_color="#455A64")
        self.btn_view_debts.pack(pady=10, padx=10, fill="x")

    def satis_goruntule_arayuzu(self):
        satis_penceresi = ctk.CTkToplevel(self.master)
        satis_penceresi.title("Satış Raporları")
        #satis_penceresi.transient(self.master)
        ##satis_penceresi.geometry("1024x768")

        #satis_penceresi.resizable(True, True)

        # Sabit boyut vermek yerine, minimum boyut
        satis_penceresi.minsize(width=900, height=600)

        ##satis_penceresi.after(50,lambda : satis_penceresi.lift())
        # İsteğe bağlı: Pencereyi ekranın ortasında başlat
        satis_penceresi.geometry("+%d+%d" % (self.master.winfo_x() + 50, self.master.winfo_y() + 50))
        # -------------------------

        satis_penceresi.after(50, lambda : satis_penceresi.focus_set())


        ##satis_penceresi.grab_set()

        tabview = ctk.CTkTabview(satis_penceresi, width=250)
        tabview.pack(padx=20, pady=20, fill="both", expand=True)
        tabview.add("Sepet Bazlı Satışlar")
        tabview.add("Ürün Bazlı Rapor")

        # --- Treeview STİLİNİ AYARLAMA ---
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2a2d2e", foreground="white", fieldbackground="#343638", borderwidth=0)
        style.map('Treeview', background=[('selected', '#22559b')])
        style.configure("Treeview.Heading", background="#565b5e", foreground="white", relief="flat",
                        font=('Calibri', 10, 'bold'))
        style.map("Treeview.Heading", background=[('active', '#3484F0')])

        # --- Sekme 1: Sepet Bazlı Satışlar ---
        sekme1 = tabview.tab("Sepet Bazlı Satışlar")
        ana_cerceve_s1 = ctk.CTkFrame(sekme1, fg_color="transparent")
        ana_cerceve_s1.pack(fill='both', expand=True)

        sol_cerceve = ctk.CTkFrame(ana_cerceve_s1)
        sol_cerceve.pack(side='left', fill='both', expand=True, padx=(0, 5), pady=5)
        ctk.CTkLabel(sol_cerceve, text="Satış Listesi", font=('Arial', 16, 'bold')).pack(pady=10)

        satis_sutunlar = ('ID', 'Tarih', 'Toplam Tutar')
        satislar_tree = ttk.Treeview(sol_cerceve, columns=satis_sutunlar, show='headings')
        satislar_tree.pack(fill='both', expand=True, padx=5, pady=5)

        sag_cerceve = ctk.CTkFrame(ana_cerceve_s1)
        sag_cerceve.pack(side='right', fill='both', expand=True, padx=(5, 0), pady=5)
        ctk.CTkLabel(sag_cerceve, text="Seçili Satışın İçeriği", font=('Arial', 16, 'bold')).pack(pady=10)
        detay_tree = ttk.Treeview(sag_cerceve, columns=('Ürün', 'Adet', 'Fiyat'), show='headings')
        detay_tree.pack(fill='both', expand=True, padx=5, pady=5)

        satis_numeric_cols = ('ID', 'Toplam Tutar')
        for col, text, width in [('ID', 'ID', 50), ('Tarih', 'Tarih', 120), ('Toplam Tutar', 'Toplam (TL)', 120)]:
            satislar_tree.heading(col, text=text, command=lambda c=col: self.generic_treeview_sort(satislar_tree, c, satis_sutunlar, satis_numeric_cols))
            satislar_tree.column(col, width=width)
        for col, text, width in [('Ürün', 'Ürün Adı', 150), ('Adet', 'Adet', 60), ('Fiyat', 'Satış Fiyatı (TL)', 100)]:
            detay_tree.heading(col, text=text)
            detay_tree.column(col, width=width)

        def satislari_yukle():
            for i in satislar_tree.get_children(): satislar_tree.delete(i)
            for satis_id, tarih, toplam in tum_satislari_getir_db():
                satislar_tree.insert('', 'end', values=(satis_id, tarih, f"{toplam:.2f}"))

        def satis_detayini_goster(event):
            for i in detay_tree.get_children(): detay_tree.delete(i)
            secili_ogeler = satislar_tree.selection()
            if not secili_ogeler: return
            secili_satis_id = satislar_tree.item(secili_ogeler[0])['values'][0]
            sepet_json = satis_detayini_getir_db(secili_satis_id)
            if sepet_json:
                for barkod, detay in json.loads(sepet_json).items():
                    detay_tree.insert('', 'end', values=(detay['isim'], detay['adet'], f"{detay['fiyat']:.2f}"))

        satislar_tree.bind('<<TreeviewSelect>>', satis_detayini_goster)
        satislari_yukle()

        # --- Sekme 2: Ürün Bazlı Rapor ---
        sekme2 = tabview.tab("Ürün Bazlı Rapor")
        ust_cerceve_s2 = ctk.CTkFrame(sekme2, fg_color="transparent")
        ust_cerceve_s2.pack(pady=10, padx=10, fill='x')

        ctk.CTkLabel(ust_cerceve_s2, text="Başlangıç:").pack(side='left')
        cal_baslangic = DateEntry(ust_cerceve_s2, width=12, date_pattern='dd.mm.yyyy')
        cal_baslangic.pack(side='left', padx=(5, 20))
        ctk.CTkLabel(ust_cerceve_s2, text="Bitiş:").pack(side='left')
        cal_bitis = DateEntry(ust_cerceve_s2, width=12, date_pattern='dd.mm.yyyy')
        cal_bitis.pack(side='left', padx=5)

        rapor_tree = ttk.Treeview(sekme2, columns=('Ürün', 'Adet', 'Gelir'), show='headings')
        rapor_tree.heading('Ürün', text='Ürün Adı')
        rapor_tree.heading('Adet', text='Toplam Satış Adedi')
        rapor_tree.heading('Gelir', text='Toplam Gelir (TL)')
        rapor_tree.pack(pady=10, padx=10, fill='both', expand=True)

        lbl_genel_toplam = ctk.CTkLabel(sekme2, text="Genel Toplam Gelir: 0.00 TL", font=('Arial', 16, 'bold'))
        lbl_genel_toplam.pack(pady=10)

        def urun_raporu_getir():
            for i in rapor_tree.get_children(): rapor_tree.delete(i)
            bas_tarih = cal_baslangic.get_date().strftime('%Y-%m-%d')
            bit_tarih = cal_bitis.get_date().strftime('%Y-%m-%d')
            sonuclar = urun_bazli_rapor_getir_db(bas_tarih, bit_tarih)

            if isinstance(sonuclar, str) and sonuclar.startswith("HATA"):
                tkinter.messagebox.showerror("Veritabanı Hatası",
                                             f"Rapor alınamadı.\n\nDetay: {sonuclar}\n\nLütfen SQLite sürümünüzün güncel olduğundan emin olun.")
                return

            genel_toplam = 0
            for urun_adi, toplam_adet, toplam_gelir in sonuclar:
                rapor_tree.insert('', 'end', values=(urun_adi, toplam_adet, f"{toplam_gelir:.2f}"))
                if toplam_gelir: genel_toplam += toplam_gelir

            lbl_genel_toplam.configure(text=f"Genel Toplam Gelir: {genel_toplam:.2f} TL")

        btn_rapor_getir = ctk.CTkButton(ust_cerceve_s2, text="Raporu Getir", command=urun_raporu_getir)
        btn_rapor_getir.pack(side='left', padx=20)

    def urun_ekle_arayuzu(self):
        urun_ekle_penceresi = ctk.CTkToplevel(self.master)
        urun_ekle_penceresi.title("Yeni Ürün Ekle")
        #urun_ekle_penceresi.transient(self.master)


        urun_ekle_penceresi.minsize(width=900, height=600)
        urun_ekle_penceresi.geometry("+%d+%d" % (self.master.winfo_x() + 50, self.master.winfo_y() + 50))  ##ortalamak için

        urun_ekle_penceresi.after(50, lambda: urun_ekle_penceresi.focus_set())

        ##urun_ekle_penceresi.grab_set()
        urun_ekle_penceresi.grid_columnconfigure(1, weight=1)

        lbl_font = ("Arial", 14)

        ctk.CTkLabel(urun_ekle_penceresi, text="Barkod:", font=lbl_font).grid(row=0, column=0, padx=20, pady=10,
                                                                              sticky="w")
        ent_barkod = ctk.CTkEntry(urun_ekle_penceresi, font=lbl_font, height=35)
        ent_barkod.grid(row=0, column=1, padx=20, pady=10, sticky='ew')

        # --- DEĞİŞİKLİK BURADA ---
        # focus_set() komutunu doğrudan çağırmak yerine, pencereye küçük bir gecikmeyle
        # çalıştırmasını söylüyoruz. Bu, pencerenin hazır olmasını garantiler.
        urun_ekle_penceresi.after(100, lambda: ent_barkod.focus_set())
        # --- DEĞİŞİKLİK BİTTİ ---

        ctk.CTkLabel(urun_ekle_penceresi, text="Ürün Adı:", font=lbl_font).grid(row=1, column=0, padx=20, pady=10,
                                                                                sticky="w")
        ent_urun_adi = ctk.CTkEntry(urun_ekle_penceresi, font=lbl_font, height=35)
        ent_urun_adi.grid(row=1, column=1, padx=20, pady=10, sticky='ew')

        ctk.CTkLabel(urun_ekle_penceresi, text="Fiyat (TL):", font=lbl_font).grid(row=2, column=0, padx=20, pady=10,
                                                                                  sticky="w")
        ent_fiyat = ctk.CTkEntry(urun_ekle_penceresi, font=lbl_font, height=35)
        ent_fiyat.grid(row=2, column=1, padx=20, pady=10, sticky='ew')

        ctk.CTkLabel(urun_ekle_penceresi, text="Stok Adedi:", font=lbl_font).grid(row=3, column=0, padx=20, pady=10,
                                                                                  sticky="w")
        ent_stok = ctk.CTkEntry(urun_ekle_penceresi, font=lbl_font, height=35)
        ent_stok.insert(0, "0")
        ent_stok.grid(row=3, column=1, padx=20, pady=10, sticky='ew')

        def urun_ekle_islem(event=None):
            barkod, urun_adi = ent_barkod.get(), ent_urun_adi.get()
            if not barkod or not urun_adi:
                tkinter.messagebox.showerror("Hata", "Barkod ve Ürün Adı alanları boş bırakılamaz.")
                return
            try:
                fiyat, stok = float(ent_fiyat.get()), int(ent_stok.get())
                if urun_ekle_db(barkod, urun_adi, fiyat, stok):
                    urun_ekle_penceresi.destroy()
                    self.urun_listesini_yenile()
                    self.urun_ekle_arayuzu()
                else:
                    tkinter.messagebox.showerror("Hata", "Bu barkoda sahip bir ürün zaten kayıtlı.")
            except ValueError:
                tkinter.messagebox.showerror("Hata", "Fiyat ve Stok alanlarına geçerli sayılar girin.")

        btn_ekle = ctk.CTkButton(urun_ekle_penceresi, text="Ürünü Kaydet", command=urun_ekle_islem, height=40)
        btn_ekle.grid(row=4, column=0, columnspan=2, padx=20, pady=20, sticky='ew')
        urun_ekle_penceresi.bind("<Return>", urun_ekle_islem)



    def urun_sat_arayuzu(self):
        urun_sat_penceresi = ctk.CTkToplevel(self.master)
        ##urun_sat_penceresi.transient(self.master)
        ##urun_sat_penceresi.grab_set()
        urun_sat_penceresi.title("Ürün Sat")

        urun_sat_penceresi.minsize(width=800, height=600)
        ##urun_sat_penceresi.after(50,lambda : urun_sat_penceresi.lift())

        ust_cerceve = ctk.CTkFrame(urun_sat_penceresi, fg_color="transparent")
        ust_cerceve.pack(fill='x', padx=20, pady=10)
        ctk.CTkLabel(ust_cerceve, text="Barkod Okut:", font=("Arial", 14)).pack(side='left')


        self.barkod_var = ctk.StringVar()

        self.ent_barkod = ctk.CTkEntry(ust_cerceve, height=40, font=("Arial", 16),textvariable=self.barkod_var)
        self.ent_barkod.pack(side='left', fill='x', expand=True, padx=10)
        # --- DEĞİŞİKLİK BURADA ---
        # focus_set() komutunu doğrudan çağırmak yerine, pencereye küçük bir gecikmeyle
        # çalıştırmasını söylüyoruz. Bu, pencerenin hazır olmasını garantiler.
        urun_sat_penceresi.after(100, lambda: self.ent_barkod.focus_set())

        self.sepet = {}
        self.lbl_sepet_toplam = ctk.CTkLabel(urun_sat_penceresi, text="Sepet Toplam: 0.00 TL",
                                             font=("Arial", 22, "bold"))
        self.lbl_sepet_toplam.pack(pady=10)

        # Listbox standart tkinter'dan kalıyor
        self.sepet_listesi = tk.Listbox(urun_sat_penceresi, bg="#2B2B2B", fg="white", selectbackground="#1F6AA5",font=("Arial", 14), borderwidth=0, highlightthickness=0)
        self.sepet_listesi.pack(padx=20, pady=10, fill='both', expand=True)

        alt_cerceve = ctk.CTkFrame(urun_sat_penceresi, fg_color="transparent")
        alt_cerceve.pack(fill='x', padx=20, pady=20)

        btn_sil = ctk.CTkButton(alt_cerceve, text="Adet Azalt", command=self.urun_sil_sepet, height=40,fg_color="#D32F2F", hover_color="#B71C1C")
        btn_sil.pack(side=tk.LEFT, padx=10)

        btn_save_as_debt = ctk.CTkButton(alt_cerceve, text="Borç Ekle", command=self.process_save_as_debt,height=40, fg_color="#FFC107", text_color="black", hover_color="#FFA000")
        btn_save_as_debt.pack(side=tk.LEFT, padx=5)

        btn_onayla = ctk.CTkButton(alt_cerceve, text="Satışı Onayla", command=self.satisi_onayla, height=40,fg_color="#4CAF50", hover_color="#45a049")
        btn_onayla.pack(side=tk.RIGHT, padx=10)

        ###### BEYTULLAH ABİ İCİN OLAN VERSİYON###########
        #self.ent_barkod.bind("<Return>", self.urun_ekle_sepete)
        #self.ent_barkod.bind("<space>", self.satisi_onayla)

        self.barkod_var.trace_add("write", self.barkod_degisti)
        self.ent_barkod.bind("<space>", self.urun_ekle_sepete)
        urun_sat_penceresi.bind("<Return>", self.satisi_onayla)

    def barkod_degisti(self, *args):
        """Barkod giriş alanındaki her değişiklikte bu fonksiyon çalışır."""

        # Giriş alanındaki mevcut metni al
        mevcut_barkod = self.barkod_var.get()

        # Eğer metnin uzunluğu tam olarak 13 ise, işlemi başlat
        if len(mevcut_barkod) == 13:
            print(f"13 haneli barkod algılandı: {mevcut_barkod}. Otomatik ekleniyor...")

            # urun_ekle_sepete fonksiyonunu çağır.
            # Bu fonksiyon normalde bir 'event' bekler ama biz None göndererek
            # manuel olarak tetiklendiğini belirtiyoruz.
            self.urun_ekle_sepete(event=None)

    def urun_ekle_sepete(self, event=None):
        # .strip() ile kullanıcı yanlışlıkla boşluk bırakırsa onu da temizleriz.
        barkod = self.ent_barkod.get().strip()
        self.ent_barkod.delete(0, ctk.END)

        # Eğer barkod boşsa (kullanıcı sadece space'e bastıysa) hiçbir şey yapma.
        if not barkod:
            return "break"  # Olayı burada kes, boşluk karakteri yazılmasın.

        urun = urun_bilgisi_getir_db(barkod)
        if urun:
            barkod, urun_adi, fiyat, stok = urun
            sepetteki_adet = self.sepet.get(barkod, {}).get("adet", 0)
            if stok <= sepetteki_adet:
                tkinter.messagebox.showwarning("Stok Yetersiz", f"'{urun_adi}' ürünü için stok yetersiz!")
                # Hata durumunda da olayı kesmek önemlidir.
                return "break"

            if barkod in self.sepet:
                self.sepet[barkod]["adet"] += 1
            else:
                self.sepet[barkod] = {"isim": urun_adi, "fiyat": fiyat, "adet": 1}
            self.sepeti_yenile()
        else:
            tkinter.messagebox.showerror("Hata", "Bu barkoda sahip bir ürün bulunamadı.")

        # EN ÖNEMLİ SATIR:
        # Fonksiyonun sonunda, olayın yayılmasını engellemek için "break" döndür.
        return "break"

    def urun_sil_sepet(self):
        try:
            secili_index = self.sepet_listesi.curselection()[0]
        except IndexError:
            tkinter.messagebox.showwarning("Uyarı", "Silmek için sepetten ürün seçin.")
            return

        secili_metin = self.sepet_listesi.get(secili_index)
        silinecek_barkod = None
        for barkod, urun_detay in self.sepet.items():
            olusturulan_metin = f"{urun_detay['isim']} - Adet: {urun_detay['adet']} - Fiyat: {urun_detay['fiyat']:.2f} TL"
            if olusturulan_metin == secili_metin:
                silinecek_barkod = barkod
                break

        if silinecek_barkod:
            if self.sepet[silinecek_barkod]['adet'] > 1:
                self.sepet[silinecek_barkod]['adet'] -= 1
            else:
                del self.sepet[silinecek_barkod]
            self.sepeti_yenile()

    def sepeti_yenile(self):
        self.sepet_listesi.delete(0, tk.END)
        toplam_fiyat = 0
        for item in self.sepet.values():
            toplam_fiyat += item["fiyat"] * item["adet"]
            self.sepet_listesi.insert(tk.END, f"{item['isim']} - Adet: {item['adet']} - Fiyat: {item['fiyat']:.2f} TL")
        self.lbl_sepet_toplam.configure(text=f"Sepet Toplam: {toplam_fiyat:.2f} TL")

    def satisi_onayla(self, event=None):
        # Eğer sepet boşsa, kullanıcı boşuna space'e basmış olabilir.
        # Bu durumda sadece olayı keselim ki boşluk yazılmasın.
        if not self.sepet:
            # İsteğe bağlı olarak bir uyarı mesajı gösterebilir veya sessiz kalabilirsin.
            # tkinter.messagebox.showerror("Hata", "Sepet boş.")
            return "break"

        toplam_fiyat = sum(item['fiyat'] * item['adet'] for item in self.sepet.values())

        for barkod, urun_detay in self.sepet.items():
            urun_db = urun_bilgisi_getir_db(barkod)
            if not urun_db or urun_db[3] < urun_detay['adet']:
                tkinter.messagebox.showerror("Stok Hatası",f"'{urun_detay['isim']}' için stok yetersiz! Satış iptal edildi.")
                return "break"  # Hata durumunda da olayı kes

        # Stokları düşür
        for barkod, urun_detay in self.sepet.items():
            urun_db = urun_bilgisi_getir_db(barkod)
            yeni_stok = urun_db[3] - urun_detay['adet']
            urun_guncelle_db(barkod, stok=yeni_stok)

        # Satışı kaydet
        if satis_kaydet_db(self.sepet, toplam_fiyat):
            print("Satış, 'satislar' tablosuna başarıyla kaydedildi.")
        else:
            tkinter.messagebox.showwarning("Kayıt Hatası", "Stoklar güncellendi ancak satış geçmişi kaydedilemedi.")

        # Sepeti temizle ve arayüzü hazırla
        self.sepet.clear()
        self.sepeti_yenile()
        self.ent_barkod.focus_set()

        # EN ÖNEMLİ KISIM: Olayın yayılmasını engelle.
        return "break"

    def urunleri_listele_arayuzu(self):
        urun_listesi_penceresi = ctk.CTkToplevel(self.master)
        urun_listesi_penceresi.title("Envanter Yönetimi")
        ##urun_listesi_penceresi.transient(self.master)


        urun_listesi_penceresi.minsize(width=800, height=600)
        urun_listesi_penceresi.geometry("+%d+%d" % (self.master.winfo_x() + 50, self.master.winfo_y() + 50))  ##ortalamak için

        urun_listesi_penceresi.after(50 ,lambda :urun_listesi_penceresi.focus_set())

        ##urun_listesi_penceresi.grab_set()

        ust_cerceve = ctk.CTkFrame(urun_listesi_penceresi, fg_color="transparent")
        ust_cerceve.pack(fill="x", padx=10, pady=10)

        btn_yeni_urun = ctk.CTkButton(ust_cerceve, text="Yeni Ürün Ekle", command=self.urun_ekle_arayuzu)
        btn_yeni_urun.pack(side="left")

        # --- YENİ ARAMA ÇUBUĞU KISMI ---
        # Arama metnini tutacak bir değişken
        self.arama_var = ctk.StringVar()

        # Arama kutusunu oluştur ve değişkene bağla
        arama_kutusu = ctk.CTkEntry(ust_cerceve, placeholder_text="Ürün Adına Göre Ara...",textvariable=self.arama_var, height=35)
        arama_kutusu.pack(side="right", fill="x", expand=True, padx=(20, 0))

        # Değişken her güncellendiğinde (yazı yazıldığında) listeyi yenile
        self.arama_var.trace_add("write", self.urun_listesini_yenile)
        # --- YENİ KISIM BİTTİ ---

        self.urun_tablosu = ttk.Treeview(urun_listesi_penceresi, columns=self.sutunlar, show='headings')
        self.urun_tablosu.pack(side="top", fill="both", expand=True, padx=10, pady=10)

        numeric_cols = ("Fiyat (TL)", "Stok")
        for sutun in self.sutunlar:
            self.urun_tablosu.heading(sutun, text=sutun,command=lambda c=sutun: self.generic_treeview_sort(self.urun_tablosu, c,self.sutunlar, numeric_cols))

        alt_cerceve = ctk.CTkFrame(urun_listesi_penceresi, fg_color="transparent")
        alt_cerceve.pack(fill="x", padx=10, pady=10)

        self.lbl_envanter_degeri = ctk.CTkLabel(alt_cerceve, text="Toplam Değer: 0.00 TL", font=("Arial", 16, "bold"))
        self.lbl_envanter_degeri.pack(pady=(0, 10))

        btn_sil = ctk.CTkButton(alt_cerceve, text="Seçili Ürünü Sil", command=self.secili_urunu_sil, fg_color="#D32F2F",hover_color="#B71C1C")
        btn_sil.pack(pady=10)

        self.urun_listesini_yenile()

        self.urun_tablosu.bind("<Double-1>", self.duzenle_hucre)
        self.duzenlenen_hucre, self.duzenleme_entry = None, None

    def urun_listesini_yenile(self, *args):
        # Tabloyu temizle
        for i in self.urun_tablosu.get_children():
            self.urun_tablosu.delete(i)

        # Arama kutusundaki metni al (küçük harfe çevirerek)
        arama_terimi = self.arama_var.get().lower()

        # Veritabanından TÜM ürünleri al
        urunler = tum_urunleri_getir_db()

        toplam_deger = 0.0

        if urunler:
            for barkod, urun_adi, fiyat, stok in urunler:
                # Eğer arama terimi, ürün adının içinde geçiyorsa (küçük harf kontrolü ile)
                if arama_terimi in urun_adi.lower():
                    # Bu ürünü tabloya ekle
                    self.urun_tablosu.insert("", tk.END, values=(barkod, urun_adi, f"{fiyat:.2f}", stok))

                    toplam_deger += (fiyat * stok)

        # --- YENİ EKLENEN ETİKET GÜNCELLEME SATIRI ---
        # Döngü bittikten sonra, hesaplanan toplam değeri etikete yazdır
        self.lbl_envanter_degeri.configure(text=f"Görüntülenen Ürünlerin Toplam Değeri: {toplam_deger:.2f} TL")
        # --- YENİ KISIM BİTTİ ---

    def secili_urunu_sil(self):
        secili_ogeler = self.urun_tablosu.selection()
        if not secili_ogeler:
            tkinter.messagebox.showwarning("Uyarı", "Lütfen silmek için bir ürün seçin.")
            return

        secili_id = secili_ogeler[0]
        urun_bilgileri = self.urun_tablosu.item(secili_id, 'values')
        barkod, urun_adi = urun_bilgileri[0], urun_bilgileri[1]

        emin_misin = tkinter.messagebox.askyesno("Silme Onayı",
                                                 f"Emin misiniz?\n\n'{urun_adi}' (Barkod: {barkod}) ürünü kalıcı olarak silinecektir.")
        if emin_misin:
            if urun_sil_db(barkod):
                self.urun_tablosu.delete(secili_id)
                tkinter.messagebox.showinfo("Başarılı", f"'{urun_adi}' ürünü başarıyla silindi.")
            else:
                tkinter.messagebox.showerror("Hata", "Ürün silinirken bir veritabanı hatası oluştu.")

    def duzenle_hucre(self, event):
        # Eğer zaten bir düzenleme kutusu aktifse, önce onu bitir
        if self.duzenleme_entry:
            self.iptal_duzenleme()

        # Tıklanan satırı ve sütunu bul
        row_id = self.urun_tablosu.identify_row(event.y)
        col_id = self.urun_tablosu.identify_column(event.x)

        if not row_id or col_id == '#1':  # Barkod sütununu düzenlemeye izin verme
            return

        # Hücrenin boyutlarını ve konumunu al
        x, y, width, height = self.urun_tablosu.bbox(row_id, col_id)

        # Hücrenin mevcut değerini al
        mevcut_deger = self.urun_tablosu.set(row_id, col_id)

        # --- HATA DÜZELTİLDİ ---
        # Genişlik ve yüksekliği, widget'ı oluştururken (constructor) veriyoruz.
        self.duzenleme_entry = ctk.CTkEntry(self.urun_tablosu.master,
                                            width=width,
                                            height=height,
                                            border_width=0,  # Kenar boşluğunu sıfırla
                                            corner_radius=0)  # Köşeleri sivri yap

        # `place` metodunda artık width ve height YOK.
        self.duzenleme_entry.place(x=x, y=y)
        # --- DÜZELTME BİTİYOR ---

        self.duzenleme_entry.insert(0, mevcut_deger)
        self.duzenleme_entry.select_range(0, tk.END)
        self.duzenleme_entry.focus_set()

        # Sütun kimliğinden ('#2', '#3' vb.) sayısal indeksi al (0'dan başlayan)
        column_index = int(col_id.replace('#', '')) - 1

        # Düzenlenen hücre bilgilerini sakla
        self.duzenlenen_hucre = (row_id, col_id, column_index)

        # Olayları bağla
        self.duzenleme_entry.bind("<Return>", self.kaydet_duzenleme)
        self.duzenleme_entry.bind("<FocusOut>", self.iptal_duzenleme)
        self.duzenleme_entry.bind("<Escape>", self.iptal_duzenleme)

    def kaydet_duzenleme(self, event):
        if not self.duzenlenen_hucre: return

        row_id, col_id, column_index = self.duzenlenen_hucre
        sutun_adi = self.sutunlar[column_index]
        yeni_deger = self.duzenleme_entry.get()
        barkod = self.urun_tablosu.set(row_id, '#1')

        guncelleme_basarili = False
        try:
            if sutun_adi == "Ürün Adı":
                if yeni_deger:
                    guncelleme_basarili = urun_guncelle_db(barkod, urun_adi=yeni_deger)
            elif sutun_adi == "Fiyat (TL)":
                temiz_deger = float(yeni_deger.replace("TL", "").strip())
                guncelleme_basarili = urun_guncelle_db(barkod, fiyat=temiz_deger)
                yeni_deger = f"{temiz_deger:.2f}"
            elif sutun_adi == "Stok":
                guncelleme_basarili = urun_guncelle_db(barkod, stok=int(yeni_deger))
        except ValueError:
            tkinter.messagebox.showerror("Hata", f"'{sutun_adi}' için geçersiz değer girdiniz: {yeni_deger}")
            self.iptal_duzenleme()
            return

        if guncelleme_basarili:
            self.urun_tablosu.set(row_id, col_id, yeni_deger)
            print(f"'{barkod}' barkodlu ürün güncellendi: {sutun_adi} -> {yeni_deger}")
        else:
            print("Veritabanı güncellemesi başarısız oldu veya değişiklik yapılmadı.")

        self.iptal_duzenleme()  # Her durumda düzenleme modunu bitir

    def iptal_duzenleme(self, event=None):
        if self.duzenleme_entry:
            self.duzenleme_entry.destroy()
            self.duzenleme_entry = None
            self.duzenlenen_hucre = None


    def generic_treeview_sort(self, tree, col, columns_list, numeric_columns):
        """Herhangi bir Treeview'ı, tıklanan sütuna göre sıralayan genel fonksiyon."""

        # 1. Bu Treeview'a özel sıralama durumunu al veya oluştur
        tree_id = str(tree)
        if tree_id not in self.sort_states:
            self.sort_states[tree_id] = {'col': None, 'reverse': False}
        state = self.sort_states[tree_id]

        # 2. Tablodaki veriyi al
        data = [(tree.set(k, col), k) for k in tree.get_children('')]

        # 3. Sıralama yönünü belirle
        if col == state['col']:
            state['reverse'] = not state['reverse']
        else:
            state['col'] = col
            state['reverse'] = False

        # 4. Veriyi sırala (sayısal veya metinsel)
        if col in numeric_columns:
            def convert_to_float(value):
                try:
                    # "12.34 TL" gibi ifadeleri temizleyip sayıya çevir
                    return float(str(value).replace("TL", "").strip())
                except (ValueError, TypeError):
                    return 0.0

            data.sort(key=lambda item: convert_to_float(item[0]), reverse=state['reverse'])
        else:
            data.sort(key=lambda item: str(item[0]).lower(), reverse=state['reverse'])

        # 5. Öğeleri sıralanmış sıraya göre yeniden taşı
        for index, (val, k) in enumerate(data):
            tree.move(k, '', index)

        # 6. Başlıkları güncelleyerek sıralama yönünü göster
        for c in columns_list:
            if c == col:
                arrow = ' ▼' if state['reverse'] else ' ▲'
                tree.heading(c, text=c + arrow)
            else:
                tree.heading(c, text=c)

    def process_save_as_debt(self):
        if not self.sepet:
            tkinter.messagebox.showerror("Hata", "Sepet boşken kaydedilemez")
            return

        for barkod, detaylar in self.sepet.items():
            urun_db = urun_bilgisi_getir_db(barkod)
            if not urun_db or urun_db[3] < detaylar['adet']:
                tkinter.messagebox.showerror("Stok Hatası", f"'{detaylar['isim']}' için stok yetersiz!")
                return

        toplam_fiyat = sum(item['fiyat'] * item['adet'] for item in self.sepet.values())

        #### call back fonksiyonu
        def borc_kaydi_basarili():
            print("Borç Kaydı Başarılı. Satış Ekranı Temizleniyor")
            self.sepet.clear()
            self.sepeti_yenile()
            self.ent_barkod.focus_set()

        BorcluSecimPenceresi(parent=self.master,sepet=self.sepet,toplam_tutar=toplam_fiyat,on_success_callback=borc_kaydi_basarili)

    def view_debts_interface(self):
        """Yeni Borç Defteri penceresini açar."""
        BorcDefteriPenceresi(parent=self.master)




