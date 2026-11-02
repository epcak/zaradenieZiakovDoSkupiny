# MIT License, Copyright (c) 2026 Erik Hadida.
# Pozri súbor LICENSE. Časť kódu a textov vznikla s pomocou AI (Muse Spark)
# a autor ju skontroloval.
"""Rozdelenie žiakov do skupín — desktopová verzia (Tkinter, len štandardná knižnica).

Funkcie (parita s webovou verziou):
- rozdelenie podľa počtu (pôvodná funkcionalita main.py: čísla 1..N),
- menné zoznamy (import TXT/CSV, ukladanie pomenovaných zoznamov, triedenie, deduplikácia),
- nastaviteľná veľkosť textu (aj čísla skupín),
- svetlý / tmavý režim,
- celoplošné zobrazenie výsledku + režim „Zmestiť všetko",
- znova zamiešať, kopírovanie, export TXT / CSV.

Spustenie:  python3 main.py
"""

import csv
import io
import json
import random
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import filedialog, ttk

APP_TITLE = "Rozdelenie žiakov do skupín"
LISTS_FILE = Path(__file__).resolve().parent / "zoznamy.json"

FONT_MIN, FONT_MAX = 14, 48
FIT_MIN, FIT_MAX = 10, 48

THEMES = {
    "light": {
        "bg": "#eef0f2",
        "card": "#ffffff",
        "text": "#23272e",
        "muted": "#616b77",
        "border": "#cfd5dc",
        "primary": "#2c5282",
        "danger": "#a02a2a",
        "input_bg": "#ffffff",
    },
    "dark": {
        "bg": "#15181d",
        "card": "#1e232a",
        "text": "#dfe3e8",
        "muted": "#9aa3ae",
        "border": "#3a424c",
        "primary": "#7fa8d1",
        "danger": "#d98a8a",
        "input_bg": "#12151a",
    },
}


# ----------------------------------------------------------------------------
# Čistá logika (bez GUI — dá sa testovať aj bez displeja)
# ----------------------------------------------------------------------------
def shuffle_items(items):
    """Náhodné premiešanie (Fisher–Yates). Vstup nemení, vracia nový zoznam."""
    pool = list(items)
    random.shuffle(pool)
    return pool


def divide_into_groups(items, num_groups):
    """Premieša položky a rovnomerne ich rozdá do N skupín (round-robin).

    Rovnaká logika ako pôvodný main.py a webová verzia (divideIntoGroups).
    """
    if num_groups < 1:
        raise ValueError("Počet skupín musí byť aspoň 1.")
    mixed = shuffle_items(items)
    groups = [[] for _ in range(num_groups)]
    for idx, item in enumerate(mixed):
        groups[idx % num_groups].append(item)
    return groups


def parse_names(text):
    """Rozdelí text na mená: jeden riadok = jedno meno, prázdne riadky von."""
    return [line.strip() for line in text.splitlines() if line.strip()]


def results_as_text(groups):
    return "\n".join(
        f"Skupina {i + 1}: {', '.join(g) if g else '—'}" for i, g in enumerate(groups)
    )


def results_as_csv(groups):
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";", lineterminator="\n")
    writer.writerow(["skupina", "meno"])
    for i, group in enumerate(groups):
        for name in group:
            writer.writerow([i + 1, name])
    return buf.getvalue()


def load_lists(path=LISTS_FILE):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {k: list(v) for k, v in data.items() if isinstance(v, list)}
    except (OSError, ValueError):
        pass
    return {}


