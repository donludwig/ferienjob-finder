// Kopierknopf unter den Anweisungen der Dokumentation (wie in der Projektschau-Doku); ohne JavaScript bleibt er verborgen
document.querySelectorAll(".fj-kopieren").forEach((k) => {
  k.hidden = false;
  const label = k.querySelector(".kern-label");
  k.addEventListener("click", () => {
    navigator.clipboard.writeText(k.parentNode.querySelector("pre").textContent).then(() => {
      label.textContent = k.dataset.kopiert;
      setTimeout(() => { label.textContent = ""; }, 1500);
    });
  });
});

// Inhaltsverzeichnis: den Abschnitt markieren, der gerade oben im Fenster steht (wie in der Projektschau-Doku).
// Nach einem Klick bleibt das Ziel markiert, bis es oben ankommt; am Seitenende gilt der letzte Abschnitt.
(() => {
  const links = [...document.querySelectorAll(".fj-toc a")];
  const ziele = links.map((a) => document.getElementById(a.getAttribute("href").slice(1)));
  let ziel = null;
  const setzen = (aktiv) => links.forEach((a, i) => (i === aktiv ? a.setAttribute("aria-current", "true") : a.removeAttribute("aria-current")));
  function markiere() {
    const ende = innerHeight + scrollY >= document.documentElement.scrollHeight - 2;
    if (ziel !== null) {
      if (ende || (ziele[ziel] && ziele[ziel].getBoundingClientRect().top <= 120)) ziel = null; else return;
    }
    let aktiv = 0;
    ziele.forEach((el, i) => { if (el && el.getBoundingClientRect().top <= 120) aktiv = i; });
    setzen(ende ? links.length - 1 : aktiv);
  }
  links.forEach((a, i) => a.addEventListener("click", () => { ziel = i; setzen(i); }));
  addEventListener("scroll", markiere, { passive: true });
  markiere();
})();
