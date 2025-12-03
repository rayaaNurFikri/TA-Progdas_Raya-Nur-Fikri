"""
digital_library.py
Digital Library demo (Python 3 + Tkinter)

Features:
- OOP: Book, Library, RequestQueue, HistoryStack, LibraryApp
- GUI: add/edit/delete/search, borrow (enqueue), process queue, return, history undo
- Persistence: auto-save/load JSON (library_db.json)
- Stack: history/undo
- Queue: borrow request queue
- Uses conditional logic and loops throughout
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog, scrolledtext
import json
import os
import time
from collections import deque

# --------------------
# Data classes
# --------------------
class Book:
    def __init__(self, book_id, title, author, pages, copies=1):
        self.book_id = str(book_id)
        self.title = title
        self.author = author
        self.pages = int(pages)
        self.copies = int(copies)  # available copies

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
        return cls(d["book_id"], d["title"], d["author"], d["pages"], d.get("copies",1))


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
        # update allowed fields
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
        """Return list of books where title or author contains query (case-insensitive)"""
        q = query.lower()
        res = []
        for b in self.books.values():
            if q in b.title.lower() or q in b.author.lower():
                res.append(b)
        return res

    def borrow_book(self, book_id):
        """Decrease copy if available, return True if success, False if no copies"""
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
        data = {bid: b.to_dict() for bid, b in self.books.items()}
        try:
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
# Queue & Stack for actions
# --------------------
class RequestQueue:
    """Queue to hold borrow requests (dicts: {'request_id', 'book_id', 'user', 'time'})"""
    def __init__(self):
        self.q = deque()
    def enqueue(self, req):
        self.q.append(req)
    def dequeue(self):
        return self.q.popleft() if self.q else None
    def size(self):
        return len(self.q)
    def is_empty(self):
        return len(self.q) == 0
    def peek_all(self):
        return list(self.q)

class HistoryStack:
    """LIFO stack to store history actions for undo"""
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
        self.root.title("Perpustakaan Digital - Praktikum")
        self.root.geometry("1000x600")
        self.library = Library()
        self.queue = RequestQueue()
        self.history = HistoryStack()
        self.setup_gui()
        # process queue periodically
        self.root.after(800, self.process_queue_worker)

    def setup_gui(self):
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill="x")

        ttk.Label(top, text="Cari:").pack(side="left")
        self.search_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.search_var, width=40).pack(side="left", padx=6)
        ttk.Button(top, text="Cari", command=self.search_books).pack(side="left")
        ttk.Button(top, text="Tampilkan Semua", command=self.refresh_book_list).pack(side="left", padx=6)

        ttk.Button(top, text="Tambah Buku", command=self.add_book_dialog).pack(side="right", padx=6)
        ttk.Button(top, text="Export Daftar Buku", command=self.export_books).pack(side="right")

        # main frames
        main = ttk.PanedWindow(self.root, orient="horizontal")
        main.pack(fill="both", expand=True, padx=8, pady=8)

        # left: book list
        left_frame = ttk.Frame(main, width=420)
        main.add(left_frame, weight=1)
        ttk.Label(left_frame, text="Daftar Buku:").pack(anchor="w")
        self.book_listbox = tk.Listbox(left_frame, height=25)
        self.book_listbox.pack(fill="both", expand=True, padx=4, pady=4)
        self.book_listbox.bind("<<ListboxSelect>>", self.on_book_select)

        # right: details & controls
        right_frame = ttk.Frame(main)
        main.add(right_frame, weight=2)

        # details
        detail_frame = ttk.Frame(right_frame, padding=6, relief="ridge")
        detail_frame.pack(fill="x", padx=4, pady=4)
        ttk.Label(detail_frame, text="Detail Buku", font=("Helvetica", 11, "bold")).pack(anchor="w")
        self.detail_text = scrolledtext.ScrolledText(detail_frame, height=8, wrap="word")
        self.detail_text.pack(fill="x", expand=True)

        # controls
        ctrl_frame = ttk.Frame(right_frame, padding=6)
        ctrl_frame.pack(fill="x", padx=4, pady=4)
        ttk.Button(ctrl_frame, text="Pinjam (enqueue)", command=self.borrow_enqueue).pack(side="left", padx=4)
        ttk.Button(ctrl_frame, text="Kembalikan", command=self.return_book).pack(side="left", padx=4)
        ttk.Button(ctrl_frame, text="Proses Antrian Sekarang", command=self.process_one_request).pack(side="left", padx=4)
        ttk.Button(ctrl_frame, text="Hapus Buku", command=self.delete_book).pack(side="left", padx=4)
        ttk.Button(ctrl_frame, text="Edit Buku", command=self.edit_book_dialog).pack(side="left", padx=4)
        ttk.Button(ctrl_frame, text="Undo Terakhir", command=self.undo_last).pack(side="right", padx=4)

        # bottom right: queue & history
        bottom = ttk.Frame(right_frame, padding=6)
        bottom.pack(fill="both", expand=True, padx=4, pady=4)
        lbl_q = ttk.Label(bottom, text="Antrian Peminjaman (FIFO):")
        lbl_q.pack(anchor="w")
        self.queue_listbox = tk.Listbox(bottom, height=6)
        self.queue_listbox.pack(fill="x", expand=False, pady=4)

        lbl_h = ttk.Label(bottom, text="History (Undo stack - LIFO):")
        lbl_h.pack(anchor="w")
        self.history_listbox = tk.Listbox(bottom, height=6)
        self.history_listbox.pack(fill="x", expand=False, pady=4)

        # populate initial list
        self.refresh_book_list()

    # --------------------
    # Book list management
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
        # parse selected line to get book_id (line starts with ID)
        line = self.book_listbox.get(idx)
        book_id = line.split()[0]
        b = self.library.books.get(book_id)
        if b:
            self.show_book_detail(b)

    def show_book_detail(self, book: Book):
        self.detail_text.delete("1.0", "end")
        text = f"ID: {book.book_id}\nTitle: {book.title}\nAuthor: {book.author}\nPages: {book.pages}\nAvailable copies: {book.copies}"
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
    # Add / Edit / Delete dialogs
    # --------------------
    def add_book_dialog(self):
        # ask for fields
        bid = simpledialog.askstring("Tambah Buku", "Masukkan ID buku (unik):", parent=self.root)
        if not bid:
            return
        if bid in self.library.books:
            messagebox.showerror("Error", "ID sudah ada.")
            return
        title = simpledialog.askstring("Tambah Buku", "Judul:", parent=self.root) or ""
        author = simpledialog.askstring("Tambah Buku", "Penulis:", parent=self.root) or ""
        pages = simpledialog.askinteger("Tambah Buku", "Jumlah halaman:", parent=self.root, minvalue=1, initialvalue=100)
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
        # simple edit via dialogs
        new_title = simpledialog.askstring("Edit Buku", "Judul:", initialvalue=b.title, parent=self.root)
        new_author = simpledialog.askstring("Edit Buku", "Penulis:", initialvalue=b.author, parent=self.root)
        new_pages = simpledialog.askinteger("Edit Buku", "Jumlah halaman:", initialvalue=b.pages, minvalue=1, parent=self.root)
        new_copies = simpledialog.askinteger("Edit Buku", "Jumlah salinan:", initialvalue=b.copies, minvalue=0, parent=self.root)
        try:
            old = b.to_dict()
            self.library.update_book(bid, title=new_title, author=new_author, pages=new_pages, copies=new_copies)
            self.history.push({"action":"edit","before":old,"after":self.library.books[bid].to_dict(),"time":time.time()})
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
    # Borrow / Queue / Process
    # --------------------
    def borrow_enqueue(self):
        sel = self.book_listbox.curselection()
        if not sel:
            messagebox.showinfo("Info", "Pilih buku untuk dipinjam.")
            return
        line = self.book_listbox.get(sel[0])
        bid = line.split()[0]
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
            success = self.library.borrow_book(req["book_id"])
            if success:
                desc = f'Processed: {req["user"]} meminjam {req["book_id"]}'
                self.history.push({"action":"borrow","req":req,"time":time.time()})
                messagebox.showinfo("Done", desc)
            else:
                # no copies: push back? we'll notify user and discard (or could re-enqueue)
                desc = f'Gagal: tidak ada salinan tersedia untuk {req["book_id"]}.'
                messagebox.showwarning("No copies", desc)
                # optionally record failure in history
                self.history.push({"action":"borrow_failed","req":req,"time":time.time()})
        except Exception as e:
            messagebox.showerror("Error", str(e))
        self.update_queue_ui()
        self.update_history_ui()
        self.refresh_book_list()

    def process_queue_worker(self):
        # automatic processing simulation: process one request every tick if any
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
        # reschedule
        self.root.after(5000, self.process_queue_worker)  # every 5 seconds

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
        # interpret action and reverse it
        act = item.get("action")
        try:
            if act == "add":
                bid = item["book"]["book_id"]
                # remove added book
                if bid in self.library.books:
                    self.library.delete_book(bid)
            elif act == "delete":
                # restore deleted book
                b = Book.from_dict(item["book"])
                self.library.add_book(b)
            elif act == "edit":
                before = item["before"]
                self.library.update_book(before["book_id"], title=before["title"], author=before["author"], pages=before["pages"], copies=before["copies"])
            elif act == "borrow":
                # undo borrow -> increment copies back
                req = item["req"]
                self.library.return_book(req["book_id"])
            elif act == "borrow_failed":
                # nothing to undo except remove history entry
                pass
            elif act == "return":
                # undo return -> decrement copies (if possible)
                bid = item["book_id"]
                # ensure there's at least 1 copy to remove (can't make negative)
                if self.library.books[bid].copies > 0:
                    self.library.books[bid].copies -= 1
                    self.library.save_db()
            else:
                # unknown action
                pass
            messagebox.showinfo("Undo", f"Berhasil membatalkan aksi: {act}")
        except Exception as e:
            messagebox.showerror("Undo Error", str(e))
        self.update_history_ui()
        self.refresh_book_list()

    def update_history_ui(self):
        self.history_listbox.delete(0, "end")
        # show last 10 actions (newest on top)
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
