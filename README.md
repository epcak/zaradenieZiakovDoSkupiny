# Rozdelenie žiakov do skupín

Jednoduchá webová pomôcka na náhodné rozdeľovanie žiakov do skupín.
Nástupca pôvodného Python/Tkinter skriptu (`main.py`) — stará funkcionalita je zachovaná.

## Funkcie

- **Podľa počtu (pôvodná funkcionalita):** zadáš počet žiakov (čísla 1 až N) a počet skupín → aplikácia čísla náhodne premieša (Fisher–Yates) a rovnomerne rozdá do skupín (round-robin, rovnaká logika ako starý `main.py`).
- **Menné zoznamy:**
  - textové pole (každé meno na nový riadok), pridávanie po jednom (Enter),
  - import zo súboru `.txt` / `.csv` (aj pretiahnutím súboru do poľa),
  - zoradenie podľa abecedy, odstránenie duplicít, počítadlo mien,
  - **ukladanie viacerých pomenovaných zoznamov** do prehliadača (localStorage) — napr. „5.A“, „krúžok“ — s načítaním a mazaním.
- **Zmena veľkosti textu:** posuvník + tlačidlá A− / A+ (14–48 px), zväčšuje mená aj čísla skupín, voľba sa pamätá.
- **Svetlý / tmavý režim** (pamätá sa, rešpektuje systémové nastavenie).
- **Znova zamiešať** bez nového zadávania, **kopírovanie**, **export TXT / CSV**, **tlač**,
  **zobrazenie výsledku na celú plochu** (vhodné na projektor, zatvára sa tlačidlom alebo Esc),
  s režimom **„Zmestiť všetko“** — automaticky zvolí najväčšie písmo (10–48 px, najviac podľa
  posuvníka), pri ktorom sú všetky skupiny vidieť naraz bez rolovania; ručná zmena písma
  ho vypne, pri zmene okna sa prepočíta.
- Validácia vstupov a slovenské rozhranie. Bez závislostí, funguje offline.

## Spustenie

Stačí otvoriť `index.html` v prehliadači, alebo lokálny server:

```bash
python3 -m http.server 8000
# potom otvor http://localhost:8000
```

## Štruktúra

```
index.html   – rozhranie (taby, formuláre, výsledky)
styles.css   – moderný vzhľad, svetlá/tmavá téma, tlačové štýly
app.js       – logika žrebovania, zoznamy, export
LICENSE      – MIT licencia
```

## Migrácia zo starého Python skriptu

Starý `main.py` (Tkinter, opravená chyba s `Tk()` vs `Toplevel`) je odstránený — jeho logika
(shuffle + cyklické `skup = 1..N`) je 1:1 prenesená do `divideIntoGroups()` v `app.js`
a je dostupná v tabe „Podľa počtu“.

## Licencia

MIT — pozri súbor [LICENSE](LICENSE). Copyright (c) 2026 Erik Hadida.

## Poznámka o použití AI

Časť kódu a textov v tomto projekte vznikla s pomocou AI (Muse Spark 1.3, agent OpenCode).
Autor prevzal zodpovednosť za výsledok: kód prešiel, logiku žrebovania overil
(Fisher–Yates + rovnomerné rozdanie) a vzhľad upravil do jednoduchej pracovnej podoby.
