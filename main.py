import customtkinter as ctk
from GUI import KantinArayuzu
from database_operations import tablo_olustur

if __name__ == "__main__":
    tablo_olustur()
    root = ctk.CTk()
    root.geometry("800x600")
    # --- YENİ EKLENEN TAM EKRAN KODU ---

    # Tam ekran durumunu takip etmek için bir değişken
    arayuz = KantinArayuzu(root)
    root.mainloop()