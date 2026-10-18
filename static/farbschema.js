// Hell/Dunkel: läuft im <head>, damit nichts aufblitzt.
// Reihenfolge: Adresse (?theme=), gespeicherte Wahl (localStorage, kein Cookie), Systemeinstellung.
// Die Adresse braucht es, weil Safari bei file:// jeder Datei einen eigenen Speicher gibt: Die Wahl wird deshalb
// zusätzlich an alle internen Links gehängt und überlebt so jeden Seitenwechsel (wie bei der Projektschau).
// Ohne JavaScript folgt KERN von selbst prefers-color-scheme, der Schalter bleibt verborgen.
(() => {
  const html = document.documentElement;
  const SCHLUESSEL = "fj-farbschema";
  const gueltig = (t) => t === "dark" || t === "light";
  let wahl = new URLSearchParams(location.search).get("theme");
  if (!gueltig(wahl)) {
    try { wahl = localStorage.getItem(SCHLUESSEL); } catch (e) { wahl = null; }
  }
  const gewaehlt = gueltig(wahl);
  if (!gewaehlt) wahl = matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  html.setAttribute("data-kern-theme", wahl);
  html.classList.add("js");
  // Nach dem Wechsel Karten/Tabelle an dieselbe Stelle (gesetzt in filter.js), ohne weiches Scrollen
  try {
    const stelle = sessionStorage.getItem("fj-stelle");
    if (stelle !== null) {
      sessionStorage.removeItem("fj-stelle");
      addEventListener("DOMContentLoaded", () => scrollTo({ top: Number(stelle), behavior: "instant" }));
    }
  } catch (e) { /* Speicher gesperrt: dann eben oben */ }  // erlaubt dem CSS, den Zustand nach filter.js vorwegzunehmen: kein Sprung beim Laden

  function merken(t) {
    try { localStorage.setItem(SCHLUESSEL, t); } catch (e) { /* Speicher gesperrt: Links tragen die Wahl */ }
    for (const a of document.querySelectorAll("a[href]")) {
      const href = a.getAttribute("href");
      if (/^[a-z0-9-]+\.html(\?|#|$)/i.test(href)) {   // nur eigene Seiten, keine externen Links
        const [pfad, anker = ""] = href.split("#");
        const u = new URL(pfad, "http://x/");
        u.searchParams.set("theme", t);
        a.setAttribute("href", u.pathname.slice(1) + u.search + (anker ? "#" + anker : ""));
      }
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    if (gewaehlt) merken(wahl);
    const knopf = document.getElementById("farbschema");
    if (!knopf) return;
    const setzen = (t) => {
      html.setAttribute("data-kern-theme", t);
      knopf.setAttribute("aria-checked", String(t === "dark"));
    };
    setzen(html.getAttribute("data-kern-theme"));
    knopf.hidden = false;
    knopf.addEventListener("click", () => {
      const neu = html.getAttribute("data-kern-theme") === "dark" ? "light" : "dark";
      setzen(neu);
      merken(neu);
    });
  });
})();
