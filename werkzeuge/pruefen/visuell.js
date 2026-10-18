// Visueller Vergleich vor und nach Änderungen an CSS oder JS (Aufräumen ohne Gestaltungsänderung):
//   aufnehmen:   node werkzeuge/pruefen/visuell.js aufnehmen <ordner> [Adresse]
//   vergleichen: node werkzeuge/pruefen/visuell.js vergleichen <referenz> <neu>
// Alle Seiten in ausgabe/, 320 und 1280 px, hell und dunkel, ohne Animationen, je höchstens 6000 px hoch.
// Daten zwischen den Aufnahmen nicht neu bauen (sonst ändern sich die Anzeigen), nur static/*.css und *.js nach ausgabe/ kopieren.
//   NODE_PATH=/PFAD/ZU/node_modules (mit playwright)
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const [modus, a, b] = process.argv.slice(2);
const AUSGABE = path.join(__dirname, "..", "..", "ausgabe");

async function aufnehmen(ordner, basis = "http://127.0.0.1:8765/") {
  fs.mkdirSync(ordner, { recursive: true });
  const seiten = fs.readdirSync(AUSGABE).filter((n) => n.endsWith(".html"));
  const browser = await chromium.launch();
  for (const breite of [320, 1280]) for (const thema of ["light", "dark"]) {
    const page = await (await browser.newContext({ viewport: { width: breite, height: 900 }, reducedMotion: "reduce" })).newPage();
    for (const s of seiten) {
      await page.goto(`${basis}${s}?theme=${thema}`, { waitUntil: "load" });
      await page.evaluate(() => document.fonts.ready);
      const hoehe = Math.min(6000, await page.evaluate(() => document.documentElement.scrollHeight));
      await page.screenshot({ path: path.join(ordner, `${s}-${breite}-${thema}.png`), clip: { x: 0, y: 0, width: breite, height: hoehe },
                              fullPage: true, animations: "disabled", caret: "hide" });
    }
  }
  await browser.close();
}

async function vergleichen(ref, neu) {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  let befunde = 0;
  for (const n of fs.readdirSync(ref).filter((x) => x.endsWith(".png")).sort()) {
    const p = path.join(neu, n);
    if (!fs.existsSync(p)) { console.log(`fehlt: ${n}`); befunde++; continue; }
    const r = fs.readFileSync(path.join(ref, n)), q = fs.readFileSync(p);
    if (r.equals(q)) continue;
    const d = await page.evaluate(async ([x, y]) => {
      const lade = async (b64) => { const i = new Image(); i.src = "data:image/png;base64," + b64; await i.decode(); return i; };
      const [i1, i2] = [await lade(x), await lade(y)];
      if (i1.width !== i2.width || i1.height !== i2.height) return { groesse: `${i1.width}×${i1.height} → ${i2.width}×${i2.height}` };
      const c = new OffscreenCanvas(i1.width, i1.height), g = c.getContext("2d");
      g.drawImage(i1, 0, 0); const d1 = g.getImageData(0, 0, c.width, c.height).data;
      g.clearRect(0, 0, c.width, c.height); g.drawImage(i2, 0, 0); const d2 = g.getImageData(0, 0, c.width, c.height).data;
      let anders = 0, oben = -1;
      for (let k = 0; k < d1.length; k += 4) if (d1[k] !== d2[k] || d1[k + 1] !== d2[k + 1] || d1[k + 2] !== d2[k + 2]) { anders++; if (oben < 0) oben = Math.floor(k / 4 / c.width); }
      return { anders, oben };
    }, [r.toString("base64"), q.toString("base64")]);
    if (d.groesse) { console.log(`Größe: ${n} ${d.groesse}`); befunde++; }
    else if (d.anders) { console.log(`anders: ${n} ${d.anders} Pixel, erste Abweichung bei y=${d.oben}`); befunde++; }
  }
  await browser.close();
  console.log(befunde ? `${befunde} Abweichungen` : "keine Abweichungen");
  process.exit(befunde ? 1 : 0);
}

if (modus === "aufnehmen") aufnehmen(a, b);
else if (modus === "vergleichen") vergleichen(a, b);
else { console.error("aufnehmen <ordner> [Adresse] | vergleichen <referenz> <neu>"); process.exit(2); }
