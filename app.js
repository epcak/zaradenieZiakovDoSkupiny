"use strict";

/* Rozdelenie žiakov do skupín — logika (MIT, Erik Hadida) */

// ---------- Pomocné ----------
const $ = (id) => document.getElementById(id);

function showError(msg) {
  const box = $("errorBox");
  if (!msg) {
    box.classList.add("hidden");
    box.textContent = "";
    return;
  }
  box.textContent = msg;
  box.classList.remove("hidden");
}

/** Kryptograficky silnejšie náhodné miešanie (Fisher–Yates). */
function shuffle(arr) {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) {
    let j;
    if (window.crypto && window.crypto.getRandomValues) {
      const buf = new Uint32Array(1);
      window.crypto.getRandomValues(buf);
      j = buf[0] % (i + 1);
    } else {
      j = Math.floor(Math.random() * (i + 1));
    }
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

/**
 * Rovnomerné rozdanie premiešaných položiek do N skupín (round-robin).
 * Zachováva pôvodnú logiku main.py: shuffle + cyklické priraďovanie 1..N.
 */
function divideIntoGroups(items, numGroups) {
  const mixed = shuffle(items);
  const groups = Array.from({ length: numGroups }, () => []);
  mixed.forEach((item, idx) => groups[idx % numGroups].push(item));
  return groups;
}

function parseNames(text) {
  return text
    .split(/\r?\n/)
    .map((s) => s.trim())
    .filter((s) => s.length > 0);
}

// ---------- Stav ----------
let lastInput = null; // { kind: 'count'|'names', items: string[] }
let lastGroups = [];

// ---------- Taby ----------
function setMode(mode) {
  const isCount = mode === "count";
  $("tabCount").classList.toggle("active", isCount);
  $("tabNames").classList.toggle("active", !isCount);
  $("tabCount").setAttribute("aria-selected", String(isCount));
  $("tabNames").setAttribute("aria-selected", String(!isCount));
  $("panelCount").classList.toggle("hidden", !isCount);
  $("panelNames").classList.toggle("hidden", isCount);
  showError(null);
}
$("tabCount").addEventListener("click", () => setMode("count"));
$("tabNames").addEventListener("click", () => setMode("names"));

// ---------- Veľkosť textu ----------
function applyFontSize(px) {
  const v = Math.min(48, Math.max(14, Number(px) || 20));
  document.documentElement.style.setProperty("--result-font-size", v + "px");
  $("fontSize").value = String(v);
  $("fontValue").textContent = v + " px";
  try {
    localStorage.setItem("skupiny-font-size", String(v));
  } catch (_) {}
}
$("fontSize").addEventListener("input", (e) => applyFontSize(e.target.value));
$("fontMinus").addEventListener("click", () => applyFontSize(Number($("fontSize").value) - 2));
$("fontPlus").addEventListener("click", () => applyFontSize(Number($("fontSize").value) + 2));

// ---------- Tmavý / svetlý režim ----------
function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  $("themeToggle").textContent = theme === "dark" ? "Svetlý režim" : "Tmavý režim";
  try {
    localStorage.setItem("skupiny-theme", theme);
  } catch (_) {}
}
$("themeToggle").addEventListener("click", () => {
  const cur = document.documentElement.getAttribute("data-theme") || "light";
  applyTheme(cur === "dark" ? "light" : "dark");
});

// ---------- Výsledky ----------
function buildGroupCard(g, i) {
  const card = document.createElement("div");
  card.className = "group-card";
  const h = document.createElement("h3");
  h.textContent = `Skupina ${i + 1} (${g.length})`;
  card.appendChild(h);
  const ul = document.createElement("ul");
  if (g.length === 0) {
    const li = document.createElement("li");
    li.className = "empty";
    li.textContent = "— prázdna —";
    ul.appendChild(li);
  } else {
    g.forEach((name) => {
      const li = document.createElement("li");
      li.textContent = name;
      ul.appendChild(li);
    });
  }
  card.appendChild(ul);
  return card;
}

function renderGroups(groups) {
  lastGroups = groups;
  const grid = $("resultsGrid");
  grid.innerHTML = "";
  groups.forEach((g, i) => grid.appendChild(buildGroupCard(g, i)));
  $("resultsSection").classList.remove("hidden");
  const title = `Výsledok — ${groups.length} ${groups.length === 1 ? "skupina" : groups.length < 5 ? "skupiny" : "skupín"}`;
  $("resultsTitle").textContent = title;
  $("fsTitle").textContent = title;
  // Ak je otvorený celoplošný náhľad, prekresli aj ten (napr. po "Znova zamiešať").
  if (!$("fsOverlay").classList.contains("hidden")) {
    const fsGrid = $("fsGrid");
    fsGrid.innerHTML = "";
    groups.forEach((g, i) => fsGrid.appendChild(buildGroupCard(g, i)));
    if (fitMode) requestAnimationFrame(applyFit);
  }
}

