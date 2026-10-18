# Prüfbericht Ferienjob-Finder

Stand: Version 0.1.0 „Herbstferien“, 15. Oktober 2026. Alle Prüfungen hat der Autor selbst durchgeführt, mit automatischen Werkzeugen und KI-gestützten Reviews. Eine Prüfung durch unabhängige Dritte gab es nicht. Das Bedrohungsmodell steht in [bedrohungsmodell.md](bedrohungsmodell.md), der Meldeweg für Sicherheitslücken in [SECURITY.md](../SECURITY.md).

## Aufbau

Auf dem Server liegt nur statisches HTML mit CSS, zwei kleinen Skripten für Filter und Farbschema, Bildern, Schriften und den Listen als CSV und JSON. Kein Server-Code, keine Datenbank, keine Anmeldung, kein Formular, das etwas verschickt, keine Cookies, nichts von fremden Servern. Erzeugt werden die Seiten von einem Python-Programm auf dem Rechner des Autors. Die Prüfungen gelten beiden Teilen: dem Programm mit den Daten von außen und den erzeugten Seiten samt Upload.

## Prüfungen

| Prüfung | Vorgehen | Ergebnis |
|---|---|---|
| Datenfluss der Anzeigen | KI-gestützter Review von der Abfrage bis zu HTML, CSV und JSON: Links, Steuerzeichen, Maskierung, Formeln in Tabellenprogrammen | Links nur mit http oder https; Bidi- und unsichtbare Steuerzeichen werden entfernt; Zellen, die mit `=`, `+`, `-`, `@`, Tab oder Wagenrücklauf beginnen, markiert die CSV als Text; Jinja2 maskiert alle Werte |
| Angriffstexte durch die ganze Strecke | Anzeigen mit Skript-Tags, Ereignis-Attributen, `javascript:`-Links, Tabellenformeln, Vorlagen-Ausdrücken und Steuerzeichen von der Abfrage bis zu HTML, CSV und JSON (`tests/test_nutzlasten.py`) | kein aktives Markup, keine Formel, kein fremder Link in der Ausgabe |
| Fuzzing | 1000 zufällig verstümmelte Anzeigen der Jobbörse (fehlende Felder, falsche Typen, Riesenwerte) bis zur fertigen Seite, dazu 600 beschädigte XML-Feeds und kaputtes JSON (`tests/test_fuzz.py`) | kein Abbruch; Werte der Jobbörse und von Recruitee werden beim Einlesen nach Typ geprüft, Datumsfelder nur als Datum übernommen, Steuerzeichen in allen Textfeldern entfernt |
| Zweiter Review | getrennter KI-Review von Netzzugriff, Bau, Upload und Bewertung | Upload nur in einen leeren oder eigenen Zielordner, leerer Zielpfad ist ein Fehler, gelöscht wird nur aus der eigenen Liste ohne `..` und absolute Pfade; der Bau leert nur einen als eigen markierten Ausgabeordner; Antworten höchstens 20 MB, ungültige Antworten landen nicht im Zwischenspeicher; Lohnangaben der Quelle zählen nur in plausiblen Spannen; ausgefallene Quellen erscheinen auf der Seite nur mit Namen, ohne Adresse und Fehlermeldung |
| Hochladen | Review des FTPS-Uploads: Verschlüsselung, Zertifikat, Ablage des Passworts, Löschen alter Dateien | FTPS mit Prüfung des Server-Zertifikats; Passwort nur im Schlüsselbund oder in einer Umgebungsvariable; jede Datei erst unter Zwischennamen, dann umbenannt |
| Mutationstest | Jede Schutzmaßnahme wird einzeln ausgebaut, dann muss mindestens ein Test scheitern (`werkzeuge/pruefen/mutationen.py`) | 20 von 20 Mutationen erkannt |
| Tests | pytest ohne Netzzugriff, mit anonymisierten Beispieldaten; Tests für Links, Steuerzeichen, CSV, Zertifikatsprüfung, Upload-Ziel, Netzgrenzen, Fehlerseiten und Sicherheits-Header | 55 Tests, alle bestanden |
| Feeds im XML-Format | Prüfung des Parsers auf Entity-Angriffe | Python 3.14 mit expat 2.7.4: keine externen Entities, Schutz gegen Entity-Expansion; ältere Python-Versionen können ein älteres expat mitbringen |
| Statische Analyse | semgrep 1.180 mit den Regelsätzen python, security-audit und secrets | Funde eingeordnet: Links in Vorlagen sind intern oder bereinigt, Attribute maskiert. Nicht von semgrep erfasst: Schutz beim Hochladen, Größengrenzen, Lohnspannen, Fehlerseiten; diese sichern Tests, Mutationstest und der zweite Review ab |
| Sicherheits-Header | `.htaccess`: Content-Security-Policy `default-src 'self'` ohne Inline-Skripte und -Stile, mit `object-src 'none'`, `base-uri 'none'`, `form-action 'self'`, `frame-ancestors 'none'`; `nosniff`, `Referrer-Policy: no-referrer`; HSTS vom Hoster; Umleitung auf HTTPS; keine Ordnerlisten; interne Dateien gesperrt; eigene Fehlerseiten 403 und 404, weil die des Hosters außerhalb des Ordners liegen und die Header nicht bekämen | live geprüft mit `curl -sI` auf Startseite, erfundene Adressen und gesperrte Ordner: alle Header überall vorhanden |
| Scanner gegen die laufende Seite | OWASP ZAP (Docker-Image `zap-stable`), Baseline-Scan: Spider und passive Regeln. Kein aktiver Scan: Ohne Server-Code bietet die Seite dafür kaum Angriffsfläche, der Scan würde nur den Webspace belasten | keine Fehler, 60 Regeln bestanden. Warnungen eingeordnet: Hinweise auf persönliche Daten, Zeitstempel und XSS sind Ziffernfolgen in Referenznummern und Formularwerte einer statischen Seite; Cache-Hinweise gewollt; Permissions-Policy und Cross-Origin-Embedder-Policy bewusst nicht gesetzt, die Seite nutzt weder Geräte-Schnittstellen noch fremde Inhalte |
| Tastatur, Fokus, Druck | Prüfskript `werkzeuge/pruefen/bedienung.js` in Chromium, 320 und 1280 Pixel: Tab läuft einmal durch jede Seite; jedes Ziel ist sichtbar, nicht verdeckt und hat einen Fokusrahmen, der nicht vom Rand eines scrollenden Bereichs abgeschnitten wird; mit „Bewegung reduzieren“ keine Animation; Druckansicht ohne Navigation und Filter, ohne Überlauf | ohne Befund. Eigene Regeln ergänzen KERN dort, wo das Kit keinen Fokusrahmen setzt (scrollbare Tabellen) oder Links beim Fokus neu positioniert (Sprunglink) |
| Barrierefreiheit | axe-core 4.14 nach WCAG 2.1 AA mit Best Practices, alle Seitentypen, hell und dunkel, 320 und 1280 Pixel, mit „Bewegung reduzieren“, damit axe den Endzustand der Animation misst; die Animation graut Karten aus statt sie durchsichtig zu machen, damit der Kontrast auch mitten im Lauf hält | keine Verstöße |
| Browser | Chromium, Firefox und WebKit (Playwright) mit `werkzeuge/pruefen/browser.js`: Konsolenfehler, CSP-Verstöße, waagerechter Überlauf; Filter, Chips, Sortierung und Datumsfeld von Hand | ohne Befund; WebKit meldet bei jedem Auswahlfeld sein eigenes internes Stylesheet als CSP-Verstoß, das betrifft nicht den Code der Seite |
| KERN-Klassen | Jede Klasse in den erzeugten Seiten: `kern-`-Klassen müssen im unveränderten Kit oder im Beispiel-Markup der KERN-Doku stehen, alle anderen tragen ein eigenes Präfix und sind in den eigenen Stylesheets oder Skripten definiert (`werkzeuge/pruefen/kern_klassen.py`) | keine erfundenen KERN-Klassen, keine Klassen ohne Präfix |
| Markup | html-validate auf allen erzeugten Seiten | offen nur Schreibweise des DOCTYPE, `role="region"` aus dem KERN-Markup und das Filterformular ohne Absende-Knopf (filtert sofort, sendet nichts) |
| CSS | Stylelint, Regel für unbekannte Selektoren | keine unbekannten Selektoren |
| Links | linkinator über alle Seiten der Live-Seite, dazu die Links nach außen auf den Textseiten | keine toten Links (46 Adressen) |
| Lighthouse 13.5 | Startseite, Ergebnisseite, Fehlerseite und Dokumentation der Live-Seite, Mobil-Profil mit simulierter Drosselung | Leistung 97 bis 98, die lange Dokumentation 92 bis 97 je nach Lauf; Barrierefreiheit, Best Practices und SEO 100 |
| Abhängigkeiten | Trivy 0.75 (Prüfsumme des Release geprüft) über `package-lock.json` und `requirements.txt` mit festen Versionen | keine bekannten Schwachstellen |
| Lieferkette | KERN-Dateien per Byte-Vergleich mit dem npm-Paket; Abfrage in der Schwachstellen-Datenbank OSV für KERN 2.8.2, Lucide 1.49.0, Jinja2 3.1.6, MarkupSafe 3.0.4 | KERN unverändert; keine bekannten Schwachstellen |
| Geheimnisse und persönliche Daten | gitleaks 8.30 über alle Commits und den Arbeitsordner; frischer Klon des öffentlichen Repositoriums durchsucht nach Zugangsdaten, lokalen Pfaden, Kontaktdaten und Bild-Metadaten | keine Funde; Commits mit anonymer GitHub-Adresse; Kontaktdaten nur wie im Impressum; Bilder ohne Standort- und Kameradaten |

