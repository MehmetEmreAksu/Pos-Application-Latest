import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import json

from debt_operations import (
    tum_borclulari_getir_db,
    borclu_ekle_db,
    borc_kaydet_db
)


from database_operations import urun_guncelle_db, urun_bilgisi_getir_db
from debt_operations import borc_ode_db,borc_sil_db



class BorcluSecimPenceresi(ctk.CTkToplevel):
    def __init__(self, parent, sepet, toplam_tutar, on_success_callback):
        super().__init__(parent)
        self.title("Borçlu Seç")
        self.geometry("400x250")
        self.resizable(False, False)

        # Bu pencere kapanana kadar ana pencereye odaklanmayı engelle
        self.grab_set()
        # Pencereyi ana pencerenin ortasında başlat
        self.after(10, self._center_window)

        # Gelen verileri saklayalım
        self.sepet = sepet
        self.toplam_tutar = toplam_tutar
        self.on_success_callback = on_success_callback # Başarılı olunca çağrılacak fonksiyon

        # Borçluları saklamak için bir sözlük (dictionary)
        # İsme göre ID'yi kolayca bulmamızı sağlayacak
        self.borclular_dict = {}

        self.setup_ui()
        self.borclulari_yukle()

    def _center_window(self):
        """Pencereyi ana pencerenin ortasında konumlandırır."""
        try:
            parent_geo = self.master.geometry().split('+')
            parent_width = int(parent_geo[0].split('x')[0])
            parent_height = int(parent_geo[0].split('x')[1])
            parent_x = int(parent_geo[1])
            parent_y = int(parent_geo[2])

            win_width = int(self.winfo_width())
            win_height = int(self.winfo_height())

            x = parent_x + (parent_width // 2) - (win_width // 2)
            y = parent_y + (parent_height // 2) - (win_height // 2)

            self.geometry(f"{win_width}x{win_height}+{x}+{y}")
        except Exception:
            # Hata olursa varsayılan konumu kullan
            pass
        self.lift()  # Pencereyi en üste getir

    def setup_ui(self):
        """Arayüz elemanlarını oluşturur ve yerleştirir."""
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(padx=20, pady=20, fill="both", expand=True)

        ctk.CTkLabel(main_frame, text="Kime borç yazılsın?", font=("Arial", 16)).pack(pady=(0, 10))

        # Mevcut borçlular için ComboBox (açılır liste)
        self.combo_borclular = ctk.CTkComboBox(main_frame, state="readonly", height=35)
        self.combo_borclular.pack(fill="x")

        # Yeni borçlu ekleme bölümü
        yeni_borclu_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        yeni_borclu_frame.pack(fill="x", pady=(20, 5))

        self.ent_yeni_borclu = ctk.CTkEntry(yeni_borclu_frame, placeholder_text="Veya yeni kişi ekle...", height=35)
        self.ent_yeni_borclu.pack(side="left", fill="x", expand=True)

        self.btn_yeni_ekle = ctk.CTkButton(yeni_borclu_frame, text="Ekle", width=60, height=35, command=self.yeni_borclu_ekle)
        self.btn_yeni_ekle.pack(side="left", padx=(10, 0))

        # Onay ve İptal Butonları
        buton_frame = ctk.CTkFrame(self, fg_color="transparent")
        buton_frame.pack(pady=10, padx=20, fill="x")

        btn_onayla = ctk.CTkButton(buton_frame, text="Borcu Kaydet", height=40, command=self.borcu_kaydet)
        btn_onayla.pack(side="left", expand=True, padx=(0, 5))

        btn_iptal = ctk.CTkButton(buton_frame, text="İptal", height=40, fg_color="#D32F2F", hover_color="#B71C1C", command=self.destroy)
        btn_iptal.pack(side="right", expand=True, padx=(5, 0))

    def borclulari_yukle(self):
        self.borclular_dict.clear()
        borclular_listesi = tum_borclulari_getir_db()
        for borclu_id, isim in borclular_listesi:
            self.borclular_dict[isim] = borclu_id

        isimler = list(self.borclular_dict.keys())

        if not isimler:
            self.combo_borclular.set("Kayıtlı borçlu yok")
            self.combo_borclular.configure(values=[])
        else:
            self.combo_borclular.configure(values=isimler)
            self.combo_borclular.set(isimler[0])

    def yeni_borclu_ekle(self):
        yeni_isim= self.ent_yeni_borclu.get()
        if not yeni_isim:
            messagebox.showwarning("Uyarı", "Lütfen İsim Girin", parent=self)
            return

        basarili, sonuc = borclu_ekle_db(yeni_isim)
        if basarili:
            self.ent_yeni_borclu.delete(0, "end") # Giriş kutusunu temizle
            self.borclulari_yukle() # Listeyi yenile
            self.combo_borclular.set(yeni_isim) # Yeni ekleneni seçili yap
        else:
            messagebox.showerror("Hata", sonuc, parent=self) # sonuc hata mesajı

    def borcu_kaydet(self):
        secilen_isim = self.combo_borclular.get()
        if not secilen_isim or secilen_isim == "Kayıtlı borçlu yok":
            messagebox.showerror("Hata", "Lütfen bir borçlu seçin.", parent=self)
            return

        secilen_borclu_id = self.borclular_dict.get(secilen_isim)
        if not secilen_borclu_id:
            messagebox.showerror("Hata", "Geçersiz borçlu seçimi.", parent=self)
            return

        for barkod, detaylar in self.sepet.items():
            urun_db = urun_bilgisi_getir_db(barkod)
            yeni_stok = urun_db[3] - detaylar["adet"]
            urun_guncelle_db(barkod,stok=yeni_stok)

        if borc_kaydet_db(secilen_borclu_id, self.sepet,self.toplam_tutar):
            self.on_success_callback()
            self.destroy()
        else:
            messagebox.showerror("Veritabanı Hatası","Borç Kaydedilirken Hata Oluştu",parent=self)


class BorcDefteriPenceresi(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Borç Defteri")
        self.geometry("1000x700")
        self.minsize(800, 600)

        self.after(50, self.en_uste_getir)

        self.sort_states = {}

        # Seçili olan borçlu ve borç işleminin ID'lerini tutmak için
        self.secili_borclu_id = None
        self.secili_islem_id = None

        # --- Arayüz Elemanları ---
        self.lbl_toplam_borc = None
        self.setup_ui()
        self.borclulari_listele() # Pencere açılır açılmaz borçluları yükle

    def en_uste_getir(self):
        """Pencereyi en üste getirir ve ona odaklanır."""
        self.lift() # Pencereyi diğer pencerelerin üzerine çıkarır.
        self.focus_force() # Pencereye zorla odaklanır.

    def setup_ui(self):
        """Pencerenin ana arayüzünü oluşturur."""
        # --- Ana Çerçeve (Sol ve Sağ olarak ikiye ayrılacak) ---
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        main_frame.grid_columnconfigure(1, weight=3)  # Sağ taraf daha geniş olsun
        main_frame.grid_rowconfigure(0, weight=1)

        # --- SOL TARAF: Borçlu Listesi ---
        sol_frame = ctk.CTkFrame(main_frame)
        sol_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        sol_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(sol_frame, text="Borçlular", font=("Arial", 16, "bold")).grid(row=0, column=0, pady=10, padx=10)

        # Borçluları Treeview'da gösterelim, daha profesyonel durur.
        self.borclular_tree = ttk.Treeview(sol_frame, columns=("İsim",), show="headings", selectmode="browse")
        self.borclular_tree.heading("İsim", text="İsim")
        self.borclular_tree.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.borclular_tree.bind("<<TreeviewSelect>>", self.borclu_secildi)

        self.borclular_cols = ("İsim",)
        self.borclular_numeric_cols = ()  # Sayısal sütun yok
        self.borclular_tree.heading("İsim", text="isim", command=lambda :self.generic_treeview_sort(self.borclular_tree, "İsim", self.borclular_cols, self.borclular_numeric_cols))

        # --- SAĞ TARAF: Borç Detayları ---
        sag_frame = ctk.CTkFrame(main_frame)
        sag_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        sag_frame.grid_rowconfigure(2, weight=2)  # İşlem detayları daha fazla yer kaplasın
        sag_frame.grid_rowconfigure(4, weight=1)
        sag_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(sag_frame, text="Seçili Kişinin Borç İşlemleri", font=("Arial", 16, "bold")).grid(row=0, column=0,pady=10, padx=10)

        toplam_borc_frame = ctk.CTkFrame(sag_frame, fg_color="transparent")
        toplam_borc_frame.grid(row=1, column=0, pady=(0, 10), padx=10, sticky="ew")
        toplam_borc_frame.grid_columnconfigure(0, weight=1)  # Etiket genişlesin

        self.lbl_toplam_borc = ctk.CTkLabel(toplam_borc_frame, text="Toplam Borç: 0.00 TL", font=("Arial", 14, "bold"),text_color="#E57373")
        self.lbl_toplam_borc.grid(row=0, column=0, sticky="w")

        self.btn_tumunu_ode = ctk.CTkButton(toplam_borc_frame, text="TÜM BORCU ÖDE", height=30, fg_color="#FF9800", hover_color="#F57C00", font=("Arial", 12, "bold"), command=self.tum_borclari_ode, state="disabled")
        self.btn_tumunu_ode.grid(row=0, column=1, sticky="e")


        self.lbl_toplam_borc = ctk.CTkLabel(sag_frame, text="Toplam Borç: 0.00 TL", font=("Arial", 14, "bold"),
                                            text_color="#E57373")
        self.lbl_toplam_borc.grid(row=1, column=0, pady=(0, 10), padx=10, sticky="w")

        self.islem_tree = ttk.Treeview(sag_frame, columns=("Tür", "Tarih", "Tutar"), show="headings", selectmode="extended")
        self.islem_tree.heading("Tür", text="Tür")
        self.islem_tree.heading("Tarih", text="Tarih")
        self.islem_tree.heading("Tutar", text="Toplam Tutar (TL)")

        self.islem_tree.column("Tür", width=80, anchor="center")
        self.islem_tree.column("Tarih", width=100)
        self.islem_tree.column("Tutar", anchor="e")

        self.islem_tree.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.islem_tree.bind("<<TreeviewSelect>>", self.islem_secildi)


        ### DİNAMİK BİR ŞEKİLDE SIRALAMAK İÇİN
        self.islem_cols = ("Tür", "Tarih", "Tutar")
        self.islem_numeric_cols = ("Tutar",)  # Tutar sayısal bir sütun
        self.islem_tree.heading("Tür", text="Tür",command=lambda: self.generic_treeview_sort(self.islem_tree, "Tür", self.islem_cols,self.islem_numeric_cols))
        self.islem_tree.heading("Tarih", text="Tarih",command=lambda: self.generic_treeview_sort(self.islem_tree, "Tarih", self.islem_cols,self.islem_numeric_cols))
        self.islem_tree.heading("Tutar", text="Toplam Tutar (TL)",command=lambda: self.generic_treeview_sort(self.islem_tree, "Tutar", self.islem_cols,self.islem_numeric_cols))

        ctk.CTkLabel(sag_frame, text="İşlem Detayları (Sepet İçeriği)", font=("Arial", 16, "bold")).grid(row=3, column=0,pady=10,padx=10)

        self.detay_tree = ttk.Treeview(sag_frame, columns=("Ürün", "Adet", "Fiyat"), show="headings")
        self.detay_tree.heading("Ürün", text="Ürün Adı")
        self.detay_tree.heading("Adet", text="Adet")
        self.detay_tree.heading("Fiyat", text="Satış Fiyatı (TL)")
        self.detay_tree.column("Adet", width=60, anchor="center")
        self.detay_tree.column("Fiyat", width=120, anchor="e")
        self.detay_tree.grid(row=4, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # --- BUTONLAR ---
        buton_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buton_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=0, pady=(5, 0))
        buton_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.btn_manuel_ekle = ctk.CTkButton(buton_frame, text="Manuel Borç Ekle", height=40,fg_color="#00BCD4", hover_color="#00ACC1",command=self.manuel_borc_ekle)
        self.btn_manuel_ekle.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.btn_ode = ctk.CTkButton(buton_frame, text="Seçili Borcu Öde", height=40, fg_color="#4CAF50",hover_color="#45a049", state="disabled",command=self.borcu_ode)
        self.btn_ode.grid(row=0, column=1, padx=5, sticky="ew")

        self.btn_sil = ctk.CTkButton(buton_frame, text="Seçili İşlemi Sil (İptal Et)", height=40, fg_color="#D32F2F", hover_color="#B71C1C", state="disabled",command=self.borcu_sil)
        self.btn_sil.grid(row=0, column=2, padx=(5, 0), sticky="ew")

        # --- STİL AYARLARI ---
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2a2d2e", foreground="white", fieldbackground="#343638", borderwidth=0,
                        rowheight=25)
        style.map('Treeview', background=[('selected', '#22559b')])
        style.configure("Treeview.Heading", background="#565b5e", foreground="white", relief="flat",
                        font=('Calibri', 10, 'bold'))
        style.map("Treeview.Heading", background=[('active', '#3484F0')])

    def borclulari_listele(self):
        """Sol taraftaki borçlular listesini doldurur."""
        # Önce tüm tabloları temizle
        for i in self.borclular_tree.get_children(): self.borclular_tree.delete(i)
        for i in self.islem_tree.get_children(): self.islem_tree.delete(i)
        for i in self.detay_tree.get_children(): self.detay_tree.delete(i)

        # Butonları pasif yap
        self.btn_ode.configure(state="disabled")
        self.btn_sil.configure(state="disabled")

        borclular = tum_borclulari_getir_db()
        # Gelen veri: [(id1, isim1), (id2, isim2), ...]
        for borclu_id, isim in borclular:
            # Treeview'a eklerken ID'yi `iid` olarak saklıyoruz.
            # Bu, daha sonra isme tıklandığında ID'yi kolayca almamızı sağlar.
            self.borclular_tree.insert("", "end", iid=borclu_id, values=(isim,))

    def borclu_secildi(self, event=None):
        """Soldaki listeden bir borçlu seçildiğinde tetiklenir."""
        # Önce sağdaki listeleri temizle
        for i in self.islem_tree.get_children(): self.islem_tree.delete(i)
        for i in self.detay_tree.get_children(): self.detay_tree.delete(i)
        self.btn_ode.configure(state="disabled")
        self.btn_sil.configure(state="disabled")

        selected_items = self.borclular_tree.selection()
        if not selected_items:
            self.secili_borclu_id = None
            self.btn_tumunu_ode.configure(state="disabled")  # Seçim yoksa butonu pasif yap
            self.lbl_toplam_borc.configure(text="Toplam Borç: 0.00 TL")
            return

        self.btn_tumunu_ode.configure(state="normal")

        self.secili_borclu_id = selected_items[0]  # `iid` olarak sakladığımız ID'yi aldık

        from debt_operations import borclunun_toplam_borcunu_getir_db
        toplam_borc = borclunun_toplam_borcunu_getir_db(self.secili_borclu_id)
        self.lbl_toplam_borc.configure(text=f"Toplam Borç: {toplam_borc:.2f} TL")

        # debt_operations'daki yeni fonksiyonumuzu çağırıyoruz
        from debt_operations import borclunun_borclarini_getir_db
        borc_islemleri = borclunun_borclarini_getir_db(self.secili_borclu_id)

        # Gelen veri: [(id, tarih, tutar), ...]
        for islem_id, tarih, tutar, sepet_json in borc_islemleri:
            try:
                sepet = json.loads(sepet_json)
                # Borcun türünü belirle
                tur = "Manuel" if sepet.get("manuel_borc") else "Satış"
            except json.JSONDecodeError:
                tur = "Bilinmiyor"
            self.islem_tree.insert("", "end", iid=islem_id, values=(tur, tarih, f"{tutar:.2f}"))

    def islem_secildi(self, event=None):
        """Sağ üstteki borç işlemleri listesinden bir işlem seçildiğinde tetiklenir."""
        # Önce detay tablosunu temizle
        for i in self.detay_tree.get_children(): self.detay_tree.delete(i)

        selected_items = self.islem_tree.selection()
        if not selected_items:
            self.secili_islem_id = None
            self.btn_ode.configure(state="disabled")
            self.btn_sil.configure(state="disabled")
            return

        self.secili_islem_id = selected_items[0]
        self.btn_ode.configure(state="normal")
        self.btn_sil.configure(state="normal")

        from debt_operations import borc_detayini_getir_db
        sepet_json = borc_detayini_getir_db(self.secili_islem_id)

        if not sepet_json:
            return

        try:
            sepet = json.loads(sepet_json)

            # --- YENİ VE AKILLI KONTROL ---
            # Bu bir manuel borç mu?
            if sepet.get("manuel_borc"):
                # Evet, manuel borç. Detay tablosunu açıklama için kullanalım.
                aciklama = sepet.get("aciklama", "Açıklama yok")

                # Sütun başlıklarını geçici olarak değiştir
                self.detay_tree.heading("Ürün", text="Açıklama")
                self.detay_tree.heading("Adet", text="")  # Boş başlık
                self.detay_tree.heading("Fiyat", text="")  # Boş başlık

                # Tek bir satır olarak açıklamayı ekle
                self.detay_tree.insert("", "end", values=(aciklama, "", ""))
            else:
                # Hayır, bu normal bir satış borcu.
                # Sütun başlıklarını orijinal haline getir
                self.detay_tree.heading("Ürün", text="Ürün Adı")
                self.detay_tree.heading("Adet", text="Adet")
                self.detay_tree.heading("Fiyat", text="Satış Fiyatı (TL)")

                # Sepet içeriğini listele
                for barkod, detay in sepet.items():
                    self.detay_tree.insert("", "end", values=(detay['isim'], detay['adet'], f"{detay['fiyat']:.2f}"))
            # --- KONTROL BİTTİ ---

        except (json.JSONDecodeError, TypeError):
            # Hatalı veya beklenmedik bir JSON formatı varsa
            self.detay_tree.insert("", "end", values=("Veri okunamadı.", "", ""))

    def borcu_ode(self):
        # 1. Adım: Seçili olan TÜM öğeleri al.
        secili_ogeler = self.islem_tree.selection()

        if not secili_ogeler:
            messagebox.showwarning("Uyarı", "Lütfen ödemek için bir veya daha fazla borç işlemi seçin.", parent=self)
            return

        # 'secili_ogeler' bir demet ('1', '3', '5') şeklindedir.
        # Bu ID listesini veritabanı fonksiyonuna göndereceğiz.
        borc_id_listesi = list(secili_ogeler)

        # 3. Adım: YENİ veritabanı fonksiyonunu çağır.
        from debt_operations import toplu_borc_ode_db
        basarili, odenen_sayi = toplu_borc_ode_db(borc_id_listesi)

        if basarili:
            # Arayüzü yenile
            self.borclu_secildi()
        else:
            messagebox.showerror("Hata", "Borçlar ödenirken bir veritabanı hatası oluştu.", parent=self)

    def borcu_sil(self):
        # 1. Adım: O AN seçili olan bir öğe var mı diye KONTROL ET.
        secili_ogeler = self.islem_tree.selection()

        # Eğer seçili bir şey yoksa, uyarı ver ve fonksiyonu bitir.
        if not secili_ogeler:
            messagebox.showwarning("Uyarı", "Lütfen silmek için bir borç işlemi seçin.", parent=self)
            return

        # 2. Adım: ID'yi DOĞRUDAN o an seçili olan öğeden al.
        secili_islem_id = secili_ogeler[0]

        # 3. Adım: Veritabanı işlemini yap.
        if borc_sil_db(secili_islem_id):
            # 4. Adım: Listeyi yenile.
            self.borclu_secildi()
        else:
            messagebox.showerror("Hata", "İşlem silinirken bir veritabanı hatası oluştu.", parent=self)

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

    def tum_borclari_ode(self):
        # 1. Adım: Seçili bir borçlu olduğundan emin ol
        if not self.secili_borclu_id:
            messagebox.showwarning("Uyarı", "Lütfen önce bir borçlu seçin.", parent=self)
            return

        # 2. Adım: Seçili borçlunun TÜM borç işlemlerinin ID'lerini topla
        # Bunun için 'islem_tree' widget'ındaki mevcut tüm ID'leri almamız yeterli.
        tum_borc_idler = self.islem_tree.get_children()

        if not tum_borc_idler:
            messagebox.showinfo("Bilgi", "Seçili kişinin ödenecek borcu bulunmamaktadır.", parent=self)
            return

        borclu_isim = self.borclular_tree.item(self.secili_borclu_id, 'values')[0]
        toplam_borc_str = self.lbl_toplam_borc.cget("text")  # Etiketteki metni al

        # 3. Adım: Onay mesajı
        emin_misin = messagebox.askyesno(
            "Tüm Hesabı Kapatma Onayı",
            f"'{borclu_isim}' adlı kişinin {toplam_borc_str.lower()} tutarındaki TÜM borcunu ödemek istediğinizden emin misiniz?",
            parent=self
        )

        if not emin_misin:
            return

        # 4. Adım: Zaten var olan toplu ödeme fonksiyonumuzu çağır
        from debt_operations import toplu_borc_ode_db
        basarili, odenen_sayi = toplu_borc_ode_db(list(tum_borc_idler))

        if basarili:
            messagebox.showinfo("Başarılı", f"{odenen_sayi} adet borç işlemi ödendi ve hesap kapatıldı.", parent=self)
            # Arayüzü yenile
            self.borclu_secildi()
        else:
            messagebox.showerror("Hata", "Tüm borçlar ödenirken bir hata oluştu.", parent=self)

    def manuel_borc_ekle(self):
        """
        Manuel borç ekleme penceresini açar.
        """
        # Yeni penceremize, işlem başarılı olduğunda ana listeyi
        # yenilemesi için 'self.borclulari_listele' fonksiyonunu gönderiyoruz.
        ManuelBorcEklemePenceresi(parent=self, on_success_callback=self.borclulari_listele)




class ManuelBorcEklemePenceresi(ctk.CTkToplevel):
    def __init__(self, parent, on_success_callback):
        super().__init__(parent)
        self.title("Manuel Borç Ekle")
        self.geometry("450x300")

        self.on_success = on_success_callback  # Başarılı olunca ana ekranı yenileyecek fonksiyon
        self.borclular_dict = {}

        self.setup_ui()
        self.borclulari_yukle()

        self.after(100, self.combo_borclular.focus_set)

    def setup_ui(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(padx=20, pady=20, fill="both", expand=True)
        main_frame.grid_columnconfigure(1, weight=1)

        # --- Borçlu Seçim Bölümü ---
        ctk.CTkLabel(main_frame, text="Kişi Seç:", font=("Arial", 14)).grid(row=0, column=0, padx=(0, 10), pady=5,
                                                                            sticky="w")
        self.combo_borclular = ctk.CTkComboBox(main_frame, state="readonly", height=35)
        self.combo_borclular.grid(row=0, column=1, sticky="ew")

        # --- Yeni Borçlu Ekleme Bölümü ---
        ctk.CTkLabel(main_frame, text="Yeni Kişi:", font=("Arial", 14)).grid(row=1, column=0, padx=(0, 10), pady=5,
                                                                             sticky="w")
        yeni_borclu_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        yeni_borclu_frame.grid(row=1, column=1, sticky="ew")

        self.ent_yeni_borclu = ctk.CTkEntry(yeni_borclu_frame, placeholder_text="Veya yeni kişi ekle...", height=35)
        self.ent_yeni_borclu.pack(side="left", fill="x", expand=True)
        btn_yeni_ekle = ctk.CTkButton(yeni_borclu_frame, text="Ekle", width=60, height=35,
                                      command=self.yeni_borclu_ekle)
        btn_yeni_ekle.pack(side="left", padx=(10, 0))

        # --- Tutar Giriş Bölümü ---
        ctk.CTkLabel(main_frame, text="Tutar (TL):", font=("Arial", 14, "bold")).grid(row=2, column=0, padx=(0, 10),
                                                                                      pady=(20, 5), sticky="w")
        self.ent_tutar = ctk.CTkEntry(main_frame, placeholder_text="Örn: 10 veya 12.5", height=35, font=("Arial", 14))
        self.ent_tutar.grid(row=2, column=1, sticky="ew")

        # --- Açıklama Giriş Bölümü ---
        ctk.CTkLabel(main_frame, text="Açıklama:", font=("Arial", 14)).grid(row=3, column=0, padx=(0, 10), pady=5,
                                                                            sticky="w")
        self.ent_aciklama = ctk.CTkEntry(main_frame, placeholder_text="İsteğe bağlı (örn: Su parası)", height=35)
        self.ent_aciklama.grid(row=3, column=1, sticky="ew")

        # --- Onay Butonu ---
        btn_kaydet = ctk.CTkButton(self, text="Borcu Kaydet", height=40, command=self.borcu_kaydet)
        btn_kaydet.pack(pady=10, padx=20, fill="x")
        self.bind("<Return>", lambda event: self.borcu_kaydet())

    def borclulari_yukle(self):
        self.borclular_dict.clear()
        borclular_listesi = tum_borclulari_getir_db()
        for borclu_id, isim in borclular_listesi:
            self.borclular_dict[isim] = borclu_id

        isimler = list(self.borclular_dict.keys())
        if not isimler:
            self.combo_borclular.set("Kayıtlı borçlu yok")
            self.combo_borclular.configure(values=[])
        else:
            self.combo_borclular.configure(values=isimler)
            self.combo_borclular.set(isimler[0])

    def yeni_borclu_ekle(self):
        yeni_isim = self.ent_yeni_borclu.get().strip()
        if not yeni_isim:
            messagebox.showwarning("Uyarı", "Lütfen eklenecek kişinin ismini girin.", parent=self)
            return

        basarili, sonuc = borclu_ekle_db(yeni_isim)
        if basarili:
            messagebox.showinfo("Başarılı", f"'{yeni_isim}' başarıyla eklendi.", parent=self)
            self.ent_yeni_borclu.delete(0, "end")
            self.borclulari_yukle()
            self.combo_borclular.set(yeni_isim)
        else:
            messagebox.showerror("Hata", sonuc, parent=self)

    def borcu_kaydet(self):
        # 1. Borçlu ID'sini al
        secilen_isim = self.combo_borclular.get()
        if not secilen_isim or secilen_isim == "Kayıtlı borçlu yok":
            messagebox.showerror("Hata", "Lütfen bir borçlu seçin.", parent=self)
            return
        secili_borclu_id = self.borclular_dict.get(secilen_isim)

        # 2. Tutarı al ve doğrula
        girilen_tutar_str = self.ent_tutar.get()
        try:
            tutar = float(girilen_tutar_str.replace(',', '.'))
            if tutar <= 0:
                raise ValueError("Tutar pozitif olmalı")
        except (ValueError, TypeError):
            messagebox.showerror("Geçersiz Giriş", "Lütfen geçerli bir sayısal tutar girin.", parent=self)
            return

        # 3. Açıklamayı al
        aciklama = self.ent_aciklama.get().strip()
        if not aciklama:
            aciklama = "Manuel olarak eklendi"

        # 4. Veritabanına kaydet
        from debt_operations import manuel_borc_ekle_db
        if manuel_borc_ekle_db(secili_borclu_id, tutar, aciklama):
            self.ent_tutar.configure(border_color="green")

            self.ent_tutar.delete(0, "end")
            self.ent_aciklama.delete(0, "end")

            self.on_success()  # Ana penceredeki yenileme fonksiyonunu çağır
        else:
            messagebox.showerror("Hata", "Borç eklenirken bir veritabanı hatası oluştu.", parent=self)


