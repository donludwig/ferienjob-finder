"""Mutationstest (Prüfhandbuch 7): Jede Schutzmaßnahme wird einzeln ausgebaut, mindestens ein Test muss dann scheitern.
Bleibt alles grün, hat die Mutation „überlebt“, und es fehlt ein Test. Jede Datei wird aus der Sicherung zurückgeschrieben,
auch bei Abbruch. Aufruf aus dem Projektordner: .venv/bin/python werkzeuge/pruefen/mutationen.py
Neue Schutzmaßnahme = neue Zeile in MUTATIONEN."""

import subprocess
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
# (Datei, Suchtext, Ersatz, was ausgebaut wird)
MUTATIONEN = [
    ("finder/modell.py", 'if not a.link.lower().startswith(("https://", "http://")):', "if False:", "Links nur http(s)"),
    ("finder/modell.py", 'return "".join(c for c in s if c in "\\n\\t" or unicodedata.category(c) not in ("Cc", "Cf"))', "return s", "Steuerzeichen entfernen"),
    ("finder/modell.py", 'wert if _DATUM.match(wert) else ""', "wert", "Datumsfelder prüfen"),
    ("finder/ausgabe.py", '''return "'" + v if isinstance(v, str) and v[:1] in ("=", "+", "-", "@", "\\t", "\\r") else v''', "return v", "CSV-Formeln als Text"),
    ("finder/ausgabe.py", 'autoescape=select_autoescape(["html"])', "autoescape=False", "Maskieren in den Vorlagen"),
    ("finder/ausgabe.py", 'if not (ziel / MARKE).exists():', "if False:", "Bau leert keinen fremden Ordner"),
    ("finder/ausgabe.py", "shutil.rmtree(alt) if alt.is_dir() else alt.unlink()", "pass", "Bau räumt alte Dateien weg"),
    ("finder/hochladen.py", "context=ssl.create_default_context()", "", "Zertifikatsprüfung bei FTPS"),
    ("finder/hochladen.py", "alt = sorted(vorher - jetzt)", "alt = sorted(vorher | jetzt)", "Löschen nur eigener, alter Dateien"),
    ("finder/hochladen.py", "if fremd and not cfg.get(\"ordner_uebernehmen\"):", "if False:", "Upload nicht in fremde Ordner"),
    ("finder/hochladen.py", 'vorher = {r for r in vorher if not r.startswith("/") and ".." not in r.split("/")}', "pass", "Löschliste bleibt im Zielordner"),
    ("finder/hochladen.py", 'if not str(cfg.get("verzeichnis", "")).strip():', "if False:", "leeres Zielverzeichnis ist ein Fehler"),
    ("finder/bewertung.py", "and 5 <= anzeige.lohn_stunde <= 60 else None", "else None", "Lohnangaben der Quelle plausibel"),
    ("finder/netz.py", "if len(roh) > GRENZE:", "if False:", "Größengrenze für Antworten"),
    ("finder/netz.py", "cache_datei(url).unlink(missing_ok=True)", "pass", "kaputte Antwort nicht im Cache"),
    ("finder/quellen/ba.py", "    return x if isinstance(x, dict) else {}", "    return x", "Typprüfung Jobbörse"),
    ("finder/quellen/ba.py", 'if str(det.get("externeUrl") or "").lower().startswith(("https://", "http://")):', 'if det.get("externeUrl"):', "externe Links der Jobbörse nur http(s)"),
    ("finder/vorlagen/ergebnis.html", "{% for f in ergebnis.ausgefallen %}", "{% for f in ergebnis.fehler %}", "Fehlermeldungen nicht öffentlich"),
    ("static/.htaccess", " base-uri 'none';", "", "CSP: base-uri"),
    ("finder/quellen/feeds.py", "        if not isinstance(o, dict):\n            continue\n", "", "Typprüfung Recruitee"),
]


def tests():
    r = subprocess.run([str(WURZEL / ".venv/bin/pytest"), "-q", "-x", "-p", "no:cacheprovider"], cwd=WURZEL,
                       capture_output=True, text=True)
    return r.returncode == 0


def main():
    if not tests():
        sys.exit("Die Tests scheitern schon ohne Mutation – erst reparieren.")
    ueberlebt = []
    for datei, alt, neu, was in MUTATIONEN:
        pfad = WURZEL / datei
        original = pfad.read_text("utf-8")
        if original.count(alt) != 1:
            sys.exit(f"Suchtext nicht genau einmal in {datei}: {was}")
        try:
            pfad.write_text(original.replace(alt, neu), "utf-8")
            gruen = tests()
        finally:
            pfad.write_text(original, "utf-8")
        print(("ÜBERLEBT  " if gruen else "erkannt   ") + was)
        if gruen:
            ueberlebt.append(was)
    print(f"{len(MUTATIONEN) - len(ueberlebt)} von {len(MUTATIONEN)} Mutationen erkannt")
    sys.exit(1 if ueberlebt else 0)


if __name__ == "__main__":
    main()
