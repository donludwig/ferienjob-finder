# Sicherheit

## Lücke melden

Wenn du eine Sicherheitslücke im Ferienjob-Finder findest, melde sie bitte vertraulich per E-Mail an **don@thinkrepeat.com** mit dem Betreff „Ferienjob-Finder Sicherheit“. Bitte kein öffentliches Ticket und keine Veröffentlichung, bevor eine Korrektur online ist.

Alternativ geht die Meldung vertraulich über GitHub: [Sicherheitslücke melden](https://github.com/donludwig/ferienjob-finder/security/advisories/new) im Repositorium.

Hilfreich in der Meldung: betroffene Seite oder Datei, Schritte zum Nachstellen, erwartetes und tatsächliches Verhalten, Auswirkung aus deiner Sicht. Ein Proof of Concept hilft; Angriffe auf die Live-Seite oder den Webspace bitte nicht.

Ablauf:

- Eingangsbestätigung mit Einschätzung und geplantem Weg innerhalb von 14 Tagen.
- Korrektur als neue Version mit Eintrag in `CHANGELOG.md`, abgestimmt mit der meldenden Person. Veröffentlichung der Einzelheiten spätestens 90 Tage nach der Meldung, früher sobald die Korrektur online ist.
- Nennung der meldenden Person im Änderungsprotokoll, wenn gewünscht.

## Was dazugehört

- Der Generator in `finder/`: Abfrage der Jobbörse und der Arbeitgeber-Feeds, Bewertung, Bau der Seiten, Upload.
- Die erzeugten Seiten unter https://ferienjobs.thinkrepeat.com/: HTML, CSS, JavaScript, CSV, JSON und `.htaccess`. Auf dem Server liegt nur statisches HTML, kein Server-Code, keine Datenbank, keine Anmeldung, keine Cookies.
- Die gebündelten Bestandteile: KERN-Designsystem (`static/kern/`, unverändert aus `@kern-ux/native`), Lucide-Symbole, Schriften.

Nicht dazu gehören der Inhalt der Anzeigen (er kommt von der Jobbörse der Bundesagentur für Arbeit und von den Arbeitgebern), die Schnittstellen dieser Quellen, das Hosting bei manitu und der Rechner, auf dem gebaut wird. Denial of Service gegen den Webspace zählt nicht als Lücke im Ferienjob-Finder.

## Unterstützte Versionen

| Version | Unterstützt |
|---|---|
| aktuelle 0.x (Live-Seite) | ja |
| ältere | nein |

## Zuständigkeit

Don Ludwig pflegt den Ferienjob-Finder und beantwortet Meldungen. Was geprüft wurde, steht im Prüfbericht `doku/pruefbericht.md`, das Bedrohungsmodell in `doku/bedrohungsmodell.md`.

---

# Security (English)

Report vulnerabilities privately to **don@thinkrepeat.com**, subject “Ferienjob-Finder Security”. Please do not open a public issue before a fix is online, and do not attack the live site or the hosting. You will receive an acknowledgement with an assessment within 14 days; details are published no later than 90 days after the report, earlier once the fix is out. Reporters are credited if they wish. You can also report privately through GitHub: [report a vulnerability](https://github.com/donludwig/ferienjob-finder/security/advisories/new).

In scope: the generator in `finder/`, the generated static pages at https://ferienjobs.thinkrepeat.com/ (no server code, no database, no login, no cookies) and the bundled KERN design system, Lucide icons and fonts. Out of scope: the content of job ads, the source APIs, the hosting and denial of service.
