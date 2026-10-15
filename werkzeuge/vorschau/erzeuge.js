// Erzeugt static/vorschau.png (Vorschau für soziale Netzwerke, 1200×630 bei Faktor 2) im Aufbau der Projektschau-Vorschau:
// helle Fläche, Marke mit Symbol, Überschrift und Unterzeile links, rechts das Kartenmotiv der Startseite.
// Baut auf der gebauten Startseite auf (ausgabe/ über den lokalen Server), damit Motiv, Farben und Schriften dieselben sind.
//   NODE_PATH=/PFAD/ZU/node_modules node werkzeuge/vorschau/erzeuge.js [http://127.0.0.1:8765/]
const { chromium } = require("playwright");
const path = require("path");

const BASIS = process.argv[2] || "http://127.0.0.1:8765/";
const ZIEL = path.join(__dirname, "..", "..", "static", "vorschau.png");

const CSS = `
html, body { margin: 0; width: 1200px; height: 630px; overflow: hidden; }
body { background: color-mix(in srgb, var(--kern-color-action-default, #2044aa) 9%, #fff); }
.v { box-sizing: border-box; display: grid; grid-template-columns: 480px 1fr; align-items: center; gap: 56px; width: 1200px; height: 630px; padding: 0 64px 0 84px; }
.v-marke { display: flex; align-items: center; gap: 14px; margin: 0 0 56px; font-size: 28px; font-weight: 600; color: var(--kern-color-layout-text-default, #131525); }
.v-marke .fj-zeichen { width: 40px; height: 40px; border-radius: 8px; }
.v-marke .fj-zeichen .fj-symbol { width: 24px; height: 24px; }
.v h1 { margin: 0; font-size: 60px; line-height: 1.08; font-weight: 600; letter-spacing: -.01em; color: var(--kern-color-layout-text-default, #131525); }
.v-unter { margin: 40px 0 0; font-size: 28px; line-height: 1.45; color: var(--kern-color-layout-text-muted, #51577a); }
.v .start-vorschau { width: 100%; padding: 0; font-size: 13px; }
`;

(async () => {
  const browser = await chromium.launch();
  const page = await (await browser.newContext({ viewport: { width: 1200, height: 630 }, deviceScaleFactor: 2, reducedMotion: "reduce" })).newPage();
  await page.goto(BASIS + "index.html?theme=light", { waitUntil: "load" });
  await page.evaluate((css) => {
    const marke = document.querySelector(".fj-header__marke").cloneNode(true);
    const motiv = document.querySelector(".start-vorschau").cloneNode(true);
    const sprite = document.querySelector(".fj-sprite").cloneNode(true);
    const v = document.createElement("main");
    v.className = "v";
    const links = document.createElement("div");
    const p = document.createElement("p");
    p.className = "v-marke";
    p.append(...marke.childNodes);
    const h1 = document.createElement("h1");
    h1.innerHTML = "Dein Ferienjob<br>in Berlin &amp;<br>Brandenburg";
    const unter = document.createElement("p");
    unter.className = "v-unter";
    unter.innerHTML = "Aushilfs- und Ferienjobs ab 16,<br>geprüft auf Eignung und Lohn";
    links.append(p, h1, unter);
    v.append(links, motiv);
    document.body.replaceChildren(sprite, v);
    const st = document.createElement("style");
    st.textContent = css;
    document.head.append(st);
  }, CSS);
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: ZIEL });
  await browser.close();
  console.log("geschrieben:", ZIEL);
})();
