"""Impressum und Datenschutz holen Anschrift und Telefon aus betreiber.toml, nicht aus den Vorlagen."""

import re

from finder import ausgabe
from finder.suche import WURZEL, toml


def test_vorlagen_ohne_feste_kontaktdaten():
    for name in ("impressum.html", "datenschutz.html"):
        quelle = (ausgabe.VORLAGEN / name).read_text(encoding="utf-8")
        assert not re.search(r'href="tel:\+|<br>DE\d{9}', quelle), name


def test_platzhalter_aus_der_vorlage():
    platz = toml("betreiber.beispiel.toml")
    html = ausgabe.umgebung().get_template("impressum.html").render(
        stand="", aenderungen=[], version="", ferien=None, gebiete=[], feste=[], domain="", quellcode="",
        seite="impressum.html", regeln={}, vorschau=None, betreiber=platz)
    assert platz["name"] in html and platz["anschrift"][1] in html and "tel:+49301234567" in html
    assert (WURZEL / ".gitignore").read_text(encoding="utf-8").count("betreiber.toml") == 1
