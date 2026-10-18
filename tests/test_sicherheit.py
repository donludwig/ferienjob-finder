"""Daten von außen: Links, Steuerzeichen, CSV-Formeln."""

from finder.ausgabe import csv_zelle
from finder.modell import Anzeige, bereinigen


def test_nur_http_links():
    for link in ("javascript:alert(1)", " javascript:alert(1)", "data:text/html,x", "//boese.example"):
        assert bereinigen(Anzeige("t", "1", "Titel", link=link)).link == ""
    assert bereinigen(Anzeige("t", "1", "Titel", link="HTTPS://example.org/a")).link == "HTTPS://example.org/a"


def test_steuerzeichen_raus():
    a = bereinigen(Anzeige("t", "1", "Kasse‮ nilreB​", firma="A\x07B", text="Zeile\nzwei"))
    assert (a.titel, a.firma, a.text) == ("Kasse nilreB", "AB", "Zeile\nzwei")


def test_csv_formeln_als_text():
    assert csv_zelle("=HYPERLINK(\"x\")") == "'=HYPERLINK(\"x\")"
    assert csv_zelle("@SUMME") == "'@SUMME"
    assert csv_zelle("Kasse") == "Kasse" and csv_zelle(12) == 12


def test_bauen_leert_keinen_fremden_ordner(tmp_path):
    import pytest
    from finder import ausgabe
    (tmp_path / "wichtig.txt").write_text("nicht löschen")
    with pytest.raises(SystemExit):
        ausgabe.bauen([], tmp_path)
    assert (tmp_path / "wichtig.txt").exists()


def test_externer_link_der_jobboerse_nur_http(monkeypatch):
    import json
    from finder import netz
    from finder.quellen import ba
    a = ba.anzeige_aus({"referenznummer": "10000-1-S", "stellenangebotsTitel": "Aushilfe"})
    vorher = a.link
    monkeypatch.setattr(netz, "get", lambda *x, **k: json.dumps({"externeUrl": "javascript:alert(1)"}))
    assert ba.details_laden(a).link == vorher                # bleibt der Link zur Jobbörse, nicht leer
    monkeypatch.setattr(netz, "get", lambda *x, **k: json.dumps({"externeUrl": "https://arbeitgeber.example/job"}))
    assert ba.details_laden(a).link == "https://arbeitgeber.example/job"


def test_netz_ungueltige_und_zu_grosse_antworten(monkeypatch, tmp_path):
    import io
    import pytest
    from finder import netz
    monkeypatch.setattr(netz, "CACHE", tmp_path)
    monkeypatch.setattr(netz, "PAUSE", 0)

    class Antwort(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): pass

    monkeypatch.setattr(netz.urllib.request, "urlopen", lambda req, timeout=None: Antwort(b"<html>Wartung</html>"))
    with pytest.raises(netz.Fehler):
        netz.get_json("https://quelle.example/a")
    assert not netz.cache_datei("https://quelle.example/a").exists()   # kaputte Antwort bleibt nicht im Cache
    monkeypatch.setattr(netz, "GRENZE", 10)
    monkeypatch.setattr(netz.urllib.request, "urlopen", lambda req, timeout=None: Antwort(b"x" * 11))
    with pytest.raises(netz.Fehler):
        netz.get("https://quelle.example/b", versuche=1)


def test_unplausible_lohnangaben_der_quelle():
    from finder.bewertung import bewerten, regeln_laden
    from finder.modell import Anzeige
    r = regeln_laden()
    assert bewerten(Anzeige("t", "1", "Aushilfe", lohn_stunde=1e9), r).lohn_stunde is None
    assert bewerten(Anzeige("t", "1", "Aushilfe", lohn_stunde=float("nan")), r).lohn_stunde is None
    assert bewerten(Anzeige("t", "1", "Aushilfe", lohn_stunde=14.5), r).lohn_stunde == 14.5


def test_fehlermeldungen_nicht_auf_der_seite(monkeypatch, tmp_path):
    """Ausgefallene Quellen erscheinen auf der Seite nur mit Namen, ohne Adresse oder technische Meldung."""
    from finder import ausgabe, netz, suche
    from finder.quellen import ba

    def kaputt(*x, **k):
        raise netz.Fehler("HTTP 500 https://geheim.example/api?token=x")
    monkeypatch.setattr(ba, "suche", kaputt)
    e = suche.suchen("Berlin", 25, details=0, mit_feeds=False)
    assert e.fehler and e.ausgefallen == ["Jobbörse der Bundesagentur für Arbeit"]
    ausgabe.bauen([("Berlin", e)], tmp_path)
    html = (tmp_path / "berlin.html").read_text("utf-8")
    assert "Jobbörse der Bundesagentur für Arbeit" in html and "geheim.example" not in html and "HTTP 500" not in html


def test_csp_der_htaccess():
    from pathlib import Path
    h = (Path(__file__).parents[1] / "static/.htaccess").read_text("utf-8")
    for teil in ("Header always set Content-Security-Policy", "default-src 'self'", "base-uri 'none'", "form-action 'self'",
                 "frame-ancestors 'none'", "object-src 'none'", "ErrorDocument 404 /404.html", "ErrorDocument 403 /403.html"):
        assert teil in h, teil


def test_fehlerseiten_pfade_ab_wurzel():
    from finder.ausgabe import ab_wurzel
    html = '<link href="kern/kern.min.css?v=1"><a href="#inhalt"></a><a href="/x"></a><a href="mailto:a@b.de"></a><a href="https://x.de"></a><script src="kopf.js"></script>'
    assert ab_wurzel(html) == ('<link href="/kern/kern.min.css?v=1"><a href="#inhalt"></a><a href="/x"></a><a href="mailto:a@b.de"></a>'
                               '<a href="https://x.de"></a><script src="/kopf.js"></script>')
