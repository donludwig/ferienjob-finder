"""Statische Seiten, CSV und JSON erzeugen. Ergebnis: ein Ordner, der so per FTP hochgeladen werden kann."""

import csv
import hashlib
import io
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

from .hochladen import MARKE

from .suche import WURZEL, toml

VORLAGEN = Path(__file__).parent / "vorlagen"
STATIC = WURZEL / "static"

# Kartenseiten (Stöbern, ohne JavaScript) gibt es für diese Vorfilter, je 50 pro Seite.
# Alle Anzeigen stehen in einer Tabelle pro Gebiet; dort filtert JavaScript.
FILTER = {  # Gruppen laut Bewertung (regeln.toml); die erste ist die Startseite eines Gebiets
    "ferien": ("Befristet & Saison", lambda t: "ferien" in t.bewertung.gruppen),
    "schueler": ("Für Schüler:innen", lambda t: "schueler" in t.bewertung.gruppen),
    "weitere": ("Weitere Aushilfsjobs", lambda t: "weitere" in t.bewertung.gruppen),
    "aussortiert": ("Aussortiert", lambda t: not t.bewertung.gruppen),
}
PRO_SEITE = {"karten": 24, "tabelle": 50}  # Blättern im Browser (filter.js); ohne JavaScript steht alles untereinander


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower().translate(str.maketrans("äöüß", "aous"))).strip("-")


def datei(gebiet, filter_="ferien", ansicht="karten"):
    return gebiet + ("" if filter_ == "ferien" else f"-{filter_}") + ("-tabelle" if ansicht == "tabelle" else "") + ".html"


def kategorien_laden():
    ks = toml("einstellungen.toml")["kategorie"]
    for k in ks:
        k["re"] = re.compile(k["muster"], re.IGNORECASE) if k.get("muster") else None
        k["slug"] = slug(k["name"])
    return ks


KATEGORIEN = None


def kategorie(anzeige):
    """Erste passende Kategorie nach Titel, sonst nach Berufsangabe; die letzte ohne Muster ist der Rest."""
    global KATEGORIEN
    KATEGORIEN = KATEGORIEN or kategorien_laden()
    for text in (anzeige.titel, anzeige.text[:300]):
        for k in KATEGORIEN:
            if k["re"] and k["re"].search(text):
                return k
    return KATEGORIEN[-1]


def euro(wert, nachkomma=2):
    return f"{wert:,.{nachkomma}f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def datum(iso):
    try:
        return datetime.fromisoformat(iso[:10]).strftime("%d.%m.%Y")
    except (TypeError, ValueError):
        return ""


def lohn_text(b):
    if b.lohn_stunde:
        return euro(b.lohn_stunde) + " pro Stunde"
    if b.lohn_monat:
        return euro(b.lohn_monat, 0) + " im Monat"
    return ""


def umgebung():
    env = Environment(loader=FileSystemLoader(VORLAGEN), autoescape=select_autoescape(["html"]),
                      trim_blocks=True, lstrip_blocks=True)
    env.filters.update(euro=euro, datum=datum, lohn_text=lohn_text)
    # Versionskennung aus dem Inhalt der eigenen Dateien: nach Änderungen lädt jeder Browser sie neu
    inhalt = b"".join((STATIC / n).read_bytes() for n in ("erweiterungen.css", "start.css", "fehler.css", "filter.js", "kopf.js", "doku.js",
                                                         "farbschema.js", "symbole.svg", "kern/kern.min.css", "schriften/schriften.css")) \
        + (WURZEL / "einstellungen.toml").read_bytes()  # Farben in farben.css kommen von dort
    # Symbole direkt in jede Seite: eine externe SVG-Datei per <use> scheitert bei file:// und bei Hostern,
    # die SVG mit falschem Dateityp ausliefern (rund 8 KB pro Seite, komprimiert etwa 2 KB)
    sprite = (STATIC / "symbole.svg").read_text("utf-8").replace(
        '<svg xmlns="http://www.w3.org/2000/svg">',
        '<svg xmlns="http://www.w3.org/2000/svg" class="fj-sprite" aria-hidden="true" focusable="false">')
    env.globals.update(datei=datei, FILTER=FILTER, kategorie=kategorie,
                       v=hashlib.sha256(inhalt).hexdigest()[:8], sprite=Markup(sprite))
    return env