function validateGroupCount(n, total) {
  if (!Number.isInteger(n) || n < 1) return "Počet skupín musí byť celé číslo ≥ 1.";
  if (n > total) return `Počet skupín (${n}) je väčší ako počet žiakov (${total}). Posledné skupiny zostanú prázdne — pokračujem aj tak.`;
  return null;
}

function drawFromItems(kind, items, numGroups) {
  if (items.length === 0) {
    showError(kind === "names" ? "Zoznam mien je prázdny." : "Počet žiakov musí byť aspoň 1.");
    return;
  }
  const warn = validateGroupCount(numGroups, items.length);
  const groups = divideIntoGroups(items, numGroups);
  lastInput = { kind, items: items.slice() };
  renderGroups(groups);
  showError(warn); // null => skryje, text => len varovanie (výsledok sa zobrazí aj tak)
}

// Pôvodná funkcionalita: čísla 1..N
$("drawCount").addEventListener("click", () => {
  const n = Number($("studentCount").value);
  const g = Number($("groupCount").value);
  if (!Number.isInteger(n) || n < 1 || n > 1000) {
    showError("Počet žiakov musí byť celé číslo od 1 do 1000.");
    return;
  }
  if (!Number.isInteger(g) || g < 1 || g > 100) {
    showError("Počet skupín musí byť celé číslo od 1 do 100.");
    return;
  }
  const items = Array.from({ length: n }, (_, i) => String(i + 1));
  drawFromItems("count", items, g);
});

// Menný zoznam
function currentNames() {
  return parseNames($("namesInput").value);
}
function refreshCounter() {
  $("nameCounter").textContent = `(${currentNames().length})`;
}
$("namesInput").addEventListener("input", refreshCounter);

$("drawNames").addEventListener("click", () => {
  const items = currentNames();
  const g = Number($("groupCountNames").value);
  if (!Number.isInteger(g) || g < 1 || g > 100) {
    showError("Počet skupín musí byť celé číslo od 1 do 100.");
    return;
  }
  drawFromItems("names", items, g);
});

$("reshuffle").addEventListener("click", () => {
  if (!lastInput) {
    showError("Zatiaľ nie je čo zamiešať. Najprv klikni na „Rozdeliť“.");
    return;
  }
  const g = lastGroups.length;
  renderGroups(divideIntoGroups(lastInput.items, g));
  showError(null);
});

// Pridanie jedného mena
function addSingleName() {
  const inp = $("singleName");
  const v = inp.value.trim();
  if (!v) return;
  const ta = $("namesInput");
  ta.value = ta.value.trim() ? ta.value.replace(/\s+$/, "") + "\n" + v : v;
  inp.value = "";
  inp.focus();
  refreshCounter();
}
$("addName").addEventListener("click", addSingleName);
$("singleName").addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    addSingleName();
  }
});

// Úpravy zoznamu
$("clearNames").addEventListener("click", () => {
  $("namesInput").value = "";
  refreshCounter();
});
$("sortNames").addEventListener("click", () => {
  const items = currentNames().sort((a, b) => a.localeCompare(b, "sk"));
  $("namesInput").value = items.join("\n");
  refreshCounter();
});
$("dedupNames").addEventListener("click", () => {
  const seen = new Set();
  const out = [];
  for (const n of currentNames()) {
    const key = n.toLowerCase();
    if (!seen.has(key)) {
      seen.add(key);
      out.push(n);
    }
  }
  $("namesInput").value = out.join("\n");
  refreshCounter();
});

