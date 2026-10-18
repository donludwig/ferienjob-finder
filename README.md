![Ferienjob-Finder: „Dein Ferienjob in Berlin & Brandenburg“, daneben Jobkarten in Kategoriefarben mit Filterleiste](static/vorschau.png)

Deutsch · [English](README.en.md)

# Ferienjob-Finder

Findet Ferien-, Aushilfs- und Minijobs für 16- bis 18-Jährige in Berlin und Brandenburg. Quelle ist die Jobbörse der Bundesagentur für Arbeit, dazu offene Stellen-Feeds einzelner Arbeitgeber. Jede Anzeige wird automatisch ausgewertet, ob sie für unter 18 passt und ob sie einen Lohn nennt. Das Ergebnis ist eine statische Website im Designsystem [KERN](https://www.kern-ux.de), die sich per FTP auf jeden Webspace laden lässt. Kein Server-Code, kein Tracking, keine Cookies.

## Start lokal

Voraussetzung: Python 3.11 oder neuer.

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt   # feste Versionen
.venv/bin/python -m finder bauen          # Suchen aus einstellungen.toml → ausgabe/
cd ausgabe && python3 -m http.server 8765 --bind 127.0.0.1
```

Dann `http://localhost:8765` im Browser öffnen. Weitere Befehle:

```
.venv/bin/python -m finder bauen --ort Dessau --umkreis 20   # beliebiger Ort
.venv/bin/python -m finder suchen --ort Berlin               # Ergebnis im Terminal
.venv/bin/python -m finder hochladen                         # ausgabe/ per FTP(S)
.venv/bin/pytest -q                                          # Tests, ohne Netzzugriff
```

## Konfiguration

Alles Inhaltliche steht in drei Dateien, ohne Code-Änderung anpassbar:

- `einstellungen.toml`: Abfragen an die Jobbörse (Minijob-Filter, Stichworte), die festen Suchen (Berlin; Brandenburg aus neun Kreisen à 50 km, damit das ganze Land abgedeckt ist), Kategorien mit Symbol und Farbe, Bundesland für den Ferienhinweis.
- `regeln.toml`: Bewertungsregeln. Pluspunkte, Ausschlüsse, Warnungen, jeweils als regulärer Ausdruck mit Begründung. Steht „kein“, „ohne“ oder „nicht“ davor, greift eine Regel nicht.
- `arbeitgeber.toml`: offene Feeds (Personio, Recruitee, Teamtailor) und feste Hinweise auf Arbeitgeber, die regelmäßig Schüler:innen suchen. Aufgenommen wird nur, was robots.txt und Nutzungsbedingungen erlauben.

## Veröffentlichung

`python -m finder bauen` erzeugt `ausgabe/`. Den Inhalt des Ordners hochladen, auch die versteckte Datei `.htaccess` (Komprimierung und Sicherheits-Header auf Apache). Alle Links sind relativ, die Seite läuft in jedem Verzeichnis. Beim Hochladen von Hand den Zielordner vorher leeren, wenn sich die Seitenstruktur geändert hat, sonst bleiben alte Seiten erreichbar; `python -m finder hochladen` löscht eigene alte Dateien selbst.

Beim Hochladen von Hand per SFTP zu manitu bricht die Übertragung mit vielen parallelen Verbindungen oft ab; höchstens zwei gleichzeitige Uploads im FTP-Programm einstellen.

Hochladen nur von Hand und nur nach ausdrücklicher Freigabe: Kein Skript und kein Zeitplan lädt die Website hoch.

1. `ftp.beispiel.toml` nach `ftp.toml` kopieren und ausfüllen (steht in `.gitignore`).
2. Passwort in den Schlüsselbund, im eigenen Terminal: `security add-generic-password -s ferienjob-finder-ftp -a BENUTZER -w` (fragt das Passwort verdeckt ab). Im Programm Schlüsselbundverwaltung beim Eintrag unter „Zugriff“ „Vor dem Erlauben des Zugriffs bestätigen“ wählen und keine Programme dauerhaft erlauben: Dann fragt macOS bei jedem Upload nach.
3. Hochladen: `.venv/bin/python -m finder hochladen`.

Täglich bauen (ohne Upload): `werkzeuge/taeglich.sh` baut `ausgabe/` neu, Protokoll in `.cache/taeglich.log`. Für den Zeitplan das Skript von einem eigenen launchd-Agent (macOS) oder cron-Eintrag aufrufen lassen, mit dem absoluten Pfad zum Projektordner.

Der Upload nutzt FTPS, schreibt jede Datei erst unter Zwischennamen und benennt sie dann um. Gelöscht werden nur Dateien, die das Programm selbst hochgeladen hat (Liste `ferienjob-dateien.txt` auf dem Server).

Impressum und Datenschutzerklärung stehen in `finder/vorlagen/`, Name, Anschrift und Telefon der betreibenden Person in `betreiber.toml` (Vorlage `betreiber.beispiel.toml`; die Datei steht in `.gitignore`), die Adresse der Seite in `einstellungen.toml` (`[seite] domain`); daraus entstehen auch die absoluten Adressen für das Vorschaubild in sozialen Medien. Unter `[seite] quellcode` steht die Adresse des Repositoriums für den Link im Footer; leer lassen, wenn es keinen gibt.

Favicon und Vorschaubild liegen in `static/` (`favicon.svg`, `favicon-32.png`, `apple-touch-icon.png`, `vorschau.png` mit 2400×1260). Das Vorschaubild für soziale Netzwerke erzeugt `werkzeuge/vorschau/erzeuge.js` aus der gebauten Startseite (Marke, Überschrift, Kartenmotiv): erst bauen, `ausgabe/` lokal ausliefern, dann `NODE_PATH=/PFAD/ZU/node_modules node werkzeuge/vorschau/erzeuge.js` (braucht Playwright). Die Symbole entstehen aus `werkzeuge/vorschau/icon.html` als Bildschirmfoto in Symbolgröße mit Gerätefaktor 2.

## Grenzen der Bewertung

- Die Bewertung ist eine Textauswertung, keine Rechtsprüfung. Sie erkennt Wörter, nicht Zusammenhänge.
- Der Volltext wird für alle Anzeigen der Jobbörse geladen (`details` in `einstellungen.toml`, 24 Stunden im Cache); fehlt er, zählt nur der Titel.
- Die Anzeigen der Jobbörse sprechen Jugendliche fast nie ausdrücklich an. „prüfen“ ist deshalb der Normalfall, „passt“ die Ausnahme.
- Viele Anzeigen nennen keinen Lohn. Unter 18 ohne Berufsabschluss gilt kein gesetzlicher Mindestlohn (MiLoG § 22 Abs. 2).
- Ob für Schüler:innen die Regeln für Kinder gelten (Vollzeitschulpflicht, JArbSchG § 2 Abs. 3), hängt vom Schulrecht des Landes ab. Die App entscheidet das nicht.
- Die Schnittstelle der Jobbörse ist öffentlich, aber nicht offiziell dokumentiert ([bundesAPI/jobsuche-api](https://github.com/bundesAPI/jobsuche-api)). Ändert sie sich, kann die Suche brechen. Stand 14.10.2026: Suche über `/pc/v6/jobs`, Details über `/pc/v4/jobdetails`.

## Sicherheit und Barrierefreiheit

Siehe [SECURITY.md](SECURITY.md) (Meldeweg), [ACCESSIBILITY.md](ACCESSIBILITY.md) (Erklärung zur Barrierefreiheit), `doku/pruefbericht.md` (Prüfbericht) und `doku/bedrohungsmodell.md` (Bedrohungsmodell).

## Lizenzen

- Eigener Code und eigene Texte: EUPL-1.2, siehe `LICENSE`. © 2026 Don Ludwig.
- KERN 2.8.2: Code unter EUPL-1.2, Texte und Grafiken unter CC BY-NC-SA ([Lizenz- und Nutzungsbedingungen](https://www.kern-ux.de/lizenz-und-nutzungsbedingungen)). Liegt unverändert in `static/kern/`, nur die Schriften sind auf die fünf genutzten Schnitte reduziert. Kopfzeile und Bildwortmarke von KERN sind öffentlichen Stellen vorbehalten und werden nicht verwendet.
- Fira Sans: SIL Open Font License 1.1 (`static/kern/fonts/LICENSE-fira-sans.txt`).
- Symbole aus KERN: Google Material Symbols, Apache License 2.0.
- Symbole: Lucide Icons 1.49.0, ISC-Lizenz (`static/LICENSE-lucide.txt`).
- Schulferien: OpenHolidays API, Daten unter ODbL-1.0.