def zeilen(treffer):
    """Flache Datensätze für CSV und JSON."""
    for t in treffer:
        a, b = t.anzeige, t.bewertung
        yield {
            "punkte": b.punkte, "eignung": b.eignung, "gruppen": ", ".join(b.gruppen), "kategorie": kategorie(a)["name"], "titel": a.titel, "arbeitgeber": a.firma,
            "plz": a.plz, "ort": a.ort, "lohn_stunde": b.lohn_stunde, "lohn_monat": b.lohn_monat,
            "lohn_quelle": b.lohn_quelle, "ausschluss": "; ".join(b.ausschluesse),
            "warnungen": "; ".join(b.warnungen), "eintritt": a.eintritt, "veroeffentlicht": a.veroeffentlicht,
            "quelle": a.quelle, "link": a.link, "volltext_geprueft": a.details_geladen,
        }


def ab_wurzel(html):
    """Relative Adressen in href und src auf / beziehen; Anker (#), absolute Pfade und Adressen mit Schema bleiben."""
    return re.sub(r'\b(href|src)="(?![#/]|[a-z][a-z0-9+.-]*:)', r'\1="/', html)


def csv_zelle(v):
    """Tabellenprogramme führen Zellen mit = + - @ als Formel aus (CSV-Injection): mit ' als Text markieren."""
    return "'" + v if isinstance(v, str) and v[:1] in ("=", "+", "-", "@", "\t", "\r") else v


def vorschau(treffer):
    """Motiv der Startseite aus echten Anzeigen: vier Karten aus verschiedenen Kategorien."""
    passend = [t for t in treffer if t.bewertung.gruppen]
    karten, kats = [], set()
    for t in passend:
        k = kategorie(t.anzeige)
        if k["slug"] not in kats and k.get("re"):  # „Sonstiges“ ist als Beispiel nichtssagend
            karten.append((t, k))
            kats.add(k["slug"])
        if len(karten) == 4:
            break
    if len(karten) < 4:
        return None
    return {"karten": karten}


def aenderungen():
    """CHANGELOG.md (Keep a Changelog) als [{titel, gruppen: [(name, [punkte])]}] für die Dokumentation und die Version im Footer."""
    text = (Path(__file__).resolve().parent.parent / "CHANGELOG.md").read_text("utf-8")
    versionen = []
    for zeile in text.splitlines():
        if zeile.startswith("## "):
            versionen.append({"titel": zeile[3:].strip(), "gruppen": []})
        elif zeile.startswith("### ") and versionen:
            versionen[-1]["gruppen"].append((zeile[4:].strip(), []))
        elif zeile.startswith("- ") and versionen and versionen[-1]["gruppen"]:
            versionen[-1]["gruppen"][-1][1].append(zeile[2:].strip())
    return versionen


def schreiben(ziel, name, text):
    # Einrückungen der Vorlagen entfernen (spart rund ein Viertel); <pre> und <textarea> kommen nicht vor
    (ziel / name).write_text(re.sub(r"\n[ \t]+", "\n", text), "utf-8")


def betreiber():
    """Angaben für Impressum und Datenschutz aus betreiber.toml (nicht im Repositorium), sonst die Platzhalter der Vorlage."""
    return toml("betreiber.toml" if (WURZEL / "betreiber.toml").exists() else "betreiber.beispiel.toml")


