"""Fuzzing (Prüfhandbuch 3.1, 3.3): verstümmelte Anzeigen der Jobbörse und kaputte Feeds dürfen den Bau nicht abbrechen.
Fester Startwert, damit ein Fund reproduzierbar ist."""

import json
import random
from pathlib import Path

from finder import ausgabe, netz, suche
from finder.quellen import feeds

FIX = Path(__file__).parent / "fixtures"
SCHLECHT = [None, 0, -1, 1e308, "", "x" * 20000, [], {}, [None], {"a": 1}, True, "‮\x00\x07", "<svg onload=1>", "2026-13-45"]


def verstuemmeln(obj, zufall, tiefe=0):
    """Entfernt Felder, setzt falsche Typen und Unsinn ein, auch verschachtelt."""
    if isinstance(obj, dict):
        neu = {}
        for k, v in obj.items():
            r = zufall.random()
            if r < 0.15:
                continue                                   # Feld fehlt
            neu[k] = zufall.choice(SCHLECHT) if r < 0.4 else verstuemmeln(v, zufall, tiefe + 1)
        if zufall.random() < 0.1:
            neu["__proto__"] = {"x": 1}
        return neu
    if isinstance(obj, list):
        return [verstuemmeln(x, zufall, tiefe + 1) for x in obj if zufall.random() > 0.1]
    return obj


def test_fuzz_jobboerse_bis_zur_seite(monkeypatch, tmp_path):
    zufall = random.Random(20261015)
    vorlage = json.loads((FIX / "ba_suche.json").read_text("utf-8"))["ergebnisliste"]
    details = json.loads((FIX / "ba_details.json").read_text("utf-8"))
    liste = [verstuemmeln(zufall.choice(vorlage), zufall) for _ in range(1000)]
    for i, a in enumerate(liste):                          # eindeutige Nummern, sonst fasst die Suche zusammen
        if isinstance(a, dict) and zufall.random() > 0.05:
            a["referenznummer"] = f"F-{i}"

    def get(url, headers=None, cache_stunden=6, versuche=4):
        if "/pc/v6/jobs" in url:
            return json.dumps({"ergebnisliste": liste if "page=1" in url else []})
        if "/jobdetails/" in url:
            return json.dumps(verstuemmeln(details, zufall))
        return None

    monkeypatch.setattr(netz, "get", get)
    e = suche.suchen("Berlin", 25, details=50, mit_feeds=False)
    assert e.treffer and not e.fehler                      # kein Abbruch; doppelte Anzeigen fasst die Suche zusammen
    ausgabe.bauen([("Berlin", e)], tmp_path)
    assert (tmp_path / "berlin.html").exists() and (tmp_path / "berlin.json").exists()


def test_fuzz_feeds_brechen_nicht():
    zufall = random.Random(7)
    texte = {"personio": (FIX / "personio.xml").read_text("utf-8"), "teamtailor": (FIX / "teamtailor.rss").read_text("utf-8")}
    for _ in range(300):
        for art, text in texte.items():
            kaputt = list(text)
            for _ in range(zufall.randint(1, 30)):           # Zeichen löschen, verdoppeln, ersetzen
                i = zufall.randrange(len(kaputt))
                kaputt[i] = zufall.choice(["", "<", ">", "&", "\x00", kaputt[i] * 2, "<![CDATA["])
            try:
                getattr(feeds, art)("".join(kaputt), "Test", "https://example.org")
            except Exception as x:                          # erlaubt: Parserfehler, den suche() pro Feed abfängt
                assert type(x).__name__ in ("ParseError", "ExpatError"), repr(x)
    json_kaputt = [None, [], {"offers": None}, {"offers": [None, 1, "x", {"title": None}]}, {"offers": [{"locations": "x"}]}]
    for j in json_kaputt:
        feeds.recruitee(j, "Test", "https://example.org")