## Was aussteht

- **Unabhängige Prüfung:** kein Pentest, kein Audit durch Dritte.
- **Screenreader und Nutzungstest:** axe-core deckt nur einen Teil der Kriterien ab. Ein Durchgang mit Screenreader und ein Test mit Jugendlichen stehen aus.
- **Inhalt der Anzeigen:** Ob eine Anzeige seriös ist, prüft der Ferienjob-Finder nicht.
- **Schnittstelle der Jobbörse:** öffentlich, aber nicht offiziell dokumentiert; ändert sie sich, kann die Suche ausfallen.
- **Automatische Prüfkette:** Die Prüfungen laufen lokal von Hand, nicht bei jedem Stand von selbst. Die Abfrage bei OSV ist eine Momentaufnahme.
- **Stückliste:** Das Repositorium enthält keine Stückliste (SBOM); Abhängigkeiten stehen mit festen Versionen in `package-lock.json` und `requirements.txt`.
- **KERN:** Geprüft ist, dass die Dateien dem Paket der Registry entsprechen. Das Kit selbst ist nicht geprüft.

## Prüfungen wiederholen

```
.venv/bin/pytest -q
.venv/bin/python werkzeuge/pruefen/mutationen.py
.venv/bin/python -m finder bauen && python3 -I werkzeuge/pruefen/kern_klassen.py
cd ausgabe && python3 -m http.server 8765 --bind 127.0.0.1
NODE_PATH=/PFAD/ZU/node_modules node werkzeuge/pruefen/browser.js http://127.0.0.1:8765/
NODE_PATH=/PFAD/ZU/node_modules node werkzeuge/pruefen/bedienung.js http://127.0.0.1:8765/
NODE_PATH=/PFAD/ZU/node_modules node werkzeuge/pruefen/visuell.js aufnehmen /tmp/vorher   # vor einer Änderung an CSS oder JS
NODE_PATH=/PFAD/ZU/node_modules node werkzeuge/pruefen/visuell.js aufnehmen /tmp/nachher  # danach, ohne neu zu bauen
NODE_PATH=/PFAD/ZU/node_modules node werkzeuge/pruefen/visuell.js vergleichen /tmp/vorher /tmp/nachher
```

`NODE_PATH` zeigt auf einen Ordner `node_modules` mit `playwright` und `@axe-core/playwright`.