def bauen(ergebnisse, ziel, ferien=None):
    """ergebnisse: Liste von (Name, Ergebnis). Schreibt alle Seiten nach `ziel`."""
    ziel = Path(ziel)
    ziel.mkdir(parents=True, exist_ok=True)
    # Reste früherer Läufe entfernen (weggefallene Seiten, umbenannte Skripte): Der Ordner wird ganz geleert, aber nur,
    # wenn er leer ist oder die Markierung eines früheren Baus trägt, damit kein falsch angegebener Ordner verloren geht
    if any(ziel.iterdir()):
        if not (ziel / MARKE).exists():
            raise SystemExit(f"{ziel} ist nicht leer und keine frühere Ausgabe (Markierung {MARKE} fehlt) – anderen Zielordner wählen.")
        for alt in ziel.iterdir():
            shutil.rmtree(alt) if alt.is_dir() else alt.unlink()
    (ziel / MARKE).write_text("Ausgabe des Ferienjob-Finders; python -m finder bauen leert diesen Ordner.\n", "utf-8")
    env = umgebung()
    stand = datetime.now().strftime("%d.%m.%Y, %H:%M Uhr")
    einst = toml("einstellungen.toml")
    seite = einst.get("seite", {})
    beschreibung = {s["name"]: s.get("beschreibung", "") for s in einst["suchen"]}
    gebiete = [{"name": n, "slug": slug(n), "ort": e.ort, "umkreis": e.umkreis, "zahlen": e.zahlen,
                "beschreibung": beschreibung.get(n) or f"{e.umkreis} km um {e.ort}"} for n, e in ergebnisse]
    feste = {f["name"]: f for _, e in ergebnisse for f in e.feste}.values()
    versionen = aenderungen()
    basis = {"stand": stand, "aenderungen": versionen, "version": versionen[0]["titel"].split(" (")[0] if versionen else "",
             "ferien": ferien, "gebiete": gebiete, "feste": list(feste),
             "domain": seite.get("domain", ""), "quellcode": seite.get("quellcode", ""), "betreiber": betreiber()}
    regeln = toml("regeln.toml")

    for g, (_, e) in zip(gebiete, ergebnisse):
        for f, (f_text, pruef) in FILTER.items():
            auswahl = [t for t in e.treffer if pruef(t)]
            kats = {}
            for t in auswahl:
                k = kategorie(t.anzeige)
                kats.setdefault(k["slug"], [k, 0])[1] += 1
            for ansicht in ("karten", "tabelle"):
                name = datei(g["slug"], f, ansicht)
                schreiben(ziel, name, env.get_template("ergebnis.html").render(
                    **basis, gebiet=g, ergebnis=e, treffer=auswahl, gesamt=len(auswahl), filter=f, filter_text=f_text,
                    ansicht=ansicht, pro_seite=PRO_SEITE[ansicht], kategorien=sorted(kats.values(), key=lambda x: -x[1]),
                    seite=name))
        felder = list(zeilen(e.treffer[:1]))[0].keys() if e.treffer else []
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=felder, delimiter=";")
        w.writeheader()
        w.writerows({k: csv_zelle(v) for k, v in z.items()} for z in zeilen(e.treffer))
        (ziel / f"{g['slug']}.csv").write_text(buf.getvalue(), "utf-8-sig")
        schreiben(ziel, f"{g['slug']}.json", json.dumps(
            {"stand": stand, "ort": e.ort, "umkreis_km": e.umkreis, "anzeigen": list(zeilen(e.treffer))},
            ensure_ascii=False, separators=(",", ":")))

    basis["vorschau"] = vorschau(ergebnisse[0][1].treffer) if ergebnisse else None
    for seite in ("index", "ferien", "so-funktionierts", "regeln", "anlaufstellen", "ueber", "dokumentation", "impressum",
                  "datenschutz"):
        schreiben(ziel, f"{seite}.html", env.get_template(f"{seite}.html").render(
            **basis, seite=f"{seite}.html", regeln=regeln))
    # Fehlerseiten erscheinen unter jeder Adresse, auch in Unterordnern (/kern/x): Pfade ab der Wurzel, sonst fehlen CSS und Links.
    # Setzt wie ErrorDocument in der .htaccess voraus, dass die Seite im Wurzelverzeichnis der Domain liegt.
    for code in (403, 404):
        schreiben(ziel, f"{code}.html", ab_wurzel(env.get_template("fehler.html").render(**basis, seite=f"{code}.html", code=code)))

    # Farben als Klassen statt style-Attribute: die Content-Security-Policy (style-src 'self') blockiert Inline-Stile
    gebietsfarben = einst.get("gebietsfarben", {})
    farben = {g["slug"]: gebietsfarben.get(g["name"], "#1d5fc4") for g in gebiete}
    farben.update({k["slug"]: k["farbe"] for k in kategorien_laden()})
    farben["arbeitgeber"] = gebietsfarben.get("Arbeitgeber", "#a8287a")
    (ziel / "farben.css").write_text("/* erzeugt aus einstellungen.toml */\n" + "".join(
        f".fj-f-{n} {{ --fj-farbe: {f}; }}\n" for n, f in farben.items()), "utf-8")

    for name in ("kern", "schriften", "erweiterungen.css", "start.css", "fehler.css", "filter.js", "kopf.js", "doku.js", "farbschema.js", "LICENSE-lucide.txt", ".htaccess",
                 "favicon.svg", "favicon-32.png", "apple-touch-icon.png", "vorschau.png", "don-ludwig.jpg"):
        quelle = STATIC / name
        if quelle.is_dir():
            shutil.rmtree(ziel / name, ignore_errors=True)  # eigener Ordner: alte KERN-Dateien nicht liegen lassen
            shutil.copytree(quelle, ziel / name)
        else:
            shutil.copy2(quelle, ziel / name)
    return ziel
