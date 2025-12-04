import tkinter as tk
import random
from tkinter import messagebox

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

class Queue:
    def __init__(self):
        self.items = []
    def enqueue(self, item):
        self.items.append(item)
    def size(self):
        return len(self.items)

class MemoryGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Memory Number Game - Score Edition")
        self.root.geometry("500x700")
        self.root.config(bg="#1e233e")

        self.buttons = []
        self.opened_cards = []
        self.numbers = list(range(1, 9)) * 2
        random.shuffle(self.numbers)

        self.stack_history = Stack()
        self.queue_finish = Queue()

        self._score = 0
        self._steps = 0
        self.history_score = []
        self.history_steps = []

        self.time_seconds = 120
        self.timer_running = False

        self.create_ui()
        self.start_timer()

    def create_ui(self):
        tk.Label(self.root, text="MEMORY NUMBER GAME",
                 font=("Verdana", 23, "bold"),
                 bg="#1e233e", fg="#7df9ff").pack(pady=10)

        self.frame = tk.Frame(self.root, bg="#2d355a",
                              highlightbackground="#7df9ff",
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

        self.info_score = tk.Label(self.root, text=f"Score: {self._score}",
                                   font=("Verdana", 14, "bold"),
                                   bg="#1e233e", fg="#57ff6e")
        self.info_score.pack()

        self.info_steps = tk.Label(self.root, text=f"Langkah: {self._steps}",
                                   font=("Verdana", 14, "bold"),
                                   bg="#1e233e", fg="#ffc04c")
        self.info_steps.pack(pady=5)

        self.info_timer = tk.Label(self.root, text="Timer: 02:00",
                                   font=("Verdana", 14, "bold"),
                                   bg="#1e233e", fg="#f94dff")
        self.info_timer.pack(pady=5)

        tk.Button(self.root, text="Undo", command=self.undo_move,
                  width=20, font=("Verdana", 11, "bold"),
                  bg="#ff6f69", fg="white",
                  activebackground="#d85c57").pack(pady=8)

        tk.Button(self.root, text="Restart Game", command=self.restart_game,
                  width=20, font=("Verdana", 11, "bold"),
                  bg="#0099ff", fg="white",
                  activebackground="#0076c7").pack(pady=5)

    def start_timer(self):
        if not self.timer_running:
            self.timer_running = True
            self.update_timer()

    def update_timer(self):
        if not self.timer_running:
            return

        minutes = self.time_seconds // 60
        seconds = self.time_seconds % 60
        self.info_timer.config(text=f"Timer: {minutes:02d}:{seconds:02d}")

        if self.time_seconds == 0:
            self.timer_running = False
            self.game_over()
            return

        self.time_seconds -= 1
        self.root.after(1000, self.update_timer)

    def game_over(self):
        for btn in self.buttons:
            btn.config(state="disabled")
        messagebox.showerror("GAME OVER", "Waktu habis!\nSilahkan restart game.")

    def open_card(self, index):
        if not self.timer_running:
            return

        if len(self.opened_cards) == 2:
            messagebox.showwarning("Peringatan", "Maksimal hanya dapat membuka 2 kartu!")
            return
        if self.buttons[index]["text"] != "?":
            return

        self.buttons[index].config(text=str(self.numbers[index]), bg="#1f7be8")
        self.opened_cards.append(index)
        self.stack_history.push(index)

        if len(self.opened_cards) == 2:
            self._steps += 1
            self.update_info()
            self.root.after(650, self.check_match)

    def check_match(self):
        i1, i2 = self.opened_cards

        self.history_score.append(self._score)
        self.history_steps.append(self._steps)

        if self.numbers[i1] == self.numbers[i2]:
            self.buttons[i1].config(bg="#13b357")
            self.buttons[i2].config(bg="#13b357")
            self.queue_finish.enqueue(self.numbers[i1])
            self._score += 10
        else:
            self.buttons[i1].config(text="?", bg="#3a4a78")
            self.buttons[i2].config(text="?", bg="#3a4a78")
            self._score = max(0, self._score - 2)

        self.opened_cards = []
        self.update_info()

        if self.queue_finish.size() == 8:
            self.timer_running = False
            messagebox.showinfo("Selesai!",
                                f"Kamu selesai!\nLangkah: {self._steps}\nScore: {self._score}\nWaktu: {self.info_timer.cget('text')}")

    def undo_move(self):
        if self.stack_history.is_empty():
            messagebox.showwarning("Undo", "Tidak ada yang bisa di-undo.")
            return

        last_index = self.stack_history.pop()
        if self.buttons[last_index]["bg"] == "#13b357":
            messagebox.showwarning("Undo", "Kartu match tidak bisa di-undo.")
            return

        if len(self.opened_cards) == 1:
            self.buttons[last_index].config(text="?", bg="#3a4a78")
            self.opened_cards.remove(last_index)
            return

        if self.history_score and self.history_steps:
            self._score = self.history_score.pop()
            self._steps = self.history_steps.pop()

        self.buttons[last_index].config(text="?", bg="#3a4a78")
        if last_index in self.opened_cards:
            self.opened_cards.remove(last_index)

        self.update_info()

    # 🔥 Perbaikan penuh timer restart
    def restart_game(self):
        self._score = 0
        self._steps = 0
        self.opened_cards = []
        self.stack_history = Stack()
        self.queue_finish = Queue()
        self.history_score = []
        self.history_steps = []

        random.shuffle(self.numbers)

        for btn in self.buttons:
            btn.config(text="?", bg="#3a4a78", state="normal")

        # --- FIX TIMER ---
        self.timer_running = False
        self.time_seconds = 120
        self.info_timer.config(text="Timer: 02:00")
        self.timer_running = True
        self.update_timer()

        self.update_info()

    def update_info(self):
        self.info_score.config(text=f"Score: {self._score}")
        self.info_steps.config(text=f"Langkah: {self._steps}")

root = tk.Tk()
MemoryGame(root)
root.mainloop()
