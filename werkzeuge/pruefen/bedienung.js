// Tastatur, Fokus, reduzierte Bewegung und Druck (Prüfhandbuch 8 und 9), in Chromium, 320 und 1280 px:
// - Tab läuft durch die ganze Seite und kommt wieder oben an (keine Falle), jedes fokussierte Element ist sichtbar und hat
//   einen Fokusrahmen (outline oder box-shadow), der nicht vom Rand eines scrollenden Bereichs abgeschnitten wird; das erste
//   Ziel ist der Sprunglink zum Inhalt
// - „Bewegung reduzieren“: keine laufenden CSS-Animationen oder -Übergänge länger als 0,01 s
// - Druck: Navigation, Filter und Chips ausgeblendet, kein waagerechter Überlauf, PDF entsteht
//   NODE_PATH=/PFAD/ZU/node_modules node werkzeuge/pruefen/bedienung.js [Adresse]
const { chromium } = require("playwright");

const BASIS = process.argv[2] || "https://ferienjobs.thinkrepeat.com/";
const SEITEN = ["index.html", "berlin.html", "berlin-tabelle.html", "regeln.html", "dokumentation.html", "ferien.html"];

(async () => {
  const befunde = [];
  const browser = await chromium.launch();
  for (const breite of [320, 1280]) {
    const ctx = await browser.newContext({ viewport: { width: breite, height: 900 }, reducedMotion: "reduce" });
    const page = await ctx.newPage();
    for (const s of SEITEN) {
      const ort = `${s} ${breite}px`;
      await page.goto(BASIS + s, { waitUntil: "load" });

      // Tastatur
      const gesehen = [];
      for (let i = 0; i < 400; i++) {
        await page.keyboard.press("Tab");
        const f = await page.evaluate(() => {
          const e = document.activeElement;
          if (!e || e === document.body) return null;
          const r = e.getBoundingClientRect(), st = getComputedStyle(e);
          const rahmen = (st.outlineStyle !== "none" && parseFloat(st.outlineWidth) > 0) || st.boxShadow !== "none";
          const verdeckt = (() => {   // liegt etwas anderes (etwa die feste Kopfzeile) über der Mitte des Elements?
            const x = r.left + r.width / 2, y = r.top + Math.min(r.height / 2, 10);
            const oben = document.elementFromPoint(x, y);
            return oben && !e.contains(oben) && !oben.contains(e) && !e.closest("summary, label")?.contains(oben);
          })();
          const abgeschnitten = (() => {   // Fokusrahmen ragt aus einem scrollenden Bereich (etwa der haftenden Seitenleiste)?
            let c = e.parentElement;
            while (c && c !== document.body && !/(auto|scroll|hidden)/.test(getComputedStyle(c).overflowY)) c = c.parentElement;
            if (!c || c === document.body || c.scrollHeight <= c.clientHeight) return false;
            const k = c.getBoundingClientRect(), d = (parseFloat(st.outlineWidth) || 0) + Math.max(0, parseFloat(st.outlineOffset) || 0);
            return r.top - d < k.top - .5 || r.bottom + d > k.bottom + .5;
          })();
          return { id: e.outerHTML.slice(0, 80), sichtbar: r.width > 0 && r.height > 0 && r.bottom > 0 && r.top < innerHeight,
                   rahmen, verdeckt, abgeschnitten, href: e.getAttribute("href") };
        });
        if (!f) { if (gesehen.length) break; continue; }
        if (gesehen.length === 0 && !(f.href || "").startsWith("#")) befunde.push(`${ort}: erstes Tab-Ziel ist kein Sprunglink: ${f.id}`);
        if (gesehen.includes(f.id) && f.id === gesehen[0]) break;   // einmal herum
        if (!f.sichtbar) befunde.push(`${ort}: fokussiert, aber nicht im Bild: ${f.id}`);
        if (!f.rahmen) befunde.push(`${ort}: kein Fokusrahmen: ${f.id}`);
        if (f.verdeckt) befunde.push(`${ort}: Fokus verdeckt: ${f.id}`);
        if (f.abgeschnitten) befunde.push(`${ort}: Fokusrahmen abgeschnitten: ${f.id}`);
        gesehen.push(f.id);
        if (i === 399) befunde.push(`${ort}: Tab kommt nach 400 Schritten nicht herum (Falle?)`);
      }

      // Haftende Seitenleiste der Ergebnisseiten: nach dem Scrollen per Tab durch, kein Fokusrahmen darf am Rand abgeschnitten sein
      if (breite === 1280 && await page.$(".fj-layout > :first-child a")) {
        await page.evaluate(() => scrollTo(0, 1500));
        await page.focus(".fj-layout > :first-child a");
        for (let i = 0; i < 80; i++) {
          const r = await page.evaluate(() => {
            const e = document.activeElement, s = document.querySelector(".fj-layout > :first-child");
            if (!s.contains(e)) return null;
            const st = getComputedStyle(e), a = e.getBoundingClientRect(), c = s.getBoundingClientRect();
            const d = (parseFloat(st.outlineWidth) || 0) + Math.max(0, parseFloat(st.outlineOffset) || 0);
            return a.top - d < c.top - .5 || a.bottom + d > c.bottom + .5 ? e.outerHTML.slice(0, 80) : "";
          });
          if (r === null) break;
          if (r) befunde.push(`${ort}: Fokusrahmen in der Seitenleiste abgeschnitten: ${r}`);
          await page.keyboard.press("Tab");
        }
        await page.evaluate(() => scrollTo(0, 0));
      }

      // Bewegung reduzieren
      const bewegt = await page.evaluate(() => [...document.querySelectorAll("*")].filter((e) => {
        const st = getComputedStyle(e);
        const lang = (w) => w.split(",").some((t) => parseFloat(t) > 0.01);
        return (st.animationName !== "none" && lang(st.animationDuration)) || lang(st.transitionDuration);
      }).map((e) => e.className || e.tagName).slice(0, 3));
      if (bewegt.length) befunde.push(`${ort}: Bewegung trotz „reduzieren“: ${bewegt.join(", ")}`);

      // Druck
      if (breite === 1280) {
        await page.emulateMedia({ media: "print" });
        const druck = await page.evaluate(() => ({
          ueberlauf: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
          sichtbar: [".fj-header nav", ".fj-chips", ".fj-filter"].filter((q) =>
            [...document.querySelectorAll(q)].some((e) => e.getClientRects().length)),
        }));
        if (druck.ueberlauf) befunde.push(`${ort}: Druck mit waagerechtem Überlauf`);
        if (druck.sichtbar.length) befunde.push(`${ort}: im Druck sichtbar: ${druck.sichtbar.join(", ")}`);
        const pdf = await page.pdf({ format: "A4" });
        if (pdf.length < 1000) befunde.push(`${ort}: PDF leer`);
        await page.emulateMedia({ media: "screen" });
      }
    }
    await ctx.close();
  }
  await browser.close();
  for (const b of befunde) console.log(b);
  console.log(befunde.length ? `${befunde.length} Befunde` : "keine Befunde");
  process.exit(befunde.length ? 1 : 0);
})();
