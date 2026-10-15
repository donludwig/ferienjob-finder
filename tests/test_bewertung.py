import pytest

from finder.bewertung import bewerten, lohn_finden, regeln_laden
from finder.modell import Anzeige

REGELN = regeln_laden()


@pytest.mark.parametrize("text, stunde, monat", [
    ("€ 15/h", 15.0, None),
    ("13,90 EUR brutto je Stunde", 13.9, None),
    ("603 € pro Monat", None, 603.0),
    ("12,50 € pro Stunde", 12.5, None),
    ("15 Euro/h", 15.0, None),
    ("15€/Stunde", 15.0, None),
    ("ab 13,90 € pro Std.", 13.9, None),
    ("Stundenlohn: 14 €", 14.0, None),
    ("Stundenlohn von 13,90 Euro", 13.9, None),
    ("1.200 € im Monat", None, 1200.0),
    ("Vergütung 556 € monatlich", None, 556.0),
    ("Schicht 6-14 h", None, None),
    ("Umsatz 250 € pro Stunde", None, None),   # unplausibel als Lohn
    ("kein Lohn genannt", None, None),
])
def test_lohn(text, stunde, monat):
    assert lohn_finden(text) == (stunde, monat)


def bew(titel, text="", **kw):
    return bewerten(Anzeige(quelle="Test", id="1", titel=titel, text=text, details_geladen=True, **kw), REGELN)


def test_spaete_uhrzeit_ist_warnung():
    b = bew("Aushilfe", "Arbeit bis 2 Uhr")
    assert "späte Uhrzeit" in b.warnungen[0]
    assert b.eignung == "prüfen"


def test_ab_18_uhr_ist_kein_altersausschluss():
    b = bew("Aushilfe", "Schichten ab 18 Uhr möglich")
    assert b.eignung != "ab 18"
    assert not b.ausschluesse


def test_ab_18_jahre():
    b = bew("Aushilfe", "Du bist mindestens 18 Jahre alt")
    assert b.eignung == "ab 18"
    assert b.punkte < 0


def test_ab_16_uhr_zaehlt_nicht_als_alter():
    assert all(g.text != "ab 15 oder 16 Jahren" for g in bew("Aushilfe", "Arbeit ab 16 Uhr").gruende)


def test_verneinung_hebt_ausschluss_auf():
    b = bew("Aushilfe", "Kein Führerschein nötig, keine Nachtarbeit, Montag bis Freitag, kein Wochenende")
    assert not b.ausschluesse
    assert not b.warnungen


def test_fachkraft_nur_im_titel():
    assert not bew("Aushilfe Küche", "Du unterstützt unsere Fachkräfte").ausschluesse
    assert bew("Fachkraft Lagerlogistik").eignung == "ungeeignet"


def test_club_mate_ist_keine_bar():
    assert not bew("Aushilfe Getränkelager", "Kisten mit Club-Mate einräumen").warnungen
    assert bew("Aushilfe", "Service im Club am Wochenende").warnungen


def test_passt_mit_begruendung():
    b = bew("Ferienjob für Schüler", "Ab 16 Jahren, keine Vorkenntnisse. 14 € pro Stunde.", minijob=True)
    assert b.eignung == "passt"
    texte = [g.text for g in b.gruende]
    assert "ausdrücklich Ferienjob" in texte and "Stundenlohn genannt" in texte and "Minijob" in texte
    assert b.lohn_stunde == 14.0 and b.lohn_quelle == "Text"
    plus = [g for g in b.gruende if g.art == "plus"]
    assert sum(g.punkte for g in plus) == b.punkte
    assert all(g.fundstelle for g in plus if g.text not in ("Minijob", "Stundenlohn genannt"))


def test_strukturierter_lohn_vor_text():
    b = bew("Aushilfe", "früher 10 € pro Stunde", lohn_stunde=13.9)
    assert (b.lohn_stunde, b.lohn_quelle) == (13.9, "Angabe")


def test_schicht_nacht_wochenende_flag():
    assert "Schicht-, Nacht- oder Wochenendarbeit" in bew("Aushilfe", schicht_nacht_wochenende=True).warnungen[0]


def test_lohnangabe_ab_16_euro_ist_kein_alter():
    b = bew("Küchenhilfe", "Stundenlohn ab 16,22 EUR, ab 18 € bei Erfahrung")
    assert all(g.text != "ab 15 oder 16 Jahren" for g in b.gruende)
    assert not b.ausschluesse


def test_frueher_arbeitsbeginn():
    assert any("früher Arbeitsbeginn" in w for w in bew("Reinigungskraft", "05:00 bis 06:30 Uhr").warnungen)
    assert not bew("Aushilfe", "Start am 05.11.2026").warnungen


def test_passt_braucht_jugend_signal():
    b = bew("Reinigungskraft Minijob", "Keine Vorkenntnisse nötig, Aushilfe, befristet. 15 € pro Stunde.", minijob=True)
    assert b.punkte >= 6 and b.eignung == "prüfen"


def test_unbefristet_ist_nicht_befristet():
    assert all(g.text != "befristet oder kurzfristig" for g in bew("Aushilfe", "Vertrag unbefristet").gruende)
    assert any(g.text == "befristet oder kurzfristig" for g in bew("Aushilfe", "befristet bis Dezember").gruende)


def test_keine_schueler():
    b = bew("Reiniger Minijob", "Faire Arbeit. Bitte k e i n e Schüler, keine Studenten.")
    assert "nimmt keine Schüler:innen" in b.ausschluesse
    assert all(g.text != "spricht Schüler:innen an" for g in b.gruende)


def test_gruppen():
    assert bew("Aushilfe Verkauf", befristet=True).gruppen == ["ferien"]
    assert bew("Aushilfe Pop-Up-Store Weihnachtsmarkt").gruppen == ["ferien"]
    assert bew("Schülerjob im Verkauf").gruppen == ["schueler"]
    assert bew("Ferienjob für Schüler ab 16").gruppen == ["ferien", "schueler"]
    assert bew("Aushilfe Kasse Minijob", befristet=False).gruppen == ["weitere"]
    assert bew("Friseur/in gesucht").gruppen == []                        # Fachberuf ausgeschlossen
    assert bew("Aushilfe", beruf="Koch/Köchin").gruppen == []             # Beruf der Quelle zählt mit


def test_falsche_jugendtreffer():
    b = bew("Schulsozialarbeiter:in an einer Grundschule", "Unterstützung der Schüler")
    assert "schueler" not in b.gruppen
    assert bew("Schülerpraktikant:in").gruppen == []                        # Praktikum ist kein Job
    assert "schueler" not in bew("Kurstrainer:in", "Kurse für Jugendliche").gruppen
    assert bew("Wegbegleiter Aushilfe").gruppen == ["weitere"]               # „leiter“ nur als Wort


def test_ausschnitt_an_wortgrenzen():
    import re
    from finder.bewertung import _ausschnitt
    text = "Wir suchen dich als Aushilfe an der Kasse am Wochenende von Montag bis Samstag zwischen acht und einundzwanzig Uhr."
    stelle = _ausschnitt(text, re.search("Wochenende", text), rand=20)
    assert stelle.startswith("…") and stelle.endswith("…")
    worte = stelle.strip("…").split()
    assert all(w in text.split() for w in worte)          # nur ganze Wörter
