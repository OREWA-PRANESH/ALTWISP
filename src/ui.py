import queue
import sys
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

from orb import ReactiveOrb


BG = "#0b1020"
PANEL = "#131a2c"
CARD = "#1a2338"
TEXT = "#f4f7ff"
MUTED = "#9aa8c1"
ACCENT = "#6ee7d2"
BLUE = "#73a7ff"
DANGER = "#ff7b8b"


class AppUI:
    def __init__(self, storage, settings, callbacks):
        self.storage = storage
        self.settings = settings
        self.callbacks = callbacks
        self.root = tk.Tk()
        self.root.title("ALTWISP")
        self.root.geometry("940x650")
        self.root.minsize(780, 540)
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_dashboard)
        self.command_queue = queue.Queue()
        self.status_var = tk.StringVar(value="Ready")
        self._configure_styles()
        self._build_dashboard()
        self._build_overlay()
        self.root.after(15, self._drain_commands)

    def _configure_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background=BG)
        style.configure("Card.TFrame", background=CARD)
        style.configure("TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=BG, foreground=TEXT, font=("Segoe UI Semibold", 24))
        style.configure("Muted.TLabel", background=BG, foreground=MUTED, font=("Segoe UI", 10))
        style.configure("Card.TLabel", background=CARD, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("Metric.TLabel", background=CARD, foreground=ACCENT, font=("Segoe UI Semibold", 26))
        style.configure("TButton", font=("Segoe UI Semibold", 10), padding=(14, 8), background=BLUE, foreground="#08101f")
        style.map("TButton", background=[("active", "#91bcff")])
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=PANEL, foreground=MUTED, padding=(18, 10), font=("Segoe UI Semibold", 10))
        style.map("TNotebook.Tab", background=[("selected", CARD)], foreground=[("selected", TEXT)])
        style.configure("Treeview", background=CARD, fieldbackground=CARD, foreground=TEXT, rowheight=30, borderwidth=0)
        style.configure("Treeview.Heading", background=PANEL, foreground=TEXT, relief="flat")
        style.map("Treeview", background=[("selected", "#294066")])
        style.configure("TCheckbutton", background=BG, foreground=TEXT)
        style.configure("TCombobox", fieldbackground=CARD, background=CARD, foreground=TEXT)

    def _build_dashboard(self):
        header = ttk.Frame(self.root, padding=(24, 20, 24, 10))
        header.pack(fill="x")
        ttk.Label(header, text="ALTWISP", style="Title.TLabel").pack(side="left")
        ttk.Label(header, textvariable=self.status_var, style="Muted.TLabel").pack(side="left", padx=18, pady=(9, 0))
        ttk.Button(header, text="Start dictation", command=self.callbacks["toggle"]).pack(side="right")

        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        self.home_tab = ttk.Frame(self.tabs, padding=18)
        self.history_tab = ttk.Frame(self.tabs, padding=18)
        self.dictionary_tab = ttk.Frame(self.tabs, padding=18)
        self.snippets_tab = ttk.Frame(self.tabs, padding=18)
        self.settings_tab = ttk.Frame(self.tabs, padding=18)
        for tab, title in ((self.home_tab, "Home"), (self.history_tab, "History"), (self.dictionary_tab, "Dictionary"),
                           (self.snippets_tab, "Snippets"), (self.settings_tab, "Settings")):
            self.tabs.add(tab, text=title)
        self._build_home()
        self._build_history()
        self._build_entries(self.dictionary_tab, "dictionary", "Spoken word", "Replacement")
        self._build_entries(self.snippets_tab, "snippets", "Voice trigger", "Expansion")
        self._build_settings()

    def _build_home(self):
        cards = ttk.Frame(self.home_tab)
        cards.pack(fill="x")
        self.metric_labels = {}
        for key, label in (("words", "Words dictated"), ("dictations", "Dictations"), ("wpm", "Average WPM")):
            card = ttk.Frame(cards, style="Card.TFrame", padding=20)
            card.pack(side="left", fill="both", expand=True, padx=(0, 12))
            value = ttk.Label(card, text="0", style="Metric.TLabel")
            value.pack(anchor="w")
            ttk.Label(card, text=label, style="Card.TLabel").pack(anchor="w", pady=(4, 0))
            self.metric_labels[key] = value
        help_card = ttk.Frame(self.home_tab, style="Card.TFrame", padding=22)
        help_card.pack(fill="x", pady=22)
        ttk.Label(help_card, text="Speak anywhere", style="Metric.TLabel").pack(anchor="w")
        ttk.Label(help_card, text="Ctrl + Windows starts and stops dictation • Ctrl + Alt + D opens this dashboard • Shift + Alt + Z pastes the last result", style="Card.TLabel").pack(anchor="w", pady=(8, 0))
        ttk.Label(help_card, text="Your dictionary, snippets, settings, and history stay on this computer.", style="Card.TLabel").pack(anchor="w", pady=(6, 0))

    def _build_history(self):
        toolbar = ttk.Frame(self.history_tab)
        toolbar.pack(fill="x", pady=(0, 12))
        ttk.Button(toolbar, text="Copy selected", command=self._copy_history).pack(side="left")
        ttk.Button(toolbar, text="Export JSON", command=self._export_history).pack(side="left", padx=8)
        ttk.Button(toolbar, text="Delete all", command=self._delete_history).pack(side="right")
        self.history_tree = ttk.Treeview(self.history_tab, columns=("time", "text", "words"), show="headings")
        self.history_tree.heading("time", text="Time")
        self.history_tree.heading("text", text="Transcript")
        self.history_tree.heading("words", text="Words")
        self.history_tree.column("time", width=150, stretch=False)
        self.history_tree.column("text", width=560)
        self.history_tree.column("words", width=70, anchor="center", stretch=False)
        self.history_tree.pack(fill="both", expand=True)

    def _build_entries(self, parent, table, first_label, second_label):
        form = ttk.Frame(parent)
        form.pack(fill="x", pady=(0, 12))
        first = ttk.Entry(form, width=25)
        second = ttk.Entry(form)
        first.pack(side="left", padx=(0, 8))
        second.pack(side="left", fill="x", expand=True, padx=(0, 8))
        first.insert(0, first_label)
        second.insert(0, second_label)
        tree = ttk.Treeview(parent, columns=("first", "second"), show="headings")
        tree.heading("first", text=first_label)
        tree.heading("second", text=second_label)
        tree.column("first", width=220)
        tree.pack(fill="both", expand=True)
        self.entry_widgets = getattr(self, "entry_widgets", {})
        self.entry_widgets[table] = (first, second, tree)

        def save():
            left, right = first.get().strip(), second.get().strip()
            if not left or not right or left == first_label or right == second_label:
                messagebox.showwarning("ALTWISP", "Enter both fields.")
                return
            if table == "dictionary":
                self.storage.upsert_dictionary(left, right)
            else:
                self.storage.upsert_snippet(left, right)
            first.delete(0, "end")
            second.delete(0, "end")
            self.refresh()

        def remove():
            selected = tree.selection()
            if selected:
                self.storage.delete_entry(table, int(selected[0]))
                self.refresh()

        ttk.Button(form, text="Add / update", command=save).pack(side="left")
        ttk.Button(form, text="Delete selected", command=remove).pack(side="left", padx=8)

    def _build_settings(self):
        form = ttk.Frame(self.settings_tab)
        form.pack(anchor="nw", fill="x")
        self.setting_vars = {
            "backend": tk.StringVar(value=self.settings.transcription_backend),
            "model": tk.StringVar(value=self.settings.local_model),
            "language": tk.StringVar(value=self.settings.language),
            "style": tk.StringVar(value=self.settings.style),
            "polish": tk.BooleanVar(value=self.settings.polish_enabled),
            "history": tk.BooleanVar(value=self.settings.save_history),
            "autostart": tk.BooleanVar(value=self.settings.launch_at_login),
            "retention": tk.StringVar(value=str(self.settings.auto_delete_hours)),
        }
        rows = [
            ("Transcription", ttk.Combobox(form, textvariable=self.setting_vars["backend"], values=("groq", "local"), state="readonly")),
            ("Local Whisper model", ttk.Combobox(form, textvariable=self.setting_vars["model"], values=("tiny", "base", "small", "medium"), state="readonly")),
            ("Language", ttk.Entry(form, textvariable=self.setting_vars["language"])),
            ("Writing style", ttk.Combobox(form, textvariable=self.setting_vars["style"], values=("neutral", "casual", "formal", "concise"), state="readonly")),
            ("Auto-delete history after hours (0 = never)", ttk.Entry(form, textvariable=self.setting_vars["retention"])),
        ]
        for row, (label, widget) in enumerate(rows):
            ttk.Label(form, text=label).grid(row=row, column=0, sticky="w", padx=(0, 20), pady=8)
            widget.grid(row=row, column=1, sticky="ew", pady=8)
        form.columnconfigure(1, weight=1)
        ttk.Checkbutton(form, text="Polish transcription with AI when a Groq key is available", variable=self.setting_vars["polish"]).grid(row=6, column=0, columnspan=2, sticky="w", pady=8)
        ttk.Checkbutton(form, text="Save transcript history locally", variable=self.setting_vars["history"]).grid(row=7, column=0, columnspan=2, sticky="w", pady=8)
        ttk.Checkbutton(form, text="Launch ALTWISP when I sign in to Windows", variable=self.setting_vars["autostart"]).grid(row=8, column=0, columnspan=2, sticky="w", pady=8)
        ttk.Button(form, text="Save settings", command=self._save_settings).grid(row=9, column=0, sticky="w", pady=18)
        ttk.Button(form, text="Quit ALTWISP", command=self.callbacks["quit"]).grid(row=9, column=1, sticky="e", pady=18)

    def _build_overlay(self):
        self.overlay = tk.Toplevel(self.root)
        self.overlay.overrideredirect(True)
        self.overlay.attributes("-topmost", True)
        transparent = "#010203"
        self.overlay.configure(bg=transparent)
        if sys.platform == "win32":
            self.overlay.attributes("-transparentcolor", transparent)
        width = height = 72
        x = (self.overlay.winfo_screenwidth() - width) // 2
        y = self.overlay.winfo_screenheight() - 128
        self.overlay.geometry(f"{width}x{height}+{x}+{y}")
        canvas = tk.Canvas(self.overlay, width=width, height=height, bg=transparent, highlightthickness=0, borderwidth=0)
        canvas.pack()
        self.overlay_canvas = canvas
        self.orb = ReactiveOrb(canvas, size=width, fps=45)
        self.overlay.update_idletasks()
        self._overlay_hwnd = None
        if sys.platform == "win32":
            import ctypes
            user32 = ctypes.windll.user32
            child = self.overlay.winfo_id()
            self._overlay_hwnd = user32.GetParent(child) or child
            get_style = user32.GetWindowLongW
            set_style = user32.SetWindowLongW
            ex_style = get_style(self._overlay_hwnd, -20)
            # WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE keeps the recorder visible
            # without moving keyboard focus away from the user's text field.
            set_style(self._overlay_hwnd, -20, ex_style | 0x00000080 | 0x08000000)
        self.overlay.withdraw()

    def enqueue(self, callback, *args, **kwargs):
        self.command_queue.put((callback, args, kwargs))

    def _drain_commands(self):
        try:
            while True:
                callback, args, kwargs = self.command_queue.get_nowait()
                callback(*args, **kwargs)
        except queue.Empty:
            pass
        try:
            if self.root.winfo_exists():
                self.root.after(15, self._drain_commands)
        except tk.TclError:
            pass

    def _save_settings(self):
        try:
            retention = max(0, int(self.setting_vars["retention"].get()))
        except ValueError:
            messagebox.showerror("ALTWISP", "History retention must be a whole number of hours.")
            return
        values = {key: var.get() for key, var in self.setting_vars.items()}
        values["retention"] = retention
        try:
            self.callbacks["save_settings"](values)
            self.set_status("Settings saved")
        except Exception as exc:
            messagebox.showerror("ALTWISP", str(exc))

    def _copy_history(self):
        selected = self.history_tree.selection()
        if selected:
            import pyperclip
            pyperclip.copy(self.history_tree.item(selected[0], "values")[1])

    def _export_history(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=(("JSON", "*.json"),))
        if path:
            self.storage.export_json(path)

    def _delete_history(self):
        if messagebox.askyesno("ALTWISP", "Delete all local transcript history?"):
            self.storage.delete_history()
            self.refresh()

    def refresh(self):
        stats = self.storage.stats()
        self.metric_labels["words"].configure(text=f"{stats['words']:,}")
        self.metric_labels["dictations"].configure(text=f"{stats['dictations']:,}")
        minutes = stats["seconds"] / 60
        self.metric_labels["wpm"].configure(text=str(round(stats["words"] / minutes)) if minutes > 0 else "0")
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        for row in self.storage.recent_history():
            timestamp = datetime.fromisoformat(row["created_at"]).astimezone().strftime("%d %b %H:%M")
            self.history_tree.insert("", "end", iid=str(row["id"]), values=(timestamp, row["final_text"], len(row["final_text"].split())))
        for table, (_, _, tree) in self.entry_widgets.items():
            for item in tree.get_children():
                tree.delete(item)
            for row in self.storage.list_entries(table):
                values = (row["spoken"], row["replacement"]) if table == "dictionary" else (row["trigger"], row["expansion"])
                tree.insert("", "end", iid=str(row["id"]), values=values)

    def set_status(self, status, error=False):
        del error
        self.enqueue(self.status_var.set, status)

    def show_recording(self):
        self.enqueue(self._show_recording_now)

    def _show_recording_now(self):
        self.orb.set_mode("listening")
        self.orb.start()
        if self._overlay_hwnd:
            import ctypes
            user32 = ctypes.windll.user32
            user32.ShowWindow(self._overlay_hwnd, 4)  # SW_SHOWNOACTIVATE
            user32.SetWindowPos(self._overlay_hwnd, -1, 0, 0, 0, 0, 0x0013)  # no move/size/activate
        else:
            self.overlay.deiconify()

    def set_overlay_status(self, text):
        mode = "processing" if "process" in text.lower() else "listening"
        self.enqueue(self.orb.set_mode, mode)

    def hide_recording(self):
        self.enqueue(self._hide_recording_now)

    def _hide_recording_now(self):
        self.orb.stop()
        self.overlay.withdraw()

    def update_waveform_from_volume(self, volume):
        # Audio callbacks can arrive much faster than the UI refresh rate. The
        # orb stores only the newest level, preventing a queue backlog and lag.
        self.orb.set_volume(volume)

    def show_dashboard(self):
        self.refresh()
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def hide_dashboard(self):
        self.root.withdraw()

    def show_error(self, title, message):
        self.enqueue(messagebox.showerror, title, message)

    def run(self, background=False):
        self.refresh()
        if background:
            self.root.withdraw()
        self.root.mainloop()
