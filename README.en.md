![Ferienjob-Finder: “Dein Ferienjob in Berlin & Brandenburg” (your holiday job in Berlin and Brandenburg), next to it job cards in category colours with a filter bar](static/vorschau.png)

[Deutsch](README.md) · English

# Ferienjob-Finder

Finds holiday, temporary and mini jobs for 16- to 18-year-olds in Berlin and Brandenburg (Germany). The source is the job board of the German Federal Employment Agency (Bundesagentur für Arbeit), plus open job feeds of individual employers. The finder rates every ad automatically for suitability for minors and checks whether it states a wage. The result is a static website in the [KERN](https://www.kern-ux.de) design system that can be uploaded to any web space. No server code, no tracking, no cookies.

The website, the code, comments and the full documentation are in German, because the audience is German-speaking. This file is a short overview.

## Run locally

Requires Python 3.11 or newer.

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt   # pinned versions
.venv/bin/python -m finder bauen          # searches from einstellungen.toml → ausgabe/
cd ausgabe && python3 -m http.server 8765 --bind 127.0.0.1
```

Then open `http://localhost:8765` in your browser. More commands:

```
.venv/bin/python -m finder bauen --ort Dessau --umkreis 20   # any town, radius in km
.venv/bin/python -m finder suchen --ort Berlin               # results in the terminal
.venv/bin/python -m finder hochladen                         # upload ausgabe/ via FTPS
.venv/bin/pytest -q                                          # tests, no network access
```

## Configuration

All content settings live in three files and can be changed without touching code:

- `einstellungen.toml`: queries to the job board, the fixed searches (regions), categories with icon and colour, federal state for the school holiday notice, site domain and the source code link.
- `regeln.toml`: rating rules (bonus points, exclusions, warnings), each a regular expression with a reason.
- `arbeitgeber.toml`: open employer feeds (Personio, Recruitee, Teamtailor) and fixed hints on employers.

## Publishing

`python -m finder bauen` writes `ausgabe/`. Upload its contents including the hidden `.htaccess` (compression, security headers, error pages on Apache). The upload command uses FTPS with certificate verification, reads the password from the macOS keychain and only deletes files it uploaded itself. See the German README for details.

Name, address and phone number for the legal notice and privacy policy come from `betreiber.toml` (template `betreiber.beispiel.toml`; the file is in `.gitignore`).

## Limits

- The rating is text analysis, not a legal assessment.
- The job board API is public but not officially documented ([bundesAPI/jobsuche-api](https://github.com/bundesAPI/jobsuche-api)); changes can break the search.
- The finder does not check whether an ad is trustworthy.

## Security

See [SECURITY.md](SECURITY.md) (English section at the end), `doku/pruefbericht.md` (test report, German) and `doku/bedrohungsmodell.md` (threat model, German).

## Accessibility

See [ACCESSIBILITY.md](ACCESSIBILITY.md) (English section at the end).

## Licences

- Own code: EUPL-1.2, see `LICENSE`. © 2026 Don Ludwig.
- KERN 2.8.2: code under EUPL-1.2, texts and graphics under CC BY-NC-SA ([terms](https://www.kern-ux.de/lizenz-und-nutzungsbedingungen)), included unchanged in `static/kern/`.
- Fira Sans: SIL Open Font License 1.1. Icons: Lucide 1.49.0, ISC licence; icons inside KERN: Google Material Symbols, Apache License 2.0. School holidays: OpenHolidays API, data under ODbL-1.0.
