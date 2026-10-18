# Barrierefreiheit

Stand 15. Oktober 2026, Version 0.1.0 „Herbstferien“. Diese Erklärung ist ein Selbsttest und kein externer Nachweis.

## Ziel

Der Ferienjob-Finder soll die Anforderungen der WCAG 2.1 auf Stufe AA erfüllen. Das gilt für alle erzeugten Seiten: Startseite, Ergebnisseiten als Karten und als Tabelle, Ferientermine, Anlaufstellen, Erklärseiten, Dokumentation und Fehlerseiten.

## Was umgesetzt ist

- Ein Sprunglink führt direkt zum Inhalt. Alle Bedienelemente sind Links oder Buttons, mit der Tastatur in der Reihenfolge der Darstellung erreichbar und mit sichtbarem Fokusrahmen, auch in scrollbaren Tabellen.
- Filter und Umschalter melden ihren Zustand über `aria-pressed` und `aria-current`. Nach dem Filtern sagt die Seite die Zahl der passenden Anzeigen an.
- Tabellen haben eine Beschriftung. Symbole sind dekorativ, jede Information steht auch als Text.
- Texte und Flächen nutzen die Farben des KERN-Kits, hell und dunkel.
- Die Seiten funktionieren ohne JavaScript: Karten und Gruppen sind echte Seiten und Links. Das Skript ergänzt nur Filter, Sortierung und Farbschema.
- Die Systemeinstellung „Bewegung reduzieren“ schaltet die Animation der Startseite ab. Läuft sie, werden Karten grau statt durchsichtig, damit der Kontrast hält.
- Die Druckansicht zeigt die Anzeigen ohne Navigation und Filter.

## Wie geprüft wurde

- axe-core 4.14 über Playwright nach WCAG 2.1 AA mit Best Practices: alle Seitentypen, hell und dunkel, 320 und 1280 Pixel. Ergebnis: keine Verstöße.
- Tastatur und Fokus per Prüfskript: Tab läuft einmal durch jede Seite, jedes Ziel ist sichtbar, nicht verdeckt und hat einen Fokusrahmen.
- Chromium, Firefox und WebKit ohne Konsolenfehler und ohne waagerechten Überlauf.
- Markup mit html-validate, dazu Lighthouse auf der Live-Seite (Barrierefreiheit 100).

Einzelheiten stehen im Prüfbericht [`doku/pruefbericht.md`](doku/pruefbericht.md).

## Was aussteht

- Ein Durchgang mit Screenreader (NVDA, JAWS, VoiceOver).
- Ein Test mit Jugendlichen und Eltern.
- Eine Prüfung durch unabhängige Dritte, etwa nach BITV 2.0 oder EN 301 549.

## Bekannte Grenzen

- Die Texte der Anzeigen stammen aus der Jobbörse und von den Arbeitgebern. Ob sie verständlich sind, liegt nicht in der Hand des Ferienjob-Finders.
- Die Seiten gibt es nur auf Deutsch.
- Das KERN-Kit ist unverändert eingebunden. Seine Barrierefreiheit ist Sache des KERN-Projekts.

## Rückmeldung

Wenn du auf eine Barriere stößt, schreib bitte an **don@thinkrepeat.com** oder eröffne ein Ticket im [Repositorium](https://github.com/donludwig/ferienjob-finder/issues). Hilfreich sind die Seite, der Browser und das Hilfsmittel, mit dem das Problem auftritt.

---

# Accessibility (English)

As of 15 October 2026, version 0.1.0 "Herbstferien". This statement is a self-assessment, not an external audit.

All generated pages aim to meet WCAG 2.1 at level AA. A skip link leads to the content; all controls are links or buttons, reachable by keyboard with a visible focus ring; filters and switches expose their state, and the number of matching jobs is announced after filtering. Tables have captions, symbols are decorative, the pages work without JavaScript, the system setting "reduce motion" is respected, and the print view shows the jobs without navigation and filters.

Checked with axe-core 4.14 through Playwright (all page types, light and dark, 320 and 1280 pixels) with no violations, a scripted keyboard and focus pass, Chromium, Firefox and WebKit, html-validate and Lighthouse. Details are in the test report [`doku/pruefbericht.md`](doku/pruefbericht.md) (German).

Still to come: a pass with a screen reader, a test with young people and parents, and a review by independent third parties. Known limits: the job texts come from the job board and employers; the pages are in German only; the KERN kit is included unchanged.

Feedback: **don@thinkrepeat.com** or an issue in the [repository](https://github.com/donludwig/ferienjob-finder/issues).
