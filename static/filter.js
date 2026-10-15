// Filter und Seitenblätterung für Karten und Tabelle. Ohne JavaScript bleiben Gruppen-Links und Ansichten nutzbar,
// alle Anzeigen stehen dann untereinander.
(() => {
  // Filterbereich: ab 992 px (KERN-Breakpoint lg) offen und ohne Kopf, darunter eingeklappt. Ohne JavaScript offen.
  const panel = document.getElementById("panel");
  if (panel) {
    const breit = matchMedia("(min-width: 992px)");
      const werkzeuge = document.getElementById("werkzeuge");
    // Ansicht und Sortierung: breit oben rechts im Seitenkopf, schmal direkt hinter „Gruppe und Filter“ (DOM verschieben,
    // damit die Reihenfolge für Tastatur und Screenreader der sichtbaren entspricht)
    const heim = werkzeuge && werkzeuge.parentNode, danach = werkzeuge && werkzeuge.nextSibling;
    const setzen = () => {
      if (werkzeuge) {
        if (breit.matches && werkzeuge.parentNode !== heim) heim.insertBefore(werkzeuge, danach);
        else if (!breit.matches && werkzeuge.previousElementSibling !== panel) panel.after(werkzeuge);
      }
      panel.open = breit.matches;
      if (werkzeuge) { werkzeuge.open = breit.matches; werkzeuge.classList.add("fj-bereit"); }
    };
    breit.addEventListener("change", setzen);
    setzen();
    panel.classList.add("fj-bereit");
  }

  const form = document.getElementById("filter");
  const liste = document.getElementById("liste");
  if (!form || !liste) return;
  const container = liste.tBodies ? liste.tBodies[0] : liste;
  const eintraege = [...container.querySelectorAll(".fj-treffer")];
  const proSeite = Number(liste.dataset.proSeite) || 24;
  const anzahl = document.getElementById("anzahl");
  const status = document.getElementById("status");
  const titel = document.getElementById("liste-titel");
  const seitenNav = document.getElementById("seiten");
  const leer = document.getElementById("leer");
  const lohnFeld = form.elements.lohn;
  const lohnWert = document.getElementById("f-lohn-wert");
  const euro = (n) => n.toFixed(2).replace(".", ",") + " €";
  let seite = 1;
  let passend = [];
  let timer;
  let bereich = "";  // gewählte Kategorie aus den Chips über der Liste, leer = alle

  function filtern() {
    const was = form.elements.was.value.trim().toLowerCase();
    const lohn = Number(lohnFeld.value);
    lohnWert.textContent = lohn ? "ab " + euro(lohn) : "egal";
    lohnFeld.style.setProperty("--anteil", (lohn / Number(lohnFeld.max || 20)) * 100 + "%");  // gefüllte Spur bis zum Knopf
    const nurLohn = form.elements.nur_lohn.checked;
    const ohneWarnung = form.elements.ohne_warnung.checked;
    const bis = form.elements.start.value;  // natives Datumsfeld liefert JJJJ-MM-TT oder leer
    const k = { punkte: (d) => Number(d.punkte), lohn: (d) => Number(d.lohn), datum: (d) => d.datum }[form.elements.sortierung.value];

    passend = eintraege.filter((e) => {
      const d = e.dataset;
      return (!was || d.text.includes(was))
        && (!bereich || d.kat === bereich)
        && (!lohn || Number(d.lohn) >= lohn)
        && (!nurLohn || d.hatlohn === "1")
        && (!ohneWarnung || d.warnung === "0")
        && (!bis || !d.eintritt || d.eintritt <= bis);
    });
    if (chips) for (const c of chips.querySelectorAll(".fj-chip")) {
      c.setAttribute("aria-pressed", String((c.dataset.kat || "") === bereich));
    }
    passend.sort((a, b) => (k(b.dataset) > k(a.dataset) ? 1 : k(b.dataset) < k(a.dataset) ? -1 : 0));
    passend.forEach((e) => container.appendChild(e));   // Reihenfolge im DOM = Sortierung
    seite = 1;
    anzeigen();
    anzahl.textContent = passend.length;
    leer.hidden = passend.length > 0;
    clearTimeout(timer);
    timer = setTimeout(() => { status.textContent = `${passend.length} Anzeigen gefunden`; }, 600);
  }

  function anzeigen() {
    const seiten = Math.max(1, Math.ceil(passend.length / proSeite));
    seite = Math.min(seite, seiten);
    const von = (seite - 1) * proSeite;
    const sichtbar = new Set(passend.slice(von, von + proSeite));
    for (const e of eintraege) e.hidden = !sichtbar.has(e);
    blaettern(seiten);
  }

  function knopf(text, ziel, { aktuell = false, beschriftung = "" } = {}) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "fj-seiten__link";
    b.textContent = text;
    b.dataset.seite = ziel;
    if (beschriftung) b.setAttribute("aria-label", beschriftung);
    if (aktuell) b.setAttribute("aria-current", "page");
    return b;
  }

  function blaettern(seiten) {
    seitenNav.hidden = seiten < 2;
    seitenNav.replaceChildren();
    if (seiten < 2) return;
    // Erste, letzte und Nachbarn der aktuellen Seite, dazwischen Auslassung
    const nummern = [...new Set([1, seite - 1, seite, seite + 1, seiten])].filter((n) => n >= 1 && n <= seiten).sort((a, b) => a - b);
    const ul = document.createElement("ul");
    ul.className = "fj-seiten__liste";
    if (seite > 1) seitenNav.append(knopf("‹ Zurück", seite - 1));
    nummern.forEach((n, i) => {
      if (i && n - nummern[i - 1] > 1) {
        const l = document.createElement("li");
        l.className = "fj-seiten__luecke";
        l.textContent = "…";
        l.setAttribute("aria-hidden", "true");
        ul.append(l);
      }
      const li = document.createElement("li");
      li.append(knopf(String(n), n, { aktuell: n === seite, beschriftung: `Seite ${n} von ${seiten}` }));
      ul.append(li);
    });
    seitenNav.append(ul);
    if (seite < seiten) seitenNav.append(knopf("Weiter ›", seite + 1));
  }

  seitenNav.addEventListener("click", (ev) => {
    const b = ev.target.closest("button[data-seite]");
    if (!b) return;
    seite = Number(b.dataset.seite);
    anzeigen();
    titel.setAttribute("tabindex", "-1");
    titel.focus();
    titel.scrollIntoView({ block: "start" });
  });

  // Bereich über die Chips: ein Tipp wählt genau diesen Bereich, noch ein Tipp oder „Alle“ hebt die Wahl auf
  const chips = document.getElementById("chips");
  if (chips) {
    chips.hidden = false;
    // Zeigt per Klasse, ob rechts noch Chips folgen (Verlauf am Rand, nur auf dem Handy sichtbar)
    const rand = () => chips.classList.toggle("fj-chips--ende", chips.scrollLeft + chips.clientWidth >= chips.scrollWidth - 2);
    chips.addEventListener("scroll", rand, { passive: true });
    addEventListener("resize", rand);
    rand();
    chips.addEventListener("click", (ev) => {
      const c = ev.target.closest(".fj-chip");
      if (!c) return;
      const nurDieser = c.dataset.kat && c.getAttribute("aria-pressed") !== "true";
      bereich = nurDieser ? c.dataset.kat : "";
      filtern();
    });
  }
  // Wechsel Karten/Tabelle: Die andere Ansicht ist eine eigene Seite. Mit JavaScript behält sie die Scrollposition, statt zum
  // Anker zu springen (der Anker bleibt für die Fassung ohne JavaScript). Gemerkt nur für diesen einen Seitenwechsel.
  for (const a of document.querySelectorAll(".fj-ansicht a[href]")) {
    a.addEventListener("click", () => {
      try { sessionStorage.setItem("fj-stelle", String(Math.round(scrollY))); } catch (e) { return; }
      a.setAttribute("href", a.getAttribute("href").split("#")[0]);
    });
  }
  form.hidden = false;
  document.getElementById("sortierung").hidden = false;
  document.getElementById("f-sortierung").addEventListener("change", filtern);  // steht außerhalb des Formulars
  form.addEventListener("input", filtern);
  form.addEventListener("submit", (ev) => { ev.preventDefault(); filtern(); });
  form.addEventListener("reset", () => { bereich = ""; setTimeout(filtern); });
  filtern();
})();
