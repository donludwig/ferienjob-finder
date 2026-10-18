"""Kommandozeile.

    python -m finder bauen                      # alle Suchen aus einstellungen.toml nach ./ausgabe
    python -m finder bauen --ort Dessau --umkreis 20
    python -m finder suchen --ort Berlin        # Zusammenfassung im Terminal
    python -m finder hochladen                  # ausgabe/ per FTP(S) laut ftp.toml
"""

import argparse
import sys
from datetime import date

from . import ausgabe, ferien, hochladen, netz
from .suche import suchen, toml


def log(s):
    print(s, end="" if s.startswith("\r") else "\n", file=sys.stderr, flush=True)


def ferien_info():
    cfg = toml("einstellungen.toml")["ferien"]
    try:
        f = ferien.naechste(cfg["land"])
    except (netz.Fehler, KeyError, IndexError, TypeError, ValueError) as x:   # kaputte Antwort: Seiten ohne Ferienhinweis
        log(f"  ! Ferien: {x}")
        return None
    if not f:
        return None
    name, start, ende = f
    fmt = lambda d: d.strftime("%d.%m.%Y")
    heute = date.today()
    try:  # Übersicht für die Seite ferien.html: Berlin und Brandenburg, ab heute zwei Jahre
        tabelle = ferien.tabelle(["DE-BE", "DE-BB"], heute, date(heute.year + 2, heute.month, min(heute.day, 28)))
    except (netz.Fehler, KeyError, IndexError, TypeError, ValueError) as x:
        log(f"  ! Ferienübersicht: {x}")
        tabelle = {}
    return {"name": name, "start": fmt(start), "ende": fmt(ende), "ende_iso": ende.isoformat(), "laeuft": start <= heute,
            "land": cfg["land_name"], "tabelle": tabelle}


def main():
    ap = argparse.ArgumentParser(prog="python -m finder", description="Ferienjobs für 16- bis 18-Jährige finden")
    sub = ap.add_subparsers(dest="befehl", required=True)
    for name, hilfe in (("bauen", "statische Seiten, CSV und JSON erzeugen"), ("suchen", "Ergebnis im Terminal")):
        p = sub.add_parser(name, help=hilfe)
        p.add_argument("--ort", help="statt der Suchen aus einstellungen.toml")
        p.add_argument("--umkreis", type=int, default=25, help="km (mit --ort)")
        p.add_argument("--name", help="Anzeigename des Gebiets (mit --ort)")
        p.add_argument("--details", type=int, help="Volltext für die N vielversprechendsten Anzeigen laden")
        p.add_argument("--ohne-feeds", action="store_true", help="nur die Jobbörse abfragen")
    sub.choices["bauen"].add_argument("--ziel", default="ausgabe", help="Zielordner (Standard: ausgabe)")
    sub.add_parser("hochladen", help="ausgabe/ per FTP(S) hochladen (Zugang: ftp.toml + Schlüsselbund)")
    args = ap.parse_args()

    if args.befehl == "hochladen":
        cfg, pw = hochladen.zugang()
        hochladen.hochladen(ausgabe.WURZEL / "ausgabe", cfg, pw)
        return

    if args.ort:
        suchen_cfg = [{"name": args.name or args.ort, "ort": args.ort, "umkreis": args.umkreis}]
    else:
        suchen_cfg = toml("einstellungen.toml")["suchen"]

    ergebnisse = []
    for s in suchen_cfg:
        log(f"{s['name']} ({s['umkreis']} km)")
        e = suchen(s["ort"], s["umkreis"], region=s.get("region"), weitere_orte=s.get("weitere_orte", ()), details=args.details,
                   mit_feeds=not args.ohne_feeds, log=log)
        log("")
        for f in e.fehler:
            log(f"  ! {f}")
        z = e.zahlen
        log(f"  {z['anzeigen']} Anzeigen, {z['ohne_ausschluss']} ohne Ausschluss, "
            f"{z['mit_lohn']} davon mit Lohnangabe, {z['passt']} „passt“.")
        ergebnisse.append((s["name"], e))

    if not any(e.treffer for _, e in ergebnisse):
        sys.exit("Keine Treffer – Netzwerk oder Schnittstelle prüfen.")

    if args.befehl == "suchen":
        for name, e in ergebnisse:
            print(f"\n{name}")
            for t in [t for t in e.treffer if not t.bewertung.ausschluesse][:15]:
                b, a = t.bewertung, t.anzeige
                lohn = f"{b.lohn_stunde:.2f} €/h".replace(".", ",") if b.lohn_stunde else "Lohn ?"
                print(f"  [{b.punkte:>2}] {b.eignung:7} {a.titel[:50]:50} {a.ort[:14]:14} {lohn:10} {a.quelle}")
        return

    ziel = ausgabe.bauen(ergebnisse, args.ziel, ferien=ferien_info())
    print(f"Fertig: {ziel}/index.html – der Ordner kann so per FTP hochgeladen werden.")


if __name__ == "__main__":
    main()
