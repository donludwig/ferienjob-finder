"""Nutzlasten durch die ganze Strecke (Prüfhandbuch 2.6): fremde Anzeige → Bewertung → HTML, CSV, JSON.
Erwartung: kein aktives Markup in den Seiten, keine Formel in der CSV, gültiges JSON mit den Werten als Text."""

import csv
import io
import json
from html.parser import HTMLParser

from finder import ausgabe, netz, suche

NUTZLASTEN = ['"><script>alert(1)</script>', "<img src=x onerror=alert(1)>", "<svg onload=alert(1)>",
              "javascript:alert(1)", "' onmouseover='alert(1)", "=HYPERLINK(\"http://x\")", "‮evil​",
              "{{ 7*7 }}", "&lt;script&gt;"]


def anzeige(i, last):
    return {"stellenangebotsTitel": f"Aushilfe {last}", "firma": last, "hauptberuf": last,
            "referenznummer": f"10000-{i}-{last}", "datumErsteVeroeffentlichung": last,
            "eintrittszeitraum": {"von": last}, "vertragsdauer": "BEFRISTET", "istGeringfuegigeBeschaeftigung": True,
            "stellenlokationen": [{"adresse": {"plz": last, "ort": last, "region": "BERLIN"}}]}


class Pruefer(HTMLParser):
    """Sammelt aktives Markup: fremde Skripte, Ereignis-Attribute, gefährliche Adressen, Inline-Stile, eingebettete Inhalte."""
    def __init__(self):
        super().__init__()
        self.funde = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "script" and not (a.get("src") or "").split("?")[0].lstrip("/") in ("filter.js", "kopf.js", "farbschema.js", "doku.js"):
            self.funde.append(f"<script {a}>")
        if tag in ("iframe", "object", "embed", "img") and tag != "img" or (tag == "img" and (a.get("src") or "").lstrip("/") != "don-ludwig.jpg"):
            self.funde.append(f"<{tag} {a}>")
        for k, v in attrs:
            if k.startswith("on") or k == "style":
                self.funde.append(f"{tag} {k}={v}")
            if k in ("href", "src", "action") and v and v.strip().lower().startswith(("javascript:", "data:", "vbscript:")):
                self.funde.append(f"{tag} {k}={v}")


def test_nutzlasten_ganze_strecke(monkeypatch, tmp_path):
    liste = [anzeige(i, n) for i, n in enumerate(NUTZLASTEN)]
    details = {"stellenangebotsBeschreibung": " ".join(NUTZLASTEN), "externeUrl": "javascript:alert(1)"}

    def get(url, headers=None, cache_stunden=6, versuche=4):
        if "/pc/v6/jobs" in url:
            return json.dumps({"ergebnisliste": liste if "page=1" in url else [], "maxErgebnisse": len(liste)})
        if "/jobdetails/" in url:
            return json.dumps(details)
        return None

    monkeypatch.setattr(netz, "get", get)
    e = suche.suchen("Berlin", 25, region="BERLIN", details=len(liste), mit_feeds=False)
    assert len(e.treffer) == len(NUTZLASTEN)
    ausgabe.bauen([("Berlin", e)], tmp_path)

    for seite in tmp_path.glob("*.html"):
        p = Pruefer()
        p.feed(seite.read_text("utf-8"))
        assert not p.funde, (seite.name, p.funde[:3])
        text = seite.read_text("utf-8")
        assert "\u202e" not in text and "\u200b" not in text, seite.name   # Steuerzeichen entfernt

    zeilen = list(csv.reader(io.StringIO((tmp_path / "berlin.csv").read_text("utf-8-sig")), delimiter=";"))
    for z in zeilen[1:]:
        for zelle in z:
            assert not zelle[:1] in ("=", "+", "-", "@"), zelle   # Formeln als Text markiert
    daten = json.loads((tmp_path / "berlin.json").read_text("utf-8"))
    assert all(a["link"] == "" or a["link"].startswith("https://") for a in daten["anzeigen"])  # javascript: nie übernommen
