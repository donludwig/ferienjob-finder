// Barrierefreiheit (axe-core, WCAG 2.1 AA + Best Practices), Konsolenfehler und CSP-Verstöße in Chromium, Firefox
// und WebKit, hell und dunkel, 320 und 1280 px, gegen die Live-Seite (echte Header) oder eine andere Adresse.
// Keine eigenen Abhängigkeiten: NODE_PATH zeigt auf einen Ordner node_modules mit playwright und @axe-core/playwright:
//   NODE_PATH=/PFAD/ZU/node_modules node werkzeuge/pruefen/browser.js [Adresse]
const { chromium, firefox, webkit } = require("playwright");
const { AxeBuilder } = require("@axe-core/playwright");

const BASIS = process.argv[2] || "https://ferienjobs.thinkrepeat.com/";
const SEITEN = ["index.html", "berlin.html", "berlin-tabelle.html", "brandenburg-saison.html", "berlin-aussortiert-tabelle.html",
  "so-funktionierts.html", "regeln.html", "anlaufstellen.html", "ferien.html", "ueber.html", "dokumentation.html", "impressum.html", "datenschutz.html", "403.html", "404.html"];

(async () => {
  let fehler = 0;
  for (const typ of [chromium, firefox, webkit]) {
    const browser = await typ.launch();
    for (const breite of [320, 1280]) for (const thema of ["light", "dark"]) {
      // „Bewegung reduzieren“: axe misst den Endzustand; mitten in der Animation der Startseite stehen Karten kurz auf 55 % Deckkraft
      const ctx = await browser.newContext({ viewport: { width: breite, height: 900 }, reducedMotion: "reduce" });
      const page = await ctx.newPage();
      const meldungen = [];
      // WebKit meldet bei jedem <select> unter style-src 'self' sein eigenes internes Stylesheet als CSP-Verstoß
      // (auch auf einer leeren Seite mit nur einem <select>); das betrifft nicht den Code der Seite
      page.on("console", (m) => {
        if (m.type() === "error" && !(typ === webkit && m.text().startsWith("Refused to apply a stylesheet"))) meldungen.push(m.text());
      });
      page.on("pageerror", (e) => meldungen.push(e.message));
      for (const s of SEITEN) {
        const antwort = await page.goto(`${BASIS}${s}?theme=${thema}`);
        if (antwort.status() !== 200) { console.log(`${typ.name()} ${s}: HTTP ${antwort.status()}`); fehler++; continue; }
        // axe nur einmal je Breite und Thema in Chromium; die anderen Browser prüfen Fehler und CSP
        if (typ === chromium) {
          const r = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "best-practice"]).analyze();
          for (const v of r.violations) { console.log(`axe ${breite}px ${thema} ${s}: ${v.id} (${v.nodes.length})`); fehler++; }
        }
        const ueberlauf = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1);
        if (ueberlauf) { console.log(`${typ.name()} ${breite}px ${s}: waagerechter Überlauf`); fehler++; }
      }
      for (const m of meldungen) { console.log(`${typ.name()} ${breite}px ${thema}: ${m}`); fehler++; }
      await ctx.close();
    }
    await browser.close();
  }
  console.log(fehler ? `${fehler} Befunde` : "keine Befunde");
  process.exit(fehler ? 1 : 0);
})();
