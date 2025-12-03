"""
digital_library_full.py
Digital Library (complete):
- CRUD (Add / Edit / Delete books)
- Search by title/author
- Borrow (enqueue request FIFO)
- Process queue: auto process 1 request per cycle (simulated staff)
- Return book
- History stack for undo last action
- Auto-save / load database (library_db.json)
- Export book list to .txt
- Popup if book is already borrowed
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog, scrolledtext
import json, os, time
from collections import deque

# --------------------
# Domain classes
# --------------------
class Book:
    def __init__(self, book_id, title, author, pages=0, copies=1):
        self.book_id = str(book_id)
        self.title = title
        self.author = author
        self.pages = int(pages)
        self.copies = int(copies)   # available copies

    def to_dict(self):
        return {
            "book_id": self.book_id,
            "title": self.title,
            "author": self.author,
            "pages": self.pages,
            "copies": self.copies
        }

    @classmethod
    def from_dict(cls, d):
        return cls(d["book_id"], d["title"], d["author"], d.get("pages",0), d.get("copies",1))

# --------------------
# Library (persistence + operations)
# --------------------
class Library:
    def __init__(self, db_path="library_db.json"):
        self.db_path = db_path
        self.books = {}  # book_id -> Book
        self.load_db()

    def add_book(self, book: Book):
        if book.book_id in self.books:
            raise ValueError("Book ID already exists.")
        self.books[book.book_id] = book
        self.save_db()

    def update_book(self, book_id, **kwargs):
        if book_id not in self.books:
            raise KeyError("Book not found.")
        b = self.books[book_id]
        if "title" in kwargs: b.title = kwargs["title"]
        if "author" in kwargs: b.author = kwargs["author"]
        if "pages" in kwargs: b.pages = int(kwargs["pages"])
        if "copies" in kwargs: b.copies = int(kwargs["copies"])
        self.save_db()

    def delete_book(self, book_id):
        if book_id in self.books:
            del self.books[book_id]
            self.save_db()
        else:
            raise KeyError("Book not found.")

    def find_books(self, query):
        q = query.strip().lower()
        res = []
        for b in self.books.values():
            if q in b.title.lower() or q in b.author.lower():
                res.append(b)
        return res

    def borrow_book(self, book_id):
        if book_id not in self.books:
            raise KeyError("Book not found.")
        book = self.books[book_id]
        if book.copies > 0:
            book.copies -= 1
            self.save_db()
            return True
        return False

    def return_book(self, book_id):
        if book_id not in self.books:
            raise KeyError("Book not found.")
        self.books[book_id].copies += 1
        self.save_db()

    def list_books(self):
        return list(self.books.values())

    def save_db(self):
        try:
            data = {bid: b.to_dict() for bid, b in self.books.items()}
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("Error saving DB:", e)

    def load_db(self):
        if not os.path.exists(self.db_path):
            # create sample DB
            sample = {
                "B001": Book("B001","Pemrograman Python","Andi",320,3).to_dict(),
                "B002": Book("B002","Struktur Data & Algoritma","Budi",280,2).to_dict(),
                "B003": Book("B003","Basis Data","Citra",240,1).to_dict()
            }
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(sample, f, ensure_ascii=False, indent=2)
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.books = {bid: Book.from_dict(d) for bid, d in data.items()}
        except Exception as e:
            print("Error loading DB:", e)
            self.books = {}

# --------------------
# Queue & History (stack)
# --------------------
class RequestQueue:
    def __init__(self):
        self.q = deque()

    def enqueue(self, req):
        self.q.append(req)

    def dequeue(self):
        return self.q.popleft() if self.q else None

    def is_empty(self):
        return len(self.q) == 0

    def size(self):
        return len(self.q)

    def peek_all(self):
        return list(self.q)

class HistoryStack:
    def __init__(self):
        self.stack = []

    def push(self, item):
        self.stack.append(item)

    def pop(self):
        return self.stack.pop() if self.stack else None

    def peek(self):
        return self.stack[-1] if self.stack else None

    def clear(self):
        self.stack = []

# --------------------
# GUI Application
# --------------------
class LibraryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📚 Perpustakaan Digital Modern (No External Modules)")
        self.root.geometry("1100x650")
        self.root.config(bg="#1f1f1f")  # Dark background

        self.library = Library()
        self.queue = RequestQueue()
        self.history = HistoryStack()

        self.make_styles()
        self.setup_gui()

        self.root.after(4000, self.process_queue_worker)

    # =============================================================
    # STYLE / THEME (No external module)
    # =============================================================
    def make_styles(self):
        style = ttk.Style()

        style.theme_use("clam")

        # Treeview modern
        style.configure(
            "Treeview",
            background="#2a2a2a",
            foreground="white",
            fieldbackground="#2a2a2a",
            rowheight=28,
            bordercolor="#444",
            borderwidth=1
        )
        style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 11, "bold"),
            background="#444",
            foreground="white"
        )

        # Button style
        style.configure(
            "Modern.TButton",
            font=("Segoe UI", 11),
            padding=6,
            background="#3a86ff",
            foreground="white",
            borderwidth=0,
            relief="flat"
        )

        # LabelFrame
        style.configure(
            "Modern.TLabelframe",
            background="#1f1f1f",
            foreground="white"
        )
        style.configure(
            "Modern.TLabelframe.Label",
            font=("Segoe UI", 12, "bold"),
            foreground="white",
            background="#1f1f1f"
        )

    # =============================================================
    # GUI SETUP
    # =============================================================
    def setup_gui(self):

        # --- HEADER BAR ---------------------------------------------------
        header = tk.Frame(self.root, height=70, bg="#3a86ff")
        header.pack(fill="x")

        tk.Label(
            header,
            text="📚 PERPUSTAKAAN DIGITAL — MODERN TKINTER UI",
            bg="#3a86ff",
            fg="white",
            font=("Segoe UI", 20, "bold")
        ).pack(pady=15)

        # --- SEARCH BAR ---------------------------------------------------
        top = tk.Frame(self.root, bg="#1f1f1f")
        top.pack(fill="x", pady=10)

        ttk.Label(top, text="🔍 Cari Judul/Penulis:", font=("Segoe UI", 11), background="#1f1f1f", foreground="white").pack(side="left", padx=10)
        self.search_var = tk.StringVar()

        ttk.Entry(top, textvariable=self.search_var, width=40).pack(side="left", padx=10)

        ttk.Button(top, text="Cari", style="Modern.TButton", command=self.search_books).pack(side="left", padx=5)
        ttk.Button(top, text="Tampilkan Semua", style="Modern.TButton", command=self.refresh_book_list).pack(side="left", padx=5)

        ttk.Button(top, text="Tambah Buku", style="Modern.TButton", command=self.add_book_dialog).pack(side="right", padx=5)
        ttk.Button(top, text="Export TXT", style="Modern.TButton", command=self.export_books).pack(side="right", padx=5)

        # --- PANED WINDOW -------------------------------------------------
        main = ttk.Panedwindow(self.root, orient="horizontal")
        main.pack(fill="both", expand=True, padx=10, pady=10)

        # LEFT ================================
        left_frame = ttk.Labelframe(main, text="DAFTAR BUKU", style="Modern.TLabelframe", padding=10)
        main.add(left_frame, weight=1)

        columns = ("id", "title", "author", "copies")
        self.tree = ttk.Treeview(left_frame, columns=columns, show="headings")

        for c in columns:
            self.tree.heading(c, text=c.upper())
            self.tree.column(c, width=150)

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_book_select)

        # RIGHT ===============================
        right_frame = ttk.Frame(main)
        main.add(right_frame, weight=1)

        # DETAIL BOX
        detail_box = ttk.Labelframe(right_frame, text="DETAIL BUKU", style="Modern.TLabelframe", padding=10)
        detail_box.pack(fill="x")

        self.detail_text = scrolledtext.ScrolledText(detail_box, height=8, bg="#2a2a2a", fg="white")
        self.detail_text.pack(fill="x")

        # BUTTON ROW
        ctrl = ttk.Frame(right_frame)
        ctrl.pack(fill="x", pady=10)

        ttk.Button(ctrl, text="Pinjam", style="Modern.TButton", command=self.borrow_enqueue).pack(side="left", padx=5)
        ttk.Button(ctrl, text="Kembalikan", style="Modern.TButton", command=self.return_book).pack(side="left", padx=5)
        ttk.Button(ctrl, text="Proses", style="Modern.TButton", command=self.process_one_request).pack(side="left", padx=5)

        ttk.Button(ctrl, text="Edit", style="Modern.TButton", command=self.edit_book_dialog).pack(side="right", padx=5)
        ttk.Button(ctrl, text="Hapus", style="Modern.TButton", command=self.delete_book).pack(side="right", padx=5)
        ttk.Button(ctrl, text="Undo", style="Modern.TButton", command=self.undo_last).pack(side="right", padx=5)

        # QUEUE + HISTORY
        bottom = ttk.Frame(right_frame)
        bottom.pack(fill="both", expand=True)

        ttk.Label(bottom, text="📥 Antrian Peminjaman", background="#1f1f1f", foreground="white").pack(anchor="w")
        self.queue_listbox = tk.Listbox(bottom, height=6, bg="#2a2a2a", fg="white")
        self.queue_listbox.pack(fill="x", pady=5)

        ttk.Label(bottom, text="📜 History Undo", background="#1f1f1f", foreground="white").pack(anchor="w")
        self.history_listbox = tk.Listbox(bottom, height=6, bg="#2a2a2a", fg="white")
        self.history_listbox.pack(fill="x")

        self.refresh_book_list()


    # --------------------
    # Book list UI
    # --------------------
    def refresh_book_list(self):
        self.book_listbox.delete(0, "end")
        for b in sorted(self.library.list_books(), key=lambda x: x.book_id):
            display = f"{b.book_id} ─ {b.title} ({b.author}) — copies: {b.copies}"
            self.book_listbox.insert("end", display)

    def on_book_select(self, event):
        sel = event.widget.curselection()
        if not sel:
            return
        idx = sel[0]
        line = self.book_listbox.get(idx)
        book_id = line.split()[0]
        b = self.library.books.get(book_id)
        if b:
            self.show_book_detail(b)

    def show_book_detail(self, book: Book):
        self.detail_text.delete("1.0", "end")
        text = (
            f"ID: {book.book_id}\n"
            f"Title: {book.title}\n"
            f"Author: {book.author}\n"
            f"Pages: {book.pages}\n"
            f"Available copies: {book.copies}"
        )
        self.detail_text.insert("1.0", text)

    def search_books(self):
        q = self.search_var.get().strip()
        if not q:
            messagebox.showinfo("Info", "Masukkan kata kunci pencarian.")
            return
        results = self.library.find_books(q)
        self.book_listbox.delete(0, "end")
        for b in results:
            display = f"{b.book_id} ─ {b.title} ({b.author}) — copies: {b.copies}"
            self.book_listbox.insert("end", display)

    # --------------------
    # CRUD dialogs
    # --------------------
    def add_book_dialog(self):
        bid = simpledialog.askstring("Tambah Buku", "Masukkan ID buku (unik):", parent=self.root)
        if not bid:
            return
        if bid in self.library.books:
            messagebox.showerror("Error", "ID sudah ada.")
            return
        title = simpledialog.askstring("Tambah Buku", "Judul:", parent=self.root) or ""
        author = simpledialog.askstring("Tambah Buku", "Penulis:", parent=self.root) or ""
        pages = simpledialog.askinteger("Tambah Buku", "Jumlah halaman:", parent=self.root, minvalue=0, initialvalue=100)
        copies = simpledialog.askinteger("Tambah Buku", "Jumlah salinan:", parent=self.root, minvalue=1, initialvalue=1)
        try:
            book = Book(bid, title, author, pages, copies)
            self.library.add_book(book)
            self.history.push({"action":"add","book":book.to_dict(),"time":time.time()})
            self.update_history_ui()
            self.refresh_book_list()
            messagebox.showinfo("Success", "Buku ditambahkan.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def edit_book_dialog(self):
        sel = self.book_listbox.curselection()
        if not sel:
            messagebox.showinfo("Info", "Pilih buku untuk di-edit.")
            return
        line = self.book_listbox.get(sel[0])
        bid = line.split()[0]
        b = self.library.books.get(bid)
        if not b:
            messagebox.showerror("Error", "Buku tidak ditemukan.")
            return
        new_title = simpledialog.askstring("Edit Buku", "Judul:", initialvalue=b.title, parent=self.root)
        new_author = simpledialog.askstring("Edit Buku", "Penulis:", initialvalue=b.author, parent=self.root)
        new_pages = simpledialog.askinteger("Edit Buku", "Jumlah halaman:", initialvalue=b.pages, minvalue=0, parent=self.root)
        new_copies = simpledialog.askinteger("Edit Buku", "Jumlah salinan:", initialvalue=b.copies, minvalue=0, parent=self.root)
        try:
            before = b.to_dict()
            self.library.update_book(bid, title=new_title, author=new_author, pages=new_pages, copies=new_copies)
            self.history.push({"action":"edit","before":before,"after":self.library.books[bid].to_dict(),"time":time.time()})
            self.update_history_ui()
            self.refresh_book_list()
            messagebox.showinfo("Success", "Buku diperbarui.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_book(self):
        sel = self.book_listbox.curselection()
        if not sel:
            messagebox.showinfo("Info", "Pilih buku untuk dihapus.")
            return
        line = self.book_listbox.get(sel[0])
        bid = line.split()[0]
        if not messagebox.askyesno("Confirm", f"Hapus buku {bid}?"):
            return
        try:
            book_dict = self.library.books[bid].to_dict()
            self.library.delete_book(bid)
            self.history.push({"action":"delete","book":book_dict,"time":time.time()})
            self.update_history_ui()
            self.refresh_book_list()
            self.detail_text.delete("1.0","end")
            messagebox.showinfo("Deleted", "Buku dihapus.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # --------------------
    # Borrowing / Queue
    # --------------------
    def borrow_enqueue(self):
        sel = self.book_listbox.curselection()
        if not sel:
            messagebox.showinfo("Info", "Pilih buku untuk dipinjam.")
            return
        line = self.book_listbox.get(sel[0])
        bid = line.split()[0]
        b = self.library.books.get(bid)
        if not b:
            messagebox.showerror("Error", "Buku tidak ditemukan.")
            return

        # if no copies -> popup immediately
        if b.copies <= 0:
            messagebox.showerror("Gagal", f"Buku '{b.title}' sedang dipinjam semua (tidak ada salinan tersedia).")
            return

        user = simpledialog.askstring("Pinjam Buku", "Masukkan nama peminjam:", parent=self.root)
        if not user:
            return
        req = {"request_id": f"R{int(time.time()*1000)}", "book_id": bid, "user": user, "time": time.time()}
        self.queue.enqueue(req)
        self.update_queue_ui()
        messagebox.showinfo("Queued", f"Permintaan pinjam dimasukkan ke antrian (posisi {self.queue.size()}).")

    def process_one_request(self):
        if self.queue.is_empty():
            messagebox.showinfo("Info", "Antrian kosong.")
            return
        req = self.queue.dequeue()
        try:
            # re-check availability when processing
            success = self.library.borrow_book(req["book_id"])
            if success:
                self.history.push({"action":"borrow","req":req,"time":time.time()})
                messagebox.showinfo("Diproses", f"{req['user']} berhasil meminjam {req['book_id']}")
            else:
                self.history.push({"action":"borrow_failed","req":req,"time":time.time()})
                messagebox.showwarning("Gagal", f"Tidak ada salinan tersedia untuk {req['book_id']}.")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        self.update_queue_ui()
        self.update_history_ui()
        self.refresh_book_list()

    def process_queue_worker(self):
        # automatic processing (1 request per tick)
        if not self.queue.is_empty():
            req = self.queue.dequeue()
            try:
                success = self.library.borrow_book(req["book_id"])
                if success:
                    self.history.push({"action":"borrow","req":req,"time":time.time()})
                else:
                    self.history.push({"action":"borrow_failed","req":req,"time":time.time()})
            except Exception as e:
                self.history.push({"action":"error","detail":str(e),"time":time.time()})
        self.update_queue_ui()
        self.update_history_ui()
        self.refresh_book_list()
        # schedule next tick (4 seconds)
        self.root.after(4000, self.process_queue_worker)

    def update_queue_ui(self):
        self.queue_listbox.delete(0, "end")
        for i, r in enumerate(self.queue.peek_all(), start=1):
            self.queue_listbox.insert("end", f"{i}. {r['request_id']} - {r['book_id']} - {r['user']}")

    # --------------------
    # Return & Undo
    # --------------------
    def return_book(self):
        sel = self.book_listbox.curselection()
        if not sel:
            messagebox.showinfo("Info", "Pilih buku untuk dikembalikan.")
            return
        line = self.book_listbox.get(sel[0])
        bid = line.split()[0]
        try:
            self.library.return_book(bid)
            self.history.push({"action":"return","book_id":bid,"time":time.time()})
            self.update_history_ui()
            self.refresh_book_list()
            messagebox.showinfo("Returned", f"Buku {bid} dikembalikan.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def undo_last(self):
        item = self.history.pop()
        if not item:
            messagebox.showinfo("Info", "Tidak ada aksi untuk di-undo.")
            return
        act = item.get("action")
        try:
            if act == "add":
                bid = item["book"]["book_id"]
                if bid in self.library.books:
                    self.library.delete_book(bid)
            elif act == "delete":
                b = Book.from_dict(item["book"])
                self.library.add_book(b)
            elif act == "edit":
                before = item["before"]
                self.library.update_book(before["book_id"], title=before["title"], author=before["author"], pages=before["pages"], copies=before["copies"])
            elif act == "borrow":
                req = item["req"]
                # undo borrow -> return one copy
                self.library.return_book(req["book_id"])
            elif act == "borrow_failed":
                # nothing to reverse
                pass
            elif act == "return":
                bid = item["book_id"]
                # undo return -> attempt to decrement copies if possible
                if self.library.books[bid].copies > 0:
                    self.library.books[bid].copies -= 1
                    self.library.save_db()
            else:
                pass
            messagebox.showinfo("Undo", f"Berhasil membatalkan aksi: {act}")
        except Exception as e:
            messagebox.showerror("Undo Error", str(e))
        self.update_history_ui()
        self.refresh_book_list()

    def update_history_ui(self):
        self.history_listbox.delete(0, "end")
        for item in list(reversed(self.history.stack))[:10]:
            ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(item.get("time", time.time())))
            desc = item.get("action")
            if desc == "borrow" and "req" in item:
                desc = f"borrow {item['req']['book_id']} by {item['req']['user']}"
            elif desc == "add" and "book" in item:
                desc = f"add {item['book']['book_id']}"
            elif desc == "delete" and "book" in item:
                desc = f"delete {item['book']['book_id']}"
            self.history_listbox.insert("end", f"{ts} ─ {desc}")

    # --------------------
    # Export
    # --------------------
    def export_books(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files","*.txt")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                for b in sorted(self.library.list_books(), key=lambda x: x.book_id):
                    f.write(f"{b.book_id}\t{b.title}\t{b.author}\t{b.pages}\t{b.copies}\n")
            messagebox.showinfo("Exported", f"Daftar buku diexport ke {path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

# --------------------
# Run
# --------------------
def main():
    root = tk.Tk()
    app = LibraryApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