def save_lists(lists, path=LISTS_FILE):
    Path(path).write_text(
        json.dumps(lists, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ----------------------------------------------------------------------------
# Pomocný scrollovateľný rám
# ----------------------------------------------------------------------------
class ScrollableFrame(ttk.Frame):
    def __init__(self, parent, on_resize=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_resize = on_resize
        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0)
        self.scrollbar = ttk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview
        )
        self.inner = ttk.Frame(self.canvas)
        self._win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.inner.bind(
            "<Configure>",
            lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self._bind_wheel(self.canvas)

    def _on_canvas_resize(self, event):
        self.canvas.itemconfigure(self._win, width=event.width)
        if self.on_resize is not None:
            self.on_resize()

    def _bind_wheel(self, widget):
        widget.bind("<Enter>", lambda _e: self._wheel_on())
        widget.bind("<Leave>", lambda _e: self._wheel_off())

    def _wheel_on(self):
        self.canvas.bind_all("<MouseWheel>", self._on_wheel)
        self.canvas.bind_all("<Button-4>", self._on_wheel_up)
        self.canvas.bind_all("<Button-5>", self._on_wheel_down)

    def _wheel_off(self):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_wheel(self, event):
        self.canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")

    def _on_wheel_up(self, _event):
        self.canvas.yview_scroll(-1, "units")

    def _on_wheel_down(self, _event):
        self.canvas.yview_scroll(1, "units")


# ----------------------------------------------------------------------------
# Aplikácia
# ----------------------------------------------------------------------------
class App:
    def __init__(self, root):
        self.root = root
        root.title(APP_TITLE)
        root.geometry("880x760")
        root.minsize(640, 520)

        self.theme_name = "light"
        self.font_size = 20
        self.last_input = None  # (kind, [items])
        self.last_groups = []
        self._result_cards = []
        self._fs_cards = []
        self._results_resize_after = None

        self.font_names = tkfont.Font(family="TkDefaultFont", size=self.font_size)
        self.font_head = tkfont.Font(
            family="TkDefaultFont", size=self._head_size(self.font_size), weight="bold"
        )

        self._canvases = []
        self._texts = []

        self._build_header()
        self._build_tabs()
        self._build_status()
        self._build_results()

        self.saved = load_lists()
        self._refresh_saved_lists()
        self._update_counter()
        self.apply_theme("light")

    # -- veľkosť nadpisu sa odvíja od veľkosti textu (požiadavka) ----------
    @staticmethod
    def _head_size(size):
        return max(9, int(round(size * 0.8)))

    # -- hlavička ----------------------------------------------------------
    def _build_header(self):
        bar = ttk.Frame(self.root, padding=(12, 8))
        bar.pack(fill="x")
        title = ttk.Frame(bar)
        title.pack(side="left")
        ttk.Label(title, text=APP_TITLE, font=("TkDefaultFont", 11, "bold")).pack(
            anchor="w"
        )
        ttk.Label(
            title,
            text="Náhodné žrebovanie podľa počtu alebo menného zoznamu",
            style="Muted.TLabel",
        ).pack(anchor="w")

        ctrl = ttk.Frame(bar)
        ctrl.pack(side="right")
        ttk.Label(ctrl, text="Text:").pack(side="left")
        ttk.Button(ctrl, text="A−", width=3, command=self._font_minus).pack(
            side="left", padx=2
        )
        self.font_var = tk.IntVar(value=self.font_size)
        ttk.Scale(
            ctrl,
            from_=FONT_MIN,
            to=FONT_MAX,
            variable=self.font_var,
            command=lambda v: self.apply_font_size(int(float(v))),
            length=100,
        ).pack(side="left", padx=2)
        ttk.Button(ctrl, text="A+", width=3, command=self._font_plus).pack(
            side="left", padx=2
        )
        self.font_label = ttk.Label(ctrl, text=f"{self.font_size} px", width=6)
        self.font_label.pack(side="left", padx=2)
        self.theme_btn = ttk.Button(
            ctrl, text="Tmavý režim", command=self._toggle_theme
        )
        self.theme_btn.pack(side="left", padx=(8, 0))

    # -- záložky -----------------------------------------------------------
    def _build_tabs(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="x", padx=12, pady=(4, 0))

        # --- tab: podľa počtu (pôvodná funkcionalita) ---
        tab_count = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(tab_count, text="Podľa počtu")
        ttk.Label(
            tab_count,
            text="Zadáš počet žiakov (čísla 1 až N) a počet skupín. "
            "Program čísla náhodne premieša a rozdá do skupín.",
            style="Muted.TLabel",
            wraplength=760,
            justify="left",
        ).pack(anchor="w", pady=(0, 8))
        form = ttk.Frame(tab_count)
        form.pack(fill="x")
        ttk.Label(form, text="Počet žiakov").grid(row=0, column=0, sticky="w")
        self.count_var = tk.StringVar(value="24")
        ttk.Spinbox(form, from_=1, to=1000, textvariable=self.count_var, width=10).grid(
            row=1, column=0, sticky="w", padx=(0, 16)
        )
        ttk.Label(form, text="Počet skupín").grid(row=0, column=1, sticky="w")
        self.groups_var = tk.StringVar(value="4")
        ttk.Spinbox(form, from_=1, to=100, textvariable=self.groups_var, width=10).grid(
            row=1, column=1, sticky="w"
        )
        ttk.Button(
            tab_count, text="Rozdeliť čísla", style="Primary.TButton", command=self._draw_count
        ).pack(anchor="w", pady=(10, 0))

        # --- tab: menný zoznam ---
        tab_names = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(tab_names, text="Menný zoznam")
        ttk.Label(
            tab_names,
            text="Každé meno na nový riadok. Zoznam si môžeš uložiť pod názvom "
            "a neskôr znova použiť.",
            style="Muted.TLabel",
            wraplength=760,
            justify="left",
        ).pack(anchor="w", pady=(0, 8))

        row1 = ttk.Frame(tab_names)
        row1.pack(fill="x")
        ttk.Label(row1, text="Uložené zoznamy").pack(side="left")
        self.saved_var = tk.StringVar()
        self.saved_combo = ttk.Combobox(row1, textvariable=self.saved_var, state="readonly", width=28)
        self.saved_combo.pack(side="left", padx=6)
        ttk.Button(row1, text="Načítať", command=self._load_list).pack(side="left")
        ttk.Button(row1, text="Vymazať", command=self._delete_list).pack(side="left", padx=6)

        row2 = ttk.Frame(tab_names)
        row2.pack(fill="x", pady=(6, 0))
        ttk.Label(row2, text="Názov zoznamu").pack(side="left")
        self.list_name_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.list_name_var, width=30).pack(side="left", padx=6)
        ttk.Button(row2, text="Uložiť zoznam", command=self._save_list).pack(side="left")

        counter_row = ttk.Frame(tab_names)
        counter_row.pack(fill="x", pady=(8, 0))
        ttk.Label(counter_row, text="Mená žiakov").pack(side="left")
        self.counter_label = ttk.Label(counter_row, text="(0)", style="Muted.TLabel")
        self.counter_label.pack(side="left", padx=4)

        self.names_text = tk.Text(tab_names, height=6, wrap="word", undo=True)
        self.names_text.pack(fill="both", expand=True, pady=4)
        self.names_text.bind("<KeyRelease>", lambda _e: self._update_counter())
        self._texts.append(self.names_text)

        row3 = ttk.Frame(tab_names)
        row3.pack(fill="x")
        ttk.Label(row3, text="Počet skupín").grid(row=0, column=0, sticky="w")
        self.groups_names_var = tk.StringVar(value="4")
        ttk.Spinbox(
            row3, from_=1, to=100, textvariable=self.groups_names_var, width=10
        ).grid(row=1, column=0, sticky="w", padx=(0, 16))
        ttk.Label(row3, text="Pridať meno").grid(row=0, column=1, sticky="w")
        add_row = ttk.Frame(row3)
        add_row.grid(row=1, column=1, sticky="w")
        self.single_var = tk.StringVar()
        single_entry = ttk.Entry(add_row, textvariable=self.single_var, width=24)
        single_entry.pack(side="left")
        single_entry.bind("<Return>", lambda _e: self._add_single_name())
        ttk.Button(add_row, text="Pridať", command=self._add_single_name).pack(
            side="left", padx=6
        )

        btns = ttk.Frame(tab_names)
        btns.pack(fill="x", pady=(10, 0))
        ttk.Button(btns, text="Rozdeliť mená", style="Primary.TButton", command=self._draw_names).pack(
            side="left"
        )
        ttk.Button(btns, text="Načítať zo súboru", command=self._import_file).pack(
            side="left", padx=6
        )
        ttk.Button(btns, text="Vyčistiť", command=self._clear_names).pack(side="left")
        ttk.Button(btns, text="Zoradiť", command=self._sort_names).pack(side="left", padx=6)
        ttk.Button(btns, text="Bez duplicít", command=self._dedup_names).pack(side="left")

    # -- stavový riadok ----------------------------------------------------
    def _build_status(self):
        self.status = ttk.Label(
            self.root, text="", style="Danger.TLabel", wraplength=820, justify="left"
        )
        self.status.pack(fill="x", padx=12, pady=(6, 0))

    def _error(self, msg):
        self.status.configure(text=msg or "")

    # -- výsledky ----------------------------------------------------------
    def _build_results(self):
        box = ttk.Frame(self.root, padding=(12, 4, 12, 12))
        box.pack(fill="both", expand=True)
        head = ttk.Frame(box)
        head.pack(fill="x", pady=(0, 6))
        self.results_title = ttk.Label(head, text="Výsledok", font=("TkDefaultFont", 10, "bold"))
        self.results_title.pack(side="left")
        btns = ttk.Frame(head)
        btns.pack(side="right")
        ttk.Button(btns, text="Znova zamiešať", command=self._reshuffle).pack(side="left")
        ttk.Button(btns, text="Kopírovať", command=self._copy).pack(side="left", padx=4)
        ttk.Button(btns, text="TXT", command=self._export_txt).pack(side="left")
        ttk.Button(btns, text="CSV", command=self._export_csv).pack(side="left", padx=4)
        ttk.Button(btns, text="Na celú plochu", command=self.open_fullscreen).pack(side="left")

        self.results_scroll = ScrollableFrame(box, on_resize=self._on_results_resize)
        self.results_scroll.pack(fill="both", expand=True)
        self._canvases.append(self.results_scroll.canvas)
        self.results_hint = ttk.Label(
            self.results_scroll.inner,
            text="Zatiaľ žiadny výsledok. Zadaj vstup a klikni na „Rozdeliť“.",
            style="Muted.TLabel",
        )
        self.results_hint.pack(pady=16)

    def _render_into(self, parent, groups, font_names, font_head):
        """Vykreslí karty skupín do mriežky. Vráti zoznam kariet na prelámovanie."""
        for child in parent.winfo_children():
            child.destroy()
        cards = []
        for i, group in enumerate(groups):
            card = ttk.Frame(parent, style="Card.TFrame", padding=8)
            ttk.Label(
                card,
                text=f"Skupina {i + 1} ({len(group)})",
                style="CardHead.TLabel",
                font=font_head,
            ).pack(anchor="w", pady=(0, 4))
            if not group:
                ttk.Label(
                    card, text="— prázdna —", style="Muted.TLabel", font=font_names
                ).pack(anchor="w")
            for name in group:
                ttk.Label(card, text=name, font=font_names).pack(anchor="w")
            cards.append(card)
        return cards

    @staticmethod
    def _layout_cards(container, canvas, cards):
        """Rozmiestni karty do toľkých stĺpcov, koľko sa vojde vedľa seba."""
        if not cards:
            return
        width = canvas.winfo_width() or container.winfo_width() or 600
        # Viac stĺpcov než kariet nemá zmysel — prázdne stĺpce by robili medzeru vpravo.
        cols = max(1, min(4, width // 260, len(cards)))
        for idx, card in enumerate(cards):
            card.grid(row=idx // cols, column=idx % cols, sticky="nsew", padx=4, pady=4)
        # Nepoužívaným stĺpcom nulujeme váhu, inak by si držali miesto vpravo
        # (zvyšok po predchádzajúcom širšom rozložení).
        for c in range(4):
            if c < cols:
                container.grid_columnconfigure(c, weight=1, uniform="groups", minsize=0)
            else:
                container.grid_columnconfigure(c, weight=0, uniform="", minsize=0)

    def _relayout_results(self):
        if self._result_cards:
            self._layout_cards(
                self.results_scroll.inner, self.results_scroll.canvas, self._result_cards
            )

    def _relayout_fs(self):
        if self.fs_win is not None and self._fs_cards:
            self._layout_cards(self.fs_inner, self.fs_canvas, self._fs_cards)

    def _render_results(self):
        self._result_cards = self._render_into(
            self.results_scroll.inner, self.last_groups, self.font_names, self.font_head
        )
        self.root.update_idletasks()
        self._relayout_results()
        n = len(self.last_groups)
        plural = "skupina" if n == 1 else ("skupiny" if n < 5 else "skupín")
        self.results_title.configure(text=f"Výsledok — {n} {plural}")
        if self.fs_win is not None and self.fs_win.winfo_exists():
            self._fs_cards = self._render_into(
                self.fs_inner, self.last_groups, self.fs_font_names, self.fs_font_head
            )
            self.fs_win.update_idletasks()
            self._relayout_fs()
            self.fs_title.configure(text=f"Výsledok — {n} {plural}")
            if self.fit_mode:
                self.fs_win.after(30, self.apply_fit)

    def _on_results_resize(self):
        if not self._result_cards:
            return
        if self._results_resize_after is not None:
            try:
                self.root.after_cancel(self._results_resize_after)
            except tk.TclError:
                pass
        self._results_resize_after = self.root.after(150, self._relayout_results)

    # -- žrebovanie --------------------------------------------------------
    def _parse_int(self, raw, minimum, maximum):
        try:
            value = int(str(raw).strip())
        except (TypeError, ValueError):
            return None
        return value if minimum <= value <= maximum else None

    def _draw_from_items(self, kind, items, num_groups):
        if not items:
            self._error(
                "Zoznam mien je prázdny."
                if kind == "names"
                else "Počet žiakov musí byť aspoň 1."
            )
            return
        if num_groups is None:
            self._error("Počet skupín musí byť celé číslo od 1 do 100.")
            return
        groups = divide_into_groups(items, num_groups)
        self.last_input = (kind, list(items))
        self.last_groups = groups
        if num_groups > len(items):
            self._error(
                f"Počet skupín ({num_groups}) je väčší ako počet žiakov "
                f"({len(items)}). Posledné skupiny zostanú prázdne."
            )
        else:
            self._error(None)
        self._render_results()

    def _draw_count(self):
        n = self._parse_int(self.count_var.get(), 1, 1000)
        if n is None:
            self._error("Počet žiakov musí byť celé číslo od 1 do 1000.")
            return
        g = self._parse_int(self.groups_var.get(), 1, 100)
        self._draw_from_items("count", [str(i) for i in range(1, n + 1)], g)

    def _draw_names(self):
        g = self._parse_int(self.groups_names_var.get(), 1, 100)
        self._draw_from_items("names", self._current_names(), g)

    def _reshuffle(self):
        if not self.last_input:
            self._error("Zatiaľ nie je čo zamiešať. Najprv klikni na „Rozdeliť“.")
            return
        kind, items = self.last_input
        self._draw_from_items(kind, items, len(self.last_groups))

    # -- mená --------------------------------------------------------------
    def _current_names(self):
        return parse_names(self.names_text.get("1.0", "end"))

    def _set_names(self, names):
        self.names_text.delete("1.0", "end")
        if names:
            self.names_text.insert("1.0", "\n".join(names))
        self._update_counter()

    def _update_counter(self):
        self.counter_label.configure(text=f"({len(self._current_names())})")

    def _add_single_name(self):
        value = self.single_var.get().strip()
        if not value:
            return
        names = self._current_names() + [value]
        self._set_names(names)
        self.single_var.set("")

    def _clear_names(self):
        self._set_names([])

    def _sort_names(self):
        import locale

        try:
            locale.setlocale(locale.LC_COLLATE, "")
            names = sorted(self._current_names(), key=locale.strxfrm)
        except locale.Error:
            names = sorted(self._current_names())
        self._set_names(names)

    def _dedup_names(self):
        seen, out = set(), []
        for name in self._current_names():
            key = name.lower()
            if key not in seen:
                seen.add(key)
                out.append(name)
        self._set_names(out)

    def _import_file(self):
        path = filedialog.askopenfilename(
            title="Načítať menný zoznam",
            filetypes=[("Textové súbory", "*.txt *.csv *.md"), ("Všetky súbory", "*.*")],
        )
        if not path:
            return
        try:
            text = Path(path).read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            self._error(f"Súbor sa nepodarilo načítať: {exc}")
            return
        names = []
        for line in text.splitlines():
            cell = line.split(";")[0].split(",")[0].strip().strip('"')
            if cell:
                names.append(cell)
        self._set_names(names)
        if not self.list_name_var.get().strip():
            self.list_name_var.set(Path(path).stem)
        self._error(None)

    # -- uložené zoznamy ---------------------------------------------------
    def _refresh_saved_lists(self, select=None):
        names = sorted(self.saved.keys())
        self.saved_combo.configure(values=names)
        if select in self.saved:
            self.saved_var.set(select)
        elif names and self.saved_var.get() not in self.saved:
            self.saved_var.set(names[0])
        elif not names:
            self.saved_var.set("")

    def _save_list(self):
        name = self.list_name_var.get().strip()
        items = self._current_names()
        if not name:
            self._error("Najprv zadaj názov zoznamu.")
            return
        if not items:
            self._error("Zoznam je prázdny, nie je čo uložiť.")
            return
        self.saved[name] = items
        try:
            save_lists(self.saved)
        except OSError as exc:
            self._error(f"Zoznam sa nepodarilo uložiť: {exc}")
            return
        self._refresh_saved_lists(select=name)
        self._error(None)

    def _load_list(self):
        name = self.saved_var.get()
        if name not in self.saved:
            self._error("Nie je vybraný žiadny uložený zoznam.")
            return
        self.list_name_var.set(name)
        self._set_names(self.saved[name])
        self._error(None)

    def _delete_list(self):
        name = self.saved_var.get()
        if name not in self.saved:
            return
        del self.saved[name]
        try:
            save_lists(self.saved)
        except OSError as exc:
            self._error(f"Zoznam sa nepodarilo vymazať: {exc}")
            return
        self._refresh_saved_lists()

    # -- písmo a téma ------------------------------------------------------
    def _font_minus(self):
        self.apply_font_size(self.font_size - 2)

    def _font_plus(self):
        self.apply_font_size(self.font_size + 2)

    def apply_font_size(self, px):
        px = max(FONT_MIN, min(FONT_MAX, int(px)))
        self.font_size = px
        self.font_var.set(px)
        self.font_label.configure(text=f"{px} px")
        self.font_names.configure(size=px)
        self.font_head.configure(size=self._head_size(px))

    def _toggle_theme(self):
        self.apply_theme("dark" if self.theme_name == "light" else "light")

    def apply_theme(self, name):
        self.theme_name = name
        t = THEMES[name]
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background=t["card"])
        style.configure("TLabel", background=t["card"], foreground=t["text"])
        style.configure("Muted.TLabel", foreground=t["muted"])
        style.configure("Danger.TLabel", foreground=t["danger"])
        style.configure(
            "TButton", background=t["card"], foreground=t["text"], bordercolor=t["border"]
        )
        style.map("TButton", background=[("active", t["bg"])])
        style.configure(
            "Primary.TButton", background=t["primary"], foreground="#ffffff" if name == "light" else "#101418"
        )
        style.map("Primary.TButton", background=[("active", t["primary"])])
        style.configure(
            "TEntry",
            fieldbackground=t["input_bg"],
            foreground=t["text"],
            bordercolor=t["border"],
        )
        style.configure(
            "TCombobox",
            fieldbackground=t["input_bg"],
            background=t["card"],
            foreground=t["text"],
            bordercolor=t["border"],
        )
        style.configure(
            "TNotebook", background=t["bg"], bordercolor=t["border"]
        )
        style.configure(
            "TNotebook.Tab", background=t["bg"], foreground=t["muted"], padding=(12, 6)
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", t["card"])],
            foreground=[("selected", t["text"])],
        )
        style.configure(
            "TLabelframe", background=t["card"], foreground=t["text"], bordercolor=t["border"]
        )
        style.configure("TLabelframe.Label", background=t["card"], foreground=t["text"])
        style.configure(
            "Card.TFrame", background=t["card"], relief="solid", borderwidth=1
        )
        style.configure(
            "CardHead.TLabel", background=t["bg"], foreground=t["text"], padding=(4, 2)
        )
        style.configure("TSpinbox", fieldbackground=t["input_bg"], foreground=t["text"])
        style.configure("Horizontal.TScale", background=t["card"])
        style.configure("TScrollbar", background=t["card"])
        self.root.configure(background=t["bg"])
        for canvas in list(self._canvases):
            try:
                canvas.configure(background=t["card"])
            except tk.TclError:
                self._canvases.remove(canvas)
        for text in list(self._texts):
            try:
                text.configure(
                    background=t["input_bg"],
                    foreground=t["text"],
                    insertbackground=t["text"],
                    selectbackground=t["primary"],
                    highlightbackground=t["border"],
                )
            except tk.TclError:
                self._texts.remove(text)
        self.theme_btn.configure(
            text="Svetlý režim" if name == "dark" else "Tmavý režim"
        )

    # -- kopírovanie a export ----------------------------------------------
    def _need_result(self):
        if not self.last_groups:
            self._error("Zatiaľ nie je čo exportovať. Najprv klikni na „Rozdeliť“.")
            return False
        return True

    def _copy(self):
        if not self._need_result():
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(results_as_text(self.last_groups))
        self._error(None)

    def _export_txt(self):
        if not self._need_result():
            return
        path = filedialog.asksaveasfilename(
            title="Exportovať ako TXT",
            defaultextension=".txt",
            filetypes=[("Text", "*.txt")],
        )
        if path:
            Path(path).write_text(
                results_as_text(self.last_groups) + "\n", encoding="utf-8"
            )

    def _export_csv(self):
        if not self._need_result():
            return
        path = filedialog.asksaveasfilename(
            title="Exportovať ako CSV",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
        )
        if path:
            Path(path).write_text(results_as_csv(self.last_groups), encoding="utf-8")

    # -- celá plocha -------------------------------------------------------
    def open_fullscreen(self):
        if not self.last_groups:
            self._error("Zatiaľ nie je čo zobraziť. Najprv klikni na „Rozdeliť“.")
            return
        if self.fs_win is not None and self.fs_win.winfo_exists():
            self.fs_win.lift()
            return
        win = tk.Toplevel(self.root)
        win.title(f"{APP_TITLE} — výsledok")
        try:
            win.state("zoomed")
        except tk.TclError:
            try:
                win.attributes("-zoomed", True)
            except tk.TclError:
                win.geometry(f"{win.winfo_screenwidth()}x{win.winfo_screenheight()}+0+0")
        win.configure(background=THEMES[self.theme_name]["bg"])
        self.fs_win = win
        self.fit_mode = False
        self.fs_font_names = tkfont.Font(family="TkDefaultFont", size=self.font_size)
        self.fs_font_head = tkfont.Font(
            family="TkDefaultFont",
            size=self._head_size(self.font_size),
            weight="bold",
        )

        head = ttk.Frame(win, padding=12)
        head.pack(fill="x")
        self.fs_title = ttk.Label(head, text="", font=("TkDefaultFont", 11, "bold"))
        self.fs_title.pack(side="left")
        ctrl = ttk.Frame(head)
        ctrl.pack(side="right")
        ttk.Button(ctrl, text="A−", width=3, command=self._fs_minus).pack(side="left", padx=2)
        ttk.Button(ctrl, text="A+", width=3, command=self._fs_plus).pack(side="left", padx=2)
        self.fs_fit_btn = ttk.Button(ctrl, text="Zmestiť všetko", command=self._toggle_fit)
        self.fs_fit_btn.pack(side="left", padx=(8, 0))
        ttk.Button(ctrl, text="Zavrieť (Esc)", style="Primary.TButton", command=self.close_fullscreen).pack(
            side="left", padx=(8, 0)
        )
        self.fs_note = ttk.Label(win, text="", style="Muted.TLabel", wraplength=1000)
        self.fs_note.pack(fill="x", padx=12)

        scroll = ScrollableFrame(win, padding=12, on_resize=self._on_fs_canvas)
        scroll.pack(fill="both", expand=True)
        self.fs_canvas = scroll.canvas
        self.fs_inner = scroll.inner
        self._canvases.append(scroll.canvas)

        n = len(self.last_groups)
        plural = "skupina" if n == 1 else ("skupiny" if n < 5 else "skupín")
        self.fs_title.configure(text=f"Výsledok — {n} {plural}")
        self._fs_cards = self._render_into(
            self.fs_inner, self.last_groups, self.fs_font_names, self.fs_font_head
        )
        win.update_idletasks()
        self._relayout_fs()
        win.bind("<Escape>", lambda _e: self.close_fullscreen())
        win.protocol("WM_DELETE_WINDOW", self.close_fullscreen)
        self._fs_resize_after = None
        win.focus_force()

    def close_fullscreen(self):
        if self.fs_win is not None and self.fs_win.winfo_exists():
            if self._fs_resize_after is not None:
                try:
                    self.fs_win.after_cancel(self._fs_resize_after)
                except tk.TclError:
                    pass
            self.fs_win.destroy()
        self.fs_win = None
        self._fs_cards = []

    def _on_fs_canvas(self):
        self._relayout_fs()
        if not self.fit_mode or self.fs_win is None:
            return
        if self._fs_resize_after is not None:
            try:
                self.fs_win.after_cancel(self._fs_resize_after)
            except tk.TclError:
                pass
        self._fs_resize_after = self.fs_win.after(150, self.apply_fit)

    def set_fs_font(self, px):
        self.fs_font_names.configure(size=px)
        self.fs_font_head.configure(size=self._head_size(px))

    def _fs_minus(self):
        if self.fit_mode:
            self.set_fit_mode(False)
        self.apply_font_size(self.font_size - 2)
        self.set_fs_font(self.font_size)

    def _fs_plus(self):
        if self.fit_mode:
            self.set_fit_mode(False)
        self.apply_font_size(self.font_size + 2)
        self.set_fs_font(self.font_size)

    def _toggle_fit(self):
        self.set_fit_mode(not self.fit_mode)

    def set_fit_mode(self, on):
        """Režim „Zmestiť všetko": najväčšie písmo, pri ktorom je všetko vidieť naraz."""
        self.fit_mode = on
        try:
            self.fs_fit_btn.configure(style="Primary.TButton" if on else "TButton")
        except tk.TclError:
            pass
        if not on:
            self.fs_note.configure(text="")
            return
        self.apply_fit()

    def apply_fit(self):
        if self.fs_win is None or not self.fs_win.winfo_exists():
            return
        self.fs_win.update_idletasks()
        avail = self.fs_canvas.winfo_height()
        if avail < 50:  # okno sa ešte nestihlo vykresliť — skús znova o chvíľu
            self.fs_win.after(80, self.apply_fit)
            return
        size = min(self.font_size, FIT_MAX)
        self.set_fs_font(size)
        self.fs_win.update_idletasks()
        guard = 0
        while (
            size > FIT_MIN
            and self.fs_inner.winfo_reqheight() > self.fs_canvas.winfo_height()
            and guard < 60
        ):
            size -= 1
            self.set_fs_font(size)
            self.fs_win.update_idletasks()
            guard += 1
        if self.fs_inner.winfo_reqheight() > self.fs_canvas.winfo_height():
            self.fs_note.configure(
                text=f"Ani pri najmenšom písme ({FIT_MIN} px) sa všetko nevojde naraz — "
                "skús menej skupín alebo väčšiu obrazovku."
            )
        else:
            self.fs_note.configure(text="")

    # pólia pre fullscreen (inicializované v open_fullscreen)
    fs_win = None
    fs_inner = None
    fs_canvas = None
    fs_title = None
    fs_note = None
    fs_fit_btn = None
    fit_mode = False
    _fs_resize_after = None


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
