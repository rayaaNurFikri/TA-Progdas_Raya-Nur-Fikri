"""
translator_with_dict.py
Offline Indonesian->English translator using an external JSON dictionary.

Features:
- OOP: Translator, RequestQueue, HistoryStack, TranslatorApp
- GUI: Tkinter with input, output, language selection (ID->EN and EN->ID),
       queue enqueue, direct translate, undo (stack), show queue size.
- Queue & Stack: RequestQueue (FIFO) and HistoryStack (LIFO).
- Loads dictionary from kamus_id_en.json (must be in same folder).
- If the JSON file is missing, a small sample dictionary is created automatically.
- Word-level translation preserving punctuation and capitalization.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
from collections import deque
import json
import os
import string
import time


# --------------------
# Translator (loads external dictionary)
# --------------------
class Translator:
    def __init__(self, dict_path="kamus_id_en.json"):
        """
        Load dictionary from JSON.
        Expected format (JSON object): { "kata_ind": "word_en", ... }
        The translator will also build the reverse lookup automatically.
        """
        self.dict_path = dict_path
        self.id_en = {}
        self.en_id = {}
        self.load_dictionary()

    def load_dictionary(self):
        # If dictionary file does not exist, create a small sample dictionary
        if not os.path.exists(self.dict_path):
            sample = {
                "makan": "eat",
                "minum": "drink",
                "buku": "book",
                "mahasiswa": "student",
                "perpustakaan": "library",
                "halo": "hello",
                "terima kasih": "thank you",
                "tolong": "please",
                "ya": "yes",
                "tidak": "no",
                "hari": "day",
                "pagi": "morning",
                "sore": "afternoon",
                "malam": "night",
                "air": "water",
                "rumah": "house",
                "mobil": "car",
                "sekolah": "school"
            }
            with open(self.dict_path, "w", encoding="utf-8") as f:
                json.dump(sample, f, ensure_ascii=False, indent=2)
            self.id_en = sample
            print(f"[Info] Sample dictionary created at '{self.dict_path}'. Replace with full dictionary to translate more words.")
        else:
            try:
                with open(self.dict_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if not isinstance(data, dict):
                    raise ValueError("Dictionary JSON must be an object of key:value pairs.")
                # normalize keys/values to lowercase for lookups
                self.id_en = {k.lower(): v.lower() for k, v in data.items()}
            except Exception as e:
                messagebox.showerror("Dictionary Load Error", f"Gagal memuat kamus: {e}")
                self.id_en = {}

        # create reverse mapping (english -> indonesian). If multiple keys map to same value,
        # keep the first encountered mapping.
        self.en_id = {}
        for k, v in self.id_en.items():
            if v not in self.en_id:
                self.en_id[v] = k

    def translate_word_id_to_en(self, word):
        """
        Translate a single Indonesian word to English using the loaded dictionary.
        Returns the translated word if found, otherwise returns [word] to mark unknown.
        """
        if not word:
            return word
        w = word.lower()
        if w in self.id_en:
            return self.id_en[w]
        # fallback heuristics: try remove common suffixes (simple)
        suffixes = ["lah", "kah", "ku", "mu", "nya", "kan", "i", "an"]
        for suf in suffixes:
            if w.endswith(suf) and w[:-len(suf)] in self.id_en:
                return self.id_en[w[:-len(suf)]]
        return f"[{word}]"

    def translate_word_en_to_id(self, word):
        if not word:
            return word
        w = word.lower()
        if w in self.en_id:
            return self.en_id[w]
        return f"[{word}]"

    def translate_text(self, text, src_lang, tgt_lang):
        """
        Word-level translation preserving punctuation and capitalization.
        src_lang and tgt_lang expected values: "Indonesian" or "English"
        """

        if src_lang == tgt_lang:
            return text

        tokens = []
        for token in text.split():
            lead = ''
            trail = ''
            core = token

            while core and core[0] in string.punctuation:
                lead += core[0]
                core = core[1:]
            while core and core[-1] in string.punctuation:
                trail = core[-1] + trail
                core = core[:-1]

            if not core:
                tokens.append(token)  # pure punctuation token
                continue

            # preserve capitalization info
            was_title = core.istitle()
            was_upper = core.isupper()

            translated_core = core
            if src_lang == "Indonesian" and tgt_lang == "English":
                translated_core = self.translate_word_id_to_en(core)
            elif src_lang == "English" and tgt_lang == "Indonesian":
                translated_core = self.translate_word_en_to_id(core)
            else:
                translated_core = core

            # apply capitalization rules
            if translated_core.startswith("["):
                # unknown tokens keep original capitalization
                translated = translated_core
            else:
                if was_upper:
                    translated = translated_core.upper()
                elif was_title:
                    translated = translated_core.capitalize()
                else:
                    translated = translated_core

            new_token = lead + translated + trail
            tokens.append(new_token)

        return " ".join(tokens)


# --------------------
# Queue & Stack
# --------------------
class RequestQueue:
    def __init__(self):
        self.q = deque()

    def enqueue(self, req):
        self.q.append(req)

    def dequeue(self):
        if self.q:
            return self.q.popleft()
        return None

    def is_empty(self):
        return len(self.q) == 0

    def size(self):
        return len(self.q)


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
class TranslatorApp:
    def __init__(self, root, dict_path="kamus_id_en.json"):
        self.root = root
        self.root.title("Offline Indonesian↔English Translator")
        self.root.geometry("900x560")
        self.translator = Translator(dict_path)
        self.request_queue = RequestQueue()
        self.history_stack = HistoryStack()
        self.setup_gui()
        self.root.after(250, self.queue_worker)

    def setup_gui(self):
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill="x")

        ttk.Label(top, text="Source:").pack(side="left")
        self.src_var = tk.StringVar(value="Indonesian")
        src_cb = ttk.Combobox(top, textvariable=self.src_var, state="readonly", width=16)
        src_cb['values'] = ("Indonesian", "English")
        src_cb.pack(side="left", padx=6)

        ttk.Label(top, text="Target:").pack(side="left")
        self.tgt_var = tk.StringVar(value="English")
        tgt_cb = ttk.Combobox(top, textvariable=self.tgt_var, state="readonly", width=16)
        tgt_cb['values'] = ("English", "Indonesian")
        tgt_cb.pack(side="left", padx=6)

        load_btn = ttk.Button(top, text="Load Dictionary...", command=self.load_dictionary_file)
        load_btn.pack(side="right", padx=6)

        # main area
        main = ttk.Frame(self.root, padding=8)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True)
        ttk.Label(left, text="Input Text:").pack(anchor="w")
        self.input_text = scrolledtext.ScrolledText(left, height=15, wrap="word")
        self.input_text.pack(fill="both", expand=True, pady=4)

        mid_controls = ttk.Frame(main, width=150)
        mid_controls.pack(side="left", fill="y", padx=8)
        ttk.Button(mid_controls, text="Translate (enqueue)", command=self.enqueue_translate).pack(fill="x", pady=4)
        ttk.Button(mid_controls, text="Translate Now (direct)", command=self.translate_now).pack(fill="x", pady=4)
        ttk.Button(mid_controls, text="Undo (pop history)", command=self.undo).pack(fill="x", pady=4)
        ttk.Button(mid_controls, text="Clear All", command=self.clear_all).pack(fill="x", pady=4)
        ttk.Button(mid_controls, text="Show Queue Size", command=self.show_queue_size).pack(fill="x", pady=4)
        ttk.Button(mid_controls, text="Export Output...", command=self.export_output).pack(fill="x", pady=4)

        right = ttk.Frame(main)
        right.pack(side="left", fill="both", expand=True)
        ttk.Label(right, text="Translated Text:").pack(anchor="w")
        self.output_text = scrolledtext.ScrolledText(right, height=15, wrap="word")
        self.output_text.pack(fill="both", expand=True, pady=4)

        # history
        bottom = ttk.Frame(self.root, padding=8)
        bottom.pack(fill="both")
        ttk.Label(bottom, text="History (double-click to restore original into input):").pack(anchor="w")
        self.history_list = tk.Listbox(bottom, height=6)
        self.history_list.pack(fill="both", expand=True)
        self.history_list.bind("<Double-Button-1>", self.restore_from_history)

    # --------------------
    # Dictionary management
    # --------------------
    def load_dictionary_file(self):
        path = filedialog.askopenfilename(title="Open dictionary JSON", filetypes=[("JSON files","*.json"),("All files","*.*")])
        if not path:
            return
        self.translator.dict_path = path
        self.translator.load_dictionary()
        messagebox.showinfo("Dictionary Loaded", f"Loaded dictionary from:\n{path}\nTotal entries: {len(self.translator.id_en)}")

    # --------------------
    # Actions
    # --------------------
    def enqueue_translate(self):
        text = self.input_text.get("1.0", "end").strip()
        if not text:
            messagebox.showinfo("Info", "Masukkan teks dulu.")
            return
        req = {"text": text, "src": self.src_var.get(), "tgt": self.tgt_var.get(), "time": time.time()}
        self.request_queue.enqueue(req)
        messagebox.showinfo("Queued", f"Permintaan dimasukkan ke antrian (posisi {self.request_queue.size()}).")

    def translate_now(self):
        text = self.input_text.get("1.0", "end").strip()
        src = self.src_var.get()
        tgt = self.tgt_var.get()
        if not text:
            messagebox.showinfo("Info", "Masukkan teks dulu.")
            return
        if src == tgt:
            messagebox.showwarning("Warning", "Source dan target sama.")
            return
        translated = self.translator.translate_text(text, src, tgt)
        hist = {"original": text, "translated": translated, "src": src, "tgt": tgt, "time": time.time()}
        self.history_stack.push(hist)
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", translated)
        self.update_history_list(hist)

    def undo(self):
        popped = self.history_stack.pop()
        if not popped:
            messagebox.showinfo("Info", "Tidak ada history untuk di-undo.")
            return
        prev = self.history_stack.peek()
        if prev:
            self.output_text.delete("1.0", "end")
            self.output_text.insert("1.0", prev["translated"])
        else:
            self.output_text.delete("1.0", "end")
        # remove top entry from listbox (which we insert newest at 0)
        if self.history_list.size() > 0:
            self.history_list.delete(0)

    def clear_all(self):
        if messagebox.askyesno("Confirm", "Hapus input, output, antrian, dan history?"):
            self.input_text.delete("1.0", "end")
            self.output_text.delete("1.0", "end")
            self.request_queue = RequestQueue()
            self.history_stack = HistoryStack()
            self.history_list.delete(0, "end")

    def show_queue_size(self):
        messagebox.showinfo("Queue Size", f"Jumlah permintaan di antrian: {self.request_queue.size()}")

    def export_output(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files","*.txt")])
        if not path:
            return
        text = self.output_text.get("1.0", "end")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        messagebox.showinfo("Exported", f"Output diexport ke {path}")

    def update_history_list(self, hist):
        display = f"{hist['src']}→{hist['tgt']} : {hist['original'][:60]} → {hist['translated'][:60]}"
        self.history_list.insert(0, display)

    def restore_from_history(self, event):
        sel = self.history_list.curselection()
        if not sel:
            return
        txt = self.history_list.get(sel[0])
        found = None
        # search stack for matching entry (iterate from newest)
        for item in reversed(self.history_stack.stack):
            preview = f"{item['src']}→{item['tgt']} : {item['original'][:60]} → {item['translated'][:60]}"
            if preview == txt:
                found = item
                break
        if found:
            self.input_text.delete("1.0", "end")
            self.input_text.insert("1.0", found['original'])
            messagebox.showinfo("Restored", "Teks asli dipulihkan ke input.")

    # --------------------
    # Queue worker
    # --------------------
    def queue_worker(self):
        # process one request per tick to keep UI responsive
        if not self.request_queue.is_empty():
            req = self.request_queue.dequeue()
            if req["src"] == req["tgt"]:
                translated = req["text"]
            else:
                translated = self.translator.translate_text(req["text"], req["src"], req["tgt"])
            hist = {"original": req["text"], "translated": translated, "src": req["src"], "tgt": req["tgt"], "time": req["time"]}
            self.history_stack.push(hist)
            # append to output with separator
            existing = self.output_text.get("1.0", "end").strip()
            newtext = (existing + "\n\n--- Queued Translation ---\n" + translated).strip() if existing else translated
            self.output_text.delete("1.0", "end")
            self.output_text.insert("1.0", newtext)
            self.update_history_list(hist)
        self.root.after(250, self.queue_worker)


def main():
    root = tk.Tk()
    app = TranslatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()


