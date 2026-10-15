// Kopfzeile wie auf der Startseite der Projektschau für KERN: haftet oben, verschwindet beim Runterscrollen, erscheint
// nach 120 px Hochscrollen am Stück, ganz oben immer und sobald sie den Tastaturfokus bekommt. Nach einem Sprung zu einem Abschnitt
// bleibt sie kurz weg, sonst läge sie über der Überschrift. Ohne JavaScript haftet sie einfach.
(() => {
  const kopf = document.querySelector(".fj-header");
  const h = document.documentElement;
  if (!kopf) return;
  let zuletzt = scrollY, wende = scrollY, wartet = false, sprung = 0, ruhe = 0;
  const chips = document.querySelector(".fj-chips-rahmen");   // haftet unter der Kopfzeile; zählt für den Abstand beim Fokus (scroll-padding)
  const messe = () => {
    h.style.setProperty("--kopf-hoehe", kopf.offsetHeight + "px");
    h.style.setProperty("--chips-hoehe", (chips ? chips.offsetHeight : 0) + "px");
  };
  function pruefe() {
    const y = scrollY;
    wartet = false;
    if (ruhe > Date.now()) { zuletzt = y; return; }
    if (Math.abs(y - zuletzt) < 6) return;
    if (y > zuletzt) wende = y;
    if (y <= kopf.offsetHeight) h.classList.remove("kopf-weg");
    else if (y > zuletzt || sprung > Date.now()) h.classList.add("kopf-weg");
    else if (wende - y > 120) h.classList.remove("kopf-weg");
    zuletzt = y;
  }
  const merkeSprung = () => { sprung = Date.now() + 1500; if (scrollY > kopf.offsetHeight) h.classList.add("kopf-weg"); };
  addEventListener("hashchange", merkeSprung);
  document.addEventListener("click", (e) => { if (e.target.closest?.('a[href^="#"]')) merkeSprung(); });
  if (location.hash) merkeSprung();
  messe();
  // Höhe neu messen, wenn sich Fensterbreite oder Schrift ändern
  const ro = new ResizeObserver(messe); ro.observe(kopf); if (chips) ro.observe(chips);
  addEventListener("scroll", () => { if (!wartet) { wartet = true; requestAnimationFrame(pruefe); } }, { passive: true });
  kopf.addEventListener("focusin", () => h.classList.remove("kopf-weg"));
  // Filter, Blättern und Sortierung ändern die Seitenhöhe und damit die Scrollposition; das ist kein Hochscrollen
  document.addEventListener("click", (e) => { if (e.target.closest?.("#filter, #seiten, #sortierung, .fj-panel")) ruhe = Date.now() + 900; }, true);
  document.addEventListener("input", () => { ruhe = Date.now() + 900; }, true);
  // Klick in der Kopfzeile (Farbschema): sie bleibt stehen, damit der Wechsel zu sehen ist
  kopf.addEventListener("click", () => { ruhe = Date.now() + 1200; h.classList.remove("kopf-weg"); }, true);
})();
