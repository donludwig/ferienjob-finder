from pathlib import Path

import pytest

from finder import netz, suche
from finder.quellen import ba, feeds

FIX = Path(__file__).parent / "fixtures"


def lies(name):
    return (FIX / name).read_text("utf-8")


@pytest.fixture
def offline(monkeypatch):
    """Ersetzt alle Netzabrufe durch Fixtures; unbekannte URLs schlagen fehl."""
    abrufe = []

    def get(url, headers=None, cache_stunden=6, versuche=4):
        abrufe.append(url)
        if "/pc/v6/jobs" in url:
            return lies("ba_suche.json")
        if "/jobdetails/" in url:
            return lies("ba_details.json")
        if url.endswith("/xml"):
            return lies("personio.xml") if "vapiano" in url else None
        if "api/offers" in url:
            return lies("recruitee.json")
        if url.endswith(".rss"):
            return lies("teamtailor.rss")
        raise AssertionError(f"unerwarteter Abruf {url}")

    monkeypatch.setattr(netz, "get", get)
    return abrufe


def test_ba_anzeige_aus_v6():
    import json
    a = ba.anzeige_aus(json.loads(lies("ba_suche.json"))["ergebnisliste"][0])
    assert a.titel.startswith("Aushilfe Verkauf")
    assert (a.ort, a.plz, a.firma) == ("Berlin", "10115", "Beispiel Bäckerei GmbH")
    assert a.lohn_stunde == 13.9 and a.minijob is True
    assert a.link.endswith("10000-0000000001-S")


def test_ba_details(offline):
    a = ba.suche("Berlin", 25)[1]
    assert not a.details_geladen
    ba.details_laden(a)
    assert a.details_geladen and "Cocktailbar" in a.text and a.schicht_nacht_wochenende


def test_feeds_ortsfilter(offline):
    berlin = suche.toml("arbeitgeber.toml")["berlin"]
    p = feeds.suche({"name": "V", "art": "personio", "url": "https://vapiano.jobs.personio.de/xml"},
                    "Berlin", 25, berlin)
    assert [a.id for a in p] == ["111"]                      # Bonn fällt raus
    fest = feeds.suche({"name": "V", "art": "personio", "url": "https://vapiano.jobs.personio.de/xml",
                        "ort": "Berlin"}, "Berlin", 25, berlin)
    assert len(fest) == 2                                    # fester Ort überschreibt den Feed
    assert p[0].link == "https://vapiano.jobs.personio.de/job/111"
    r25 = feeds.suche({"name": "B", "art": "recruitee", "url": "https://x/api/offers/"}, "Berlin", 25, berlin)
    r50 = feeds.suche({"name": "B", "art": "recruitee", "url": "https://x/api/offers/"}, "Berlin", 50, berlin)
    assert [a.ort for a in r25] == ["Berlin"]
    assert [a.ort for a in r50] == ["Berlin", "Potsdam"]     # Umland erst ab größerem Umkreis
    assert r25[0].lohn_stunde == 13.9
    t = feeds.suche({"name": "F", "art": "teamtailor", "url": "https://x/jobs.rss"}, "Berlin", 25, berlin)
    assert (t[0].plz, t[0].ort) == ("10785", "Berlin")


def test_suchen_gesamt(offline):
    r = suche.suchen("Berlin", 25, details=5)
    titel = [t.anzeige.titel for t in r.treffer]
    assert len(titel) == len(set(titel))                     # zwei BA-Abfragen liefern dieselben Anzeigen
    bar = next(t for t in r.treffer if "Bar" in t.anzeige.titel)
    assert bar.bewertung.eignung == "ab 18"
    assert bar.bewertung.lohn_monat == 556.0
    assert r.treffer[0].bewertung.eignung == "passt"
    assert not r.fehler
    assert any(f["name"] == "Lidl" for f in r.feste)
    assert r.zahlen["anzeigen"] == len(r.treffer)


def test_bauen(offline, tmp_path):
    from finder import ausgabe
    e = suche.suchen("Berlin", 25, details=5)
    ausgabe.bauen([("Berlin", e)], tmp_path, ferien={"name": "Herbstferien", "start": "19.10.2026",
                                                     "ende": "31.10.2026", "laeuft": False, "land": "Berlin"})
    for name in ("index.html", "berlin.html", "berlin-tabelle.html", "berlin-weitere.html", "berlin-aussortiert-tabelle.html", "regeln.html", "anlaufstellen.html",
                 "ferien.html", "dokumentation.html", "berlin.csv", "berlin.json", "kern/kern.min.css", "farbschema.js", "LICENSE-lucide.txt"):
        assert (tmp_path / name).exists(), name
    html = (tmp_path / "berlin.html").read_text("utf-8")
    assert "Herbstferien" in html and "kern-card" in html and "{{" not in html
    for name in set(__import__("re").findall(r'<use href="#([a-z-]+)"', html)):   # jedes Symbol ist in der Seite definiert
        assert f'<symbol id="{name}"' in html, name
    assert 'href="http' not in (tmp_path / "index.html").read_text("utf-8").split("<main")[0]  # keine externen Ressourcen im Kopf
    for seite in tmp_path.glob("*.html"):   # CSP style-src 'self': keine Inline-Stile
        assert 'style="' not in seite.read_text("utf-8"), seite.name
    assert ".fj-f-berlin { --fj-farbe:" in (tmp_path / "farben.css").read_text("utf-8")
    (tmp_path / "veraltet.js").write_text("x")              # Reste früherer Läufe verschwinden beim nächsten Bau
    ausgabe.bauen([("Berlin", e)], tmp_path)
    assert not (tmp_path / "veraltet.js").exists() and (tmp_path / "index.html").exists()
    index = (tmp_path / "index.html").read_text("utf-8")
    assert 'rel="icon" href="favicon.svg"' in index and (tmp_path / "vorschau.png").exists()
    assert '<meta property="og:image" content="https://' in index           # Vorschaubild braucht absolute Adresse


def test_region(offline):
    r = suche.suchen("Berlin", 50, region="BRANDENBURG", details=0)
    assert [t.anzeige.ort for t in r.treffer] == ["Potsdam"]          # nur der Potsdamer Feed-Treffer
    assert {"Filmpark Babelsberg", "Lidl", "dm-drogerie markt"} <= {f["name"] for f in r.feste}
    b = suche.suchen("Berlin", 50, region="BERLIN", details=0)
    assert all(t.anzeige.region == "BERLIN" for t in b.treffer) and len(b.treffer) >= 4
    assert "Filmpark Babelsberg" not in {f["name"] for f in b.feste}
