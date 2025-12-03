import tkinter as tk
import random
from tkinter import messagebox
from PIL import Image, ImageTk

# ===============================
# CLASS STACK
# ===============================
class Stack:
    def __init__(self):
        self.items = []
    def push(self, item):
        self.items.append(item)
    def pop(self):
        return self.items.pop() if self.items else None
    def is_empty(self):
        return len(self.items) == 0

# ===============================
# CLASS QUEUE
# ===============================
class Queue:
    def __init__(self):
        self.items = []
    def enqueue(self, item):
        self.items.append(item)
    def size(self):
        return len(self.items)

# ===============================
# MEMORY GAME
# ===============================
class MemoryGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Memory Playing Card Game")
        self.root.geometry("650x730")
        self.root.config(bg="#1e233e")

        # PIL — Load image kartu
        self.back_img = ImageTk.PhotoImage(Image.open("cards/BACK.png").resize((95,140)))

        ranks = ["A", "K", "Q", "J"]
        suits = ["S", "H", "D", "C"]
        selected = [f"{r}{s}" for r in ranks for s in suits][:8]

        self.cards = selected * 2
        random.shuffle(self.cards)

        self.images = {c: ImageTk.PhotoImage(Image.open(f"cards/{c}.png").resize((95,140))) for c in selected}

        self.buttons = []
        self.opened_cards = []
        self.stack_history = Stack()
        self.queue_finish = Queue()

        self.score = 0
        self.steps = 0

        self.create_ui()

    def create_ui(self):
        tk.Label(self.root, text="MEMORY PLAYING CARDS",
                 font=("Verdana", 24, "bold"), bg="#1e233e", fg="#ffd863").pack(pady=10)

        self.frame = tk.Frame(self.root, bg="#1e233e")
        self.frame.pack()

        for i in range(16):
            btn = tk.Button(self.frame, image=self.back_img, bd=0,
                            command=lambda i=i: self.open_card(i))
            btn.grid(row=i // 4, column=i % 4, padx=7, pady=7)
            self.buttons.append(btn)

        self.info_score = tk.Label(self.root, text=f"Score: {self.score}",
                                   font=("Verdana", 15, "bold"), bg="#1e233e", fg="#57ff6e")
        self.info_score.pack()

        self.info_steps = tk.Label(self.root, text=f"Langkah: {self.steps}",
                                   font=("Verdana", 15, "bold"), bg="#1e233e", fg="#ffb04d")
        self.info_steps.pack(pady=5)

        tk.Button(self.root, text="Undo", command=self.undo_move,
                  width=20, font=("Verdana", 11, "bold"),
                  bg="#ff6f69", fg="white").pack(pady=6)

        tk.Button(self.root, text="Restart Game", command=self.restart_game,
                  width=20, font=("Verdana", 11, "bold"),
                  bg="#0099ff", fg="white").pack(pady=2)

    # ===========================
    def open_card(self, index):
        if len(self.opened_cards) == 2:
            return

        if self.buttons[index]["image"] != str(self.back_img):
            return

        card = self.cards[index]
        self.buttons[index].config(image=self.images[card])
        self.opened_cards.append(index)
        self.stack_history.push(index)

        if len(self.opened_cards) == 2:
            self.steps += 1
            self.update_info()
            self.root.after(600, self.check_match)

    # ===========================
    def check_match(self):
        i1, i2 = self.opened_cards
        if self.cards[i1] == self.cards[i2]:
            self.queue_finish.enqueue(self.cards[i1])
            self.score += 10
        else:
            self.buttons[i1].config(image=self.back_img)
            self.buttons[i2].config(image=self.back_img)
            self.score = max(0, self.score - 2)

        self.opened_cards = []
        self.update_info()

        if self.queue_finish.size() == 8:
            messagebox.showinfo("Selesai!",
                                f"🎉 Kamu menang!\nLangkah: {self.steps}\nScore: {self.score}")

    # ===========================
    def undo_move(self):
        if self.stack_history.is_empty(): return
        last = self.stack_history.pop()
        self.buttons[last].config(image=self.back_img)

    # ===========================
    def restart_game(self):
        random.shuffle(self.cards)
        self.score = 0
        self.steps = 0
        self.opened_cards = []
        self.stack_history = Stack()
        self.queue_finish = Queue()
        for btn in self.buttons:
            btn.config(image=self.back_img)
        self.update_info()

    # ===========================
    def update_info(self):
        self.info_score.config(text=f"Score: {self.score}")
        self.info_steps.config(text=f"Langkah: {self.steps}")


root = tk.Tk()
MemoryGame(root)
root.mainloop()
