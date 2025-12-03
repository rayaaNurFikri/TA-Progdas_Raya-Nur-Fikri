import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from collections import deque


# ==========================
#   CLASS BOOK
# ==========================
class Book:
    def __init__(self, title, author, year, status="Tersedia"):
        self.title = title
        self.author = author
        self.year = year
        self.status = status


# ==========================
#   MAIN APPLICATION CLASS
# ==========================
class LibraryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Perpustakaan Digital Modern")
        self.root.geometry("900x550")
        self.root.configure(bg="#f0f4ff")

        self.books = []
        self.loan_queue = deque()
        self.undo_stack = []

        self.load_database()
        self.setup_gui()
        self.refresh_tree()

    # ==========================
    #   GUI SETUP
    # ==========================
    def setup_gui(self):
        title_label = tk.Label(
            self.root, text="📚 PERPUSTAKAAN DIGITAL", 
            font=("Arial", 20, "bold"), bg="#f0f4ff"
        )
        title_label.pack(pady=10)

        frm = tk.Frame(self.root, bg="#f0f4ff")
        frm.pack(pady=5)

        tk.Label(frm, text="Judul:", bg="#f0f4ff").grid(row=0, column=0)
        tk.Label(frm, text="Penulis:", bg="#f0f4ff").grid(row=1, column=0)
        tk.Label(frm, text="Tahun:", bg="#f0f4ff").grid(row=2, column=0)

        self.entry_title = tk.Entry(frm, width=40)
        self.entry_author = tk.Entry(frm, width=40)
        self.entry_year = tk.Entry(frm, width=40)

        self.entry_title.grid(row=0, column=1, padx=5, pady=4)
        self.entry_author.grid(row=1, column=1, padx=5, pady=4)
        self.entry_year.grid(row=2, column=1, padx=5, pady=4)

        # BUTTON FRAME
        btn_frame = tk.Frame(self.root, bg="#f0f4ff")
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Tambah Buku", command=self.add_book).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Edit Buku", command=self.edit_book).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Hapus Buku", command=self.delete_book).grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="Pinjam Buku", command=self.request_loan).grid(row=0, column=3, padx=5)
        ttk.Button(btn_frame, text="Proses Antrian", command=self.process_queue).grid(row=0, column=4, padx=5)
        ttk.Button(btn_frame, text="Undo", command=self.undo_action).grid(row=0, column=5, padx=5)

        # SEARCH
        search_frame = tk.Frame(self.root, bg="#f0f4ff")
        search_frame.pack()

        tk.Label(search_frame, text="Cari Judul / Penulis:", bg="#f0f4ff").grid(row=0, column=0)
        self.entry_search = tk.Entry(search_frame, width=40)
        self.entry_search.grid(row=0, column=1, padx=5)
        ttk.Button(search_frame, text="Cari", command=self.search_book).grid(row=0, column=2)

        # TREEVIEW
        self.tree = ttk.Treeview(self.root, columns=("Judul", "Penulis", "Tahun", "Status"), show="headings")
        self.tree.heading("Judul", text="Judul")
        self.tree.heading("Penulis", text="Penulis")
        self.tree.heading("Tahun", text="Tahun")
        self.tree.heading("Status", text="Status")
        self.tree.pack(pady=10, fill="both", expand=True)

        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        ttk.Button(self.root, text="Export Daftar Buku", command=self.export_books).pack(pady=10)

    # ==========================
    #   TREEVIEW SELECTION
    # ==========================
    def on_tree_select(self, event):
        selected = self.get_selected_book_index()
        if selected is not None:
            book = self.books[selected]
            self.entry_title.delete(0, tk.END)
            self.entry_title.insert(0, book.title)
            self.entry_author.delete(0, tk.END)
            self.entry_author.insert(0, book.author)
            self.entry_year.delete(0, tk.END)
            self.entry_year.insert(0, book.year)

    # ==========================
    #   CRUD
    # ==========================
    def add_book(self):
        title = self.entry_title.get()
        author = self.entry_author.get()
        year = self.entry_year.get()

        if not title or not author or not year:
            messagebox.showwarning("Warning", "Semua data wajib diisi!")
            return

        new_book = Book(title, author, year)
        self.books.append(new_book)
        self.undo_stack.append(("delete", new_book))
        self.refresh_tree()
        self.save_database()

    def edit_book(self):
        idx = self.get_selected_book_index()
        if idx is None:
            return

        old_book = self.books[idx]
        backup = Book(old_book.title, old_book.author, old_book.year, old_book.status)
        self.undo_stack.append(("edit", idx, backup))

        old_book.title = self.entry_title.get()
        old_book.author = self.entry_author.get()
        old_book.year = self.entry_year.get()

        self.refresh_tree()
        self.save_database()

    def delete_book(self):
        idx = self.get_selected_book_index()
        if idx is None:
            return

        removed = self.books.pop(idx)
        self.undo_stack.append(("add", removed))
        self.refresh_tree()
        self.save_database()

    # ==========================
    #   SEARCH
    # ==========================
    def search_book(self):
        query = self.entry_search.get().lower()
        results = [b for b in self.books if query in b.title.lower() or query in b.author.lower()]

        self.tree.delete(*self.tree.get_children())

        for b in results:
            self.tree.insert("", tk.END, values=(b.title, b.author, b.year, b.status))

    # ==========================
    #   PEMINJAMAN (QUEUE)
    # ==========================
    def request_loan(self):
        idx = self.get_selected_book_index()
        if idx is None:
            return

        book = self.books[idx]

        if book.status == "Dipinjam":
            messagebox.showerror("Gagal", f"Buku '{book.title}' sedang dipinjam!")
            return

        self.loan_queue.append(book)
        messagebox.showinfo("Berhasil", f"Permintaan peminjaman untuk '{book.title}' masuk ke ANTRIAN.")

    def process_queue(self):
        if not self.loan_queue:
            messagebox.showinfo("Info", "Tidak ada permintaan peminjaman.")
            return

        book = self.loan_queue.popleft()
        book.status = "Dipinjam"

        self.undo_stack.append(("return", book))
        self.refresh_tree()
        self.save_database()

        messagebox.showinfo("Diproses", f"Buku '{book.title}' berhasil DIPINJAM.")

    # ==========================
    #   UNDO (STACK)
    # ==========================
    def undo_action(self):
        if not self.undo_stack:
            messagebox.showinfo("Info", "Tidak ada aksi untuk di-undo.")
            return

        action = self.undo_stack.pop()

        if action[0] == "delete":
            self.books.remove(action[1])
        elif action[0] == "add":
            self.books.append(action[1])
        elif action[0] == "edit":
            idx, backup = action[1], action[2]
            self.books[idx] = backup
        elif action[0] == "return":
            action[1].status = "Tersedia"

        self.refresh_tree()
        self.save_database()

    # ==========================
    #   HELPER FUNCTIONS
    # ==========================
    def get_selected_book_index(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Pilih buku dahulu!")
            return None

        item = self.tree.item(selected[0])
        title = item["values"][0]

        for i, b in enumerate(self.books):
            if b.title == title:
                return i
        return None

    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        for b in self.books:
            self.tree.insert("", tk.END, values=(b.title, b.author, b.year, b.status))

    # ==========================
    #   DATABASE
    # ==========================
    def save_database(self):
        data = [{"title": b.title, "author": b.author, "year": b.year, "status": b.status} for b in self.books]
        with open("library_db.json", "w") as f:
            json.dump(data, f, indent=4)

    def load_database(self):
        if not os.path.exists("library_db.json"):
            return

        with open("library_db.json", "r") as f:
            data = json.load(f)
            for b in data:
                self.books.append(Book(b["title"], b["author"], b["year"], b["status"]))

    def export_books(self):
        with open("export_buku.txt", "w") as f:
            for b in self.books:
                f.write(f"{b.title} - {b.author} - {b.year} - {b.status}\n")
        messagebox.showinfo("Berhasil", "Daftar buku berhasil diexport ke export_buku.txt")


# ==========================
#   RUN PROGRAM
# ==========================
if __name__ == "__main__":
    root = tk.Tk()
    app = LibraryApp(root)
    root.mainloop()
