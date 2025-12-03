import tkinter as tk
import random
from tkinter import messagebox

# ===============================
# CLASS STACK (untuk history klik)
# ===============================
class Stack:
    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        if not self.is_empty():
            return self.items.pop()
        return None

    def is_empty(self):
        return len(self.items) == 0

# ========================================
# CLASS QUEUE (untuk menyimpan kartu komplit)
# ========================================
class Queue:
    def __init__(self):
        self.items = []

    def enqueue(self, item):
        self.items.append(item)

    def size(self):
        return len(self.items)

# ===========================
# CLASS MEMORY GAME
# ===========================
class MemoryGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Memory Number Game - Score Edition")
        self.root.geometry("500x670")
        self.root.config(bg="#1e233e")

        self.buttons = []
        self.opened_cards = []
        self.numbers = list(range(1, 9)) * 2
        random.shuffle(self.numbers)

        self.stack_history = Stack()
        self.queue_finish = Queue()

        self.score = 0
        self.steps = 0

        self.create_ui()

    def create_ui(self):
        tk.Label(self.root, text="MEMORY NUMBER GAME",
                 font=("Verdana", 23, "bold"),
                 bg="#1e233e", fg="#7df9ff").pack(pady=10)

        self.frame = tk.Frame(self.root, bg="#2d355a", highlightbackground="#7df9ff",
                              highlightthickness=3)
        self.frame.pack(pady=20)

        for i in range(16):
            btn = tk.Button(self.frame, text="?", width=5, height=2,
                            font=("Consolas", 22, "bold"),
                            bg="#3a4a78", fg="white",
                            activebackground="#254c9e",
                            command=lambda i=i: self.open_card(i))
            btn.grid(row=i // 4, column=i % 4, padx=8, pady=8)
            self.buttons.append(btn)

        self.info_score = tk.Label(self.root,
                                   text=f"Score: {self.score}",
                                   font=("Verdana", 14, "bold"),
                                   bg="#1e233e", fg="#57ff6e")
        self.info_score.pack()

        self.info_steps = tk.Label(self.root,
                                   text=f"Langkah: {self.steps}",
                                   font=("Verdana", 14, "bold"),
                                   bg="#1e233e", fg="#ffc04c")
        self.info_steps.pack(pady=5)

        tk.Button(self.root, text="Undo", command=self.undo_move,
                  width=20, font=("Verdana", 11, "bold"),
                  bg="#ff6f69", fg="white",
                  activebackground="#d85c57").pack(pady=8)

        tk.Button(self.root, text="Restart Game", command=self.restart_game,
                  width=20, font=("Verdana", 11, "bold"),
                  bg="#0099ff", fg="white",
                  activebackground="#0076c7").pack(pady=5)
        
        
                  
    # ===========================
    # Membuka kartu
    # ===========================
    def open_card(self, index):
        if len(self.opened_cards) == 2:
            messagebox.showwarning("Peringatan", "Maksimal hanya dapat membuka 2 kartu!!! ")
            return

        if self.buttons[index]["text"] != "?":
            return

        self.buttons[index].config(text=str(self.numbers[index]), bg="#1f7be8")
        self.opened_cards.append(index)
        self.stack_history.push(index)

        if len(self.opened_cards) == 2:
            self.steps += 1
            self.update_info()
            self.root.after(650, self.check_match)

    # ===========================
    # Mengecek kecocokan
    # ===========================
    def check_match(self):
        i1, i2 = self.opened_cards

        if self.numbers[i1] == self.numbers[i2]:
            self.buttons[i1].config(bg="#13b357")
            self.buttons[i2].config(bg="#13b357")
            self.queue_finish.enqueue(self.numbers[i1])
            self.score += 10
        else:
            self.buttons[i1].config(text="?", bg="#3a4a78")
            self.buttons[i2].config(text="?", bg="#3a4a78")
            self.score = max(0, self.score - 2)

        self.opened_cards = []
        self.update_info()

        if self.queue_finish.size() == 8:
            messagebox.showinfo("Selesai!", f"Kamu selesai!\nLangkah: {self.steps}\nScore: {self.score}")

    # ===========================
    # Undo menggunakan Stack
    # ===========================
    def undo_move(self):
        if self.stack_history.is_empty():
            messagebox.showwarning("Undo", "Tidak ada yang bisa di-undo.")
            return

        last_index = self.stack_history.pop()
        if self.buttons[last_index]["text"] != "?":
            self.buttons[last_index].config(text="?", bg="#3a4a78")

    # ===========================
    # Restart Game
    # ===========================
    def restart_game(self):
        self.score = 0
        self.steps = 0
        self.opened_cards = []
        self.stack_history = Stack()
        self.queue_finish = Queue()

        random.shuffle(self.numbers)

        for btn in self.buttons:
            btn.config(text="?", bg="#3a4a78")

        self.update_info()

    # ===========================
    # Update score & langkah
    # ===========================
    def update_info(self):
        self.info_score.config(text=f"Score: {self.score}")
        self.info_steps.config(text=f"Langkah: {self.steps}")


# =========================
# MAIN PROGRAM
# =========================
root = tk.Tk()
MemoryGame(root)
root.mainloop()
