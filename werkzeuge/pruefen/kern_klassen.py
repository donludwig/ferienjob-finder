"""Prüft, dass die erzeugten Seiten nur echte KERN-Klassen und gekennzeichnete eigene Erweiterungen nutzen.
- Jede Klasse mit Präfix kern- muss im unveränderten Kit (static/kern/kern.min.css) vorkommen; erfundene KERN-Klassen fallen auf.
- Jede andere Klasse muss ein eigenes Präfix tragen (fj- für Erweiterungen, start- für die Startseite) und in den eigenen
  Stylesheets definiert sein; Klassen ohne Präfix sind ein Befund.
- Die KERN-Dateien müssen Byte für Byte dem npm-Paket entsprechen (node_modules/@kern-ux/native/dist).
Aufruf nach dem Bauen: python3 werkzeuge/pruefen/kern_klassen.py"""

import re
import sys
from html.parser import HTMLParser
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
KIT = (WURZEL / "static/kern/kern.min.css").read_text("utf-8")
EIGEN = "".join((WURZEL / "static" / n).read_text("utf-8") for n in ("erweiterungen.css", "start.css", "fehler.css"))
# Klassen, die im Beispiel-Markup der KERN-Doku stehen, aber keine eigene Regel im Kit haben (geprüft auf kern-ux.de,
# Komponenten „Table“ und „Accordion“, 15.10.2026)
KERN_DOKU = {"kern-table__head", "kern-accordion-group"}
KIT_KLASSEN = set(re.findall(r"\.(kern-[a-z0-9_-]+)", KIT)) | KERN_DOKU
EIGENE_KLASSEN = set(re.findall(r"\.((?:fj|start)-[a-z0-9_-]+)", EIGEN))
SKRIPTE = "".join((WURZEL / "static" / n).read_text("utf-8") for n in ("filter.js", "kopf.js", "doku.js", "farbschema.js"))


def eigen_definiert(k):
    """Eigene Klasse mit Regel, als Grundlage einer Variante (k--x, k__x) oder als Ansatzpunkt für ein Skript."""
    return k in EIGENE_KLASSEN or any(e.startswith((k + "--", k + "__")) for e in EIGENE_KLASSEN) or k in SKRIPTE
OHNE_STIL = {"js"}   # Zustandsklassen ohne eigene Regel am Element


class Klassen(HTMLParser):
    def __init__(self):
        super().__init__()
        self.klassen = set()

    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if k == "class" and v:
                self.klassen.update(v.split())


def main():
    befunde = []
    for seite in sorted((WURZEL / "ausgabe").glob("*.html")):
        p = Klassen()
        p.feed(seite.read_text("utf-8"))
        for k in sorted(p.klassen):
            if k.startswith("kern-"):
                if k not in KIT_KLASSEN:
                    befunde.append(f"{seite.name}: {k} gibt es in KERN nicht")
            elif k.startswith(("fj-", "start-")):
                if not eigen_definiert(k) and not k.startswith("fj-f-"):   # fj-f-* kommt aus farben.css
                    befunde.append(f"{seite.name}: {k} ist nirgends definiert")
            elif k not in OHNE_STIL:
                befunde.append(f"{seite.name}: {k} ohne Präfix (weder KERN noch eigene Erweiterung)")
    paket = WURZEL / "node_modules/@kern-ux/native/dist/kern.min.css"
    if paket.exists() and paket.read_bytes() != (WURZEL / "static/kern/kern.min.css").read_bytes():
        befunde.append("static/kern/kern.min.css weicht vom npm-Paket ab")
    for b in sorted(set(befunde)):
        print(b)
    print(f"{len(KIT_KLASSEN)} KERN-Klassen im Kit, {len(EIGENE_KLASSEN)} eigene Klassen; "
          + (f"{len(set(befunde))} Befunde" if befunde else "keine Befunde"))
    sys.exit(1 if befunde else 0)


if __name__ == "__main__":
    main()