// Import zo súboru + drag & drop
$("fileInput").addEventListener("change", (e) => {
  const f = e.target.files && e.target.files[0];
  if (f) readNamesFile(f);
  e.target.value = "";
});
function readNamesFile(file) {
  const reader = new FileReader();
  reader.onload = () => {
    const text = String(reader.result || "");
    // CSV: berieme prvý stĺpec, prípadne celý riadok po čiarku/bodkočiarku
    const lines = text
      .split(/\r?\n/)
      .map((l) => l.split(/[;,]/)[0].trim().replace(/^"|"$/g, ""))
      .filter(Boolean);
    const ta = $("namesInput");
    ta.value = lines.join("\n");
    const base = file.name.replace(/\.[^.]+$/, "");
    if (!$("listName").value.trim()) $("listName").value = base;
    refreshCounter();
    showError(null);
  };
  reader.readAsText(file, "utf-8");
}
["dragover", "dragenter"].forEach((ev) =>
  $("namesInput").addEventListener(ev, (e) => e.preventDefault())
);
$("namesInput").addEventListener("drop", (e) => {
  e.preventDefault();
  const f = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
  if (f) readNamesFile(f);
});

// ---------- Uložené menné zoznamy (localStorage) ----------
const LS_KEY = "skupiny-zoznamy-v1";

function getSavedLists() {
  try {
    return JSON.parse(localStorage.getItem(LS_KEY) || "{}");
  } catch (_) {
    return {};
  }
}
function setSavedLists(obj) {
  localStorage.setItem(LS_KEY, JSON.stringify(obj));
}
function refreshSavedLists(selectName) {
  const lists = getSavedLists();
  const sel = $("savedLists");
  const names = Object.keys(lists).sort((a, b) => a.localeCompare(b, "sk"));
  sel.innerHTML = "";
  if (names.length === 0) {
    const o = document.createElement("option");
    o.value = "";
    o.textContent = "— zatiaľ žiadne uložené zoznamy —";
    sel.appendChild(o);
    return;
  }
  names.forEach((n) => {
    const o = document.createElement("option");
    o.value = n;
    o.textContent = `${n} (${lists[n].length})`;
    sel.appendChild(o);
  });
  if (selectName && lists[selectName]) sel.value = selectName;
}
$("saveList").addEventListener("click", () => {
  const name = $("listName").value.trim();
  const items = currentNames();
  if (!name) {
    showError("Najprv zadaj názov zoznamu.");
    return;
  }
  if (items.length === 0) {
    showError("Zoznam je prázdny, nie je čo uložiť.");
    return;
  }
  const lists = getSavedLists();
  lists[name] = items;
  setSavedLists(lists);
  refreshSavedLists(name);
  showError(null);
});
$("loadList").addEventListener("click", () => {
  const sel = $("savedLists").value;
  if (!sel) {
    showError("Nie je vybraný žiadny uložený zoznam.");
    return;
  }
  const lists = getSavedLists();
  if (!lists[sel]) {
    showError("Zoznam sa nenašiel.");
    return;
  }
  $("namesInput").value = lists[sel].join("\n");
  $("listName").value = sel;
  refreshCounter();
  showError(null);
});
$("deleteList").addEventListener("click", () => {
  const sel = $("savedLists").value;
  if (!sel) return;
  const lists = getSavedLists();
  delete lists[sel];
  setSavedLists(lists);
  refreshSavedLists();
});

// ---------- Kopírovanie / export ----------
function resultsAsText() {
  return lastGroups
    .map((g, i) => `Skupina ${i + 1}: ${g.length ? g.join(", ") : "—"}`)
    .join("\n");
}
$("copyResult").addEventListener("click", async () => {
  if (!lastGroups.length) return;
  try {
    await navigator.clipboard.writeText(resultsAsText());
    showError(null);
  } catch (_) {
    showError("Kopírovanie do schránky sa nepodarilo (prehliadač to zamietol).");
  }
});
function download(filename, content, mime) {
  const blob = new Blob([content], { type: mime });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    URL.revokeObjectURL(a.href);
    a.remove();
  }, 500);
}
$("exportTxt").addEventListener("click", () => {
  if (!lastGroups.length) return;
  download("skupiny.txt", resultsAsText() + "\n", "text/plain;charset=utf-8");
});
$("exportCsv").addEventListener("click", () => {
  if (!lastGroups.length) return;
  const rows = ["skupina;meno"];
  lastGroups.forEach((g, i) =>
    g.forEach((m) => rows.push(`${i + 1};"${m.replace(/"/g, '""')}"`))
  );
  download("skupiny.csv", rows.join("\n") + "\n", "text/csv;charset=utf-8");
});
$("printResult").addEventListener("click", () => window.print());

