import tkinter as tk
from tkinter import messagebox

# -----------------------------
# Fungsi untuk menghitung kecepatan
# -----------------------------
def hitung_kecepatan():
    try:
        nama = entry_nama.get()
        jarak = float(entry_jarak.get())
        waktu = float(entry_waktu.get())

        if waktu == 0:
            messagebox.showerror("Error", "Waktu tidak boleh 0!")
            return
        
        kecepatan = jarak / waktu
        hasil_label.config(text=f"Halo {nama}, kecepatan motormu adalah: {kecepatan:.2f} km/jam")

    except ValueError:
        messagebox.showerror("Error", "Pastikan jarak dan waktu berupa angka!")

# -----------------------------
# GUI Design
# -----------------------------

window = tk.Tk()
window.title("Cek Seberapa Cepat Motor Kamu")
window.geometry("450x350")
window.configure(bg="#2b2d42")   # Warna background dark-blue

# Judul
judul = tk.Label(window, text="Cek Seberapa Cepat Motor Kamu",
                 font=("Helvetica", 16, "bold"),
                 bg="#2b2d42", fg="#edf2f4")
judul.pack(pady=15)

# Frame form
frame = tk.Frame(window, bg="#2b2d42")
frame.pack(pady=5)

# Input nama
tk.Label(frame, text="Nama:", bg="#2b2d42", fg="white",
         font=("Arial", 12)).grid(row=0, column=0, sticky="w", pady=5)
entry_nama = tk.Entry(frame, width=25, font=("Arial", 12))
entry_nama.grid(row=0, column=1, pady=5)

# Input jarak
tk.Label(frame, text="Jarak (km):", bg="#2b2d42", fg="white",
         font=("Arial", 12)).grid(row=1, column=0, sticky="w", pady=5)
entry_jarak = tk.Entry(frame, width=25, font=("Arial", 12))
entry_jarak.grid(row=1, column=1, pady=5)

# Input waktu
tk.Label(frame, text="Waktu (jam):", bg="#2b2d42", fg="white",
         font=("Arial", 12)).grid(row=2, column=0, sticky="w", pady=5)
entry_waktu = tk.Entry(frame, width=25, font=("Arial", 12))
entry_waktu.grid(row=2, column=1, pady=5)

# Tombol hitung
tombol = tk.Button(window, text="Hitung Kecepatan",
                   font=("Arial", 12, "bold"),
                   bg="#8d99ae", fg="white", width=20,
                   command=hitung_kecepatan)
tombol.pack(pady=15)

# Label hasil
hasil_label = tk.Label(window,
                       text="Hasil akan muncul di sini",
                       font=("Arial", 12),
                       bg="#2b2d42", fg="#ef233c")
hasil_label.pack(pady=10)

# Jalankan window
window.mainloop()
