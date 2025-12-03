import tkinter as tk
from tkinter import messagebox, ttk

class AplikasiKantin:
    def __init__(self, root):
        self.root = root
        self.root.title("Kantin Kelompok 20")
        self.root.geometry("350x450")
        self.root.resizable(False, False)

        # --- 1. Judul / Header (Label) ---
        self.label_judul = tk.Label(root, text="Menu Kantin Mahasiswa", font=("Arial", 14, "bold"))
        self.label_judul.pack(pady=10)

        # --- 2. Input Nama (Entry) ---
        self.frame_nama = tk.Frame(root) 
        self.frame_nama.pack(pady=5)
        
        tk.Label(self.frame_nama, text="Nama Pemesan:").pack(side="left")
        self.entry_nama = tk.Entry(self.frame_nama)
        self.entry_nama.pack(side="left", padx=5)

        # --- 3. Pilihan Makanan (Combobox) ---
        tk.Label(root, text="Pilih Makanan:").pack(pady=(10,0))
        
        self.menu_options = ["Nasi Goreng (Rp 15.000)", "Mie Ayam (Rp 12.000)", "Soto Ayam (Rp 18.000)"]
        self.combo_menu = ttk.Combobox(root, values=self.menu_options, state="readonly")
        self.combo_menu.current(0)
        self.combo_menu.pack(pady=5)

        # --- 4. Jenis Pesanan (Radiobutton) ---
        tk.Label(root, text="Jenis Pesanan:").pack(pady=(10,0))
        
        self.jenis_var = tk.StringVar(value="Dine In")
        
        self.frame_radio = tk.Frame(root)
        self.frame_radio.pack()
        
        tk.Radiobutton(self.frame_radio, text="Dine In", variable=self.jenis_var, value="Dine In").pack(side="left", padx=10)
        tk.Radiobutton(self.frame_radio, text="Take Away", variable=self.jenis_var, value="Take Away").pack(side="left", padx=10)

        # --- 5. Tambahan (Checkbutton) ---
        tk.Label(root, text="Tambahan (Rp 3.000):").pack(pady=(10,0))
        
        self.cek_es = tk.IntVar()
        self.cek_nasi = tk.IntVar()

        tk.Checkbutton(root, text="Tambah Es Teh", variable=self.cek_es).pack()
        tk.Checkbutton(root, text="Tambah Nasi Putih", variable=self.cek_nasi).pack()

        # --- 6. Tombol Aksi (Button) ---
        self.btn_pesan = tk.Button(root, text="Hitung & Pesan", command=self.proses_pesanan, bg="lightblue", width=20)
        self.btn_pesan.pack(pady=20)

    def proses_pesanan(self):
        nama = self.entry_nama.get()
        menu_terpilih = self.combo_menu.get()
        jenis = self.jenis_var.get()
        
        # Validasi Nama tidak boleh kosong
        if nama == "":
            messagebox.showwarning("Peringatan", "Nama pemesan wajib diisi!")
            return

        total_harga = 0
        
        if "Nasi Goreng" in menu_terpilih:
            total_harga += 15000
        elif "Mie Ayam" in menu_terpilih:
            total_harga += 12000
        elif "Soto Ayam" in menu_terpilih:
            total_harga += 18000

        if self.cek_es.get() == 1:
            total_harga += 3000
        if self.cek_nasi.get() == 1:
            total_harga += 3000

        # Tampilkan Output (Messagebox)
        detail_struk = f"Pemesan: {nama}\nMenu: {menu_terpilih}\nJenis: {jenis}\n\nTotal Bayar: Rp {total_harga}"
        messagebox.showinfo("Struk Pesanan", detail_struk)

if __name__ == "__main__":
    root = tk.Tk()
    app = AplikasiKantin(root)
root.mainloop()