// ---------- Celoplošné zobrazenie výsledku ----------
function openFullscreen() {
  if (!lastGroups.length) {
    showError("Zatiaľ nie je čo zobraziť. Najprv klikni na „Rozdeliť“.");
    return;
  }
  const grid = $("fsGrid");
  grid.innerHTML = "";
  lastGroups.forEach((g, i) => grid.appendChild(buildGroupCard(g, i)));
  $("fsOverlay").classList.remove("hidden");
  document.body.style.overflow = "hidden";
  $("fsClose").focus();
  if (fitMode) requestAnimationFrame(applyFit);
  // Skúsime aj skutočný fullscreen prehliadača, tiché zlyhanie nevadí (prekryv funguje aj tak).
  try {
    const el = $("fsOverlay");
    if (el.requestFullscreen && !document.fullscreenElement) {
      const p = el.requestFullscreen();
      if (p && p.catch) p.catch(() => {});
    }
  } catch (_) {}
}
function closeFullscreen() {
  $("fsOverlay").classList.add("hidden");
  document.body.style.overflow = "";
  try {
    if (document.fullscreenElement) {
      const p = document.exitFullscreen();
      if (p && p.catch) p.catch(() => {});
    }
  } catch (_) {}
}
$("fullscreenBtn").addEventListener("click", openFullscreen);
$("fsClose").addEventListener("click", closeFullscreen);

// Ručná zmena písma má prednosť — fit režim sa vypne.
$("fsMinus").addEventListener("click", () => {
  if (fitMode) setFitMode(false);
  applyFontSize(Number($("fontSize").value) - 2);
});
$("fsPlus").addEventListener("click", () => {
  if (fitMode) setFitMode(false);
  applyFontSize(Number($("fontSize").value) + 2);
});

// ---------- "Zmestiť všetko" — všetko viditeľné naraz bez rolovania ----------
let fitMode = false;
const FIT_MIN = 10; // px, menšie písmo už nedáva zmysel
const FIT_MAX = 48; // px, strop posuvníka

function setGridFont(px) {
  $("fsGrid").style.setProperty("--result-font-size", px + "px");
}
function clearGridFont() {
  $("fsGrid").style.removeProperty("--result-font-size");
}

/* Nájde najväčšie písmo v medziach FIT_MIN–FIT_MAX (max. aktuálny posuvník),
   pri ktorom sa celý obsah prekryvu vojde bez rolovania. */
function applyFit() {
  const overlay = $("fsOverlay");
  if (overlay.classList.contains("hidden")) return;
  overlay.classList.add("fit");
  let size = Math.min(Number($("fontSize").value) || 20, FIT_MAX);
  setGridFont(size);
  let guard = 0;
  while (size > FIT_MIN && overlay.scrollHeight > overlay.clientHeight + 1 && guard++ < 60) {
    size -= 1;
    setGridFont(size);
  }
  const note = $("fsFitNote");
  if (overlay.scrollHeight > overlay.clientHeight + 1) {
    note.textContent = `Ani pri najmenšom písme (${FIT_MIN} px) sa všetko nevojde naraz — skús menej skupín alebo väčšiu obrazovku.`;
    note.classList.remove("hidden");
  } else {
    note.textContent = "";
    note.classList.add("hidden");
  }
}

function setFitMode(on) {
  fitMode = on;
  const btn = $("fsFit");
  btn.classList.toggle("on", on);
  btn.setAttribute("aria-pressed", String(on));
  if (on) {
    applyFit();
  } else {
    $("fsOverlay").classList.remove("fit");
    clearGridFont();
    $("fsFitNote").textContent = "";
    $("fsFitNote").classList.add("hidden");
  }
}
$("fsFit").addEventListener("click", () => setFitMode(!fitMode));

// Pri zmene veľkosti okna fit prepočítaj (ak je zapnutý a prekryv je otvorený).
let resizeQueued = false;
window.addEventListener("resize", () => {
  if (!fitMode || $("fsOverlay").classList.contains("hidden") || resizeQueued) return;
  resizeQueued = true;
  requestAnimationFrame(() => {
    resizeQueued = false;
    applyFit();
  });
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && !$("fsOverlay").classList.contains("hidden")) {
    closeFullscreen();
  }
});

// ---------- Inicializácia ----------
(function init() {
  let theme = "light";
  let fontSize = 20;
  try {
    theme = localStorage.getItem("skupiny-theme") || "light";
    fontSize = Number(localStorage.getItem("skupiny-font-size")) || 20;
    if (window.matchMedia && !localStorage.getItem("skupiny-theme")) {
      theme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }
  } catch (_) {}
  applyTheme(theme);
  applyFontSize(fontSize);
  refreshSavedLists();
  refreshCounter();
})();
