"""Bewertung einer Anzeige: Regeln aus regeln.toml, Lohn-Erkennung, Begründung je Treffer."""

import re
import tomllib
from pathlib import Path

from .modell import Bewertung, Grund

REGELN_DATEI = Path(__file__).resolve().parent.parent / "regeln.toml"

# Stundenlohn: "14,50 € pro Stunde", "€ 15/Std.", "15 Euro/h", "13,90 EUR brutto je Stunde"
LOHN_RE = re.compile(
    r"(?:(?:€|eur(?:o)?)\s*)?(?<![\d.,])(\d{1,2}(?:[.,]\d{1,2})?)\s*(?:€|eur(?:o)?)?\s*"
    r"(?:brutto\s*)?(?:/|pro|je|die)\s*(?:std\.?|stunde|h)\b",
    re.IGNORECASE,
)
# "Stundenlohn: 14 €", "Stundenlohn von 13,90 Euro"
STUNDENLOHN_RE = re.compile(
    r"stundenlohn\D{0,20}?(?<![\d.,])(\d{1,2}(?:[.,]\d{1,2})?)\s*(?:€|eur)", re.IGNORECASE
)
# Monat: "603 € pro Monat", "1.200 € im Monat", "556 € monatlich"
MONAT_RE = re.compile(
    r"(?<![\d.,])(\d{1,2}\.\d{3}|\d{3,4})(?:,\d{2})?\s*(?:€|eur(?:o)?)\s*(?:brutto\s*)?"
    r"(?:(?:/|pro|im|je)\s*monat|monatlich)",
    re.IGNORECASE,
)
UNBEFRISTET = {"re": re.compile(r"\bunbefristet")}
VERNEINUNG_RE = re.compile(r"\b(kein\w*|k e i n e?|ohne|nicht)\b[^.!?\n]{0,15}$")


def _zahl(s):
    return float(s.replace(",", "."))


def lohn_finden(text):
    """(Stundenlohn, Monatsbetrag) aus dem Text, jeweils der höchste plausible Wert."""
    stunde = [_zahl(m.group(1)) for r in (LOHN_RE, STUNDENLOHN_RE) for m in r.finditer(text)]
    stunde = [w for w in stunde if 5 <= w <= 60]
    monat = [float(m.group(1).replace(".", "")) for m in MONAT_RE.finditer(text)]
    monat = [w for w in monat if 100 <= w <= 6000]
    return (max(stunde) if stunde else None), (max(monat) if monat else None)


def regeln_laden():
    with open(REGELN_DATEI, "rb") as fh:
        r = tomllib.load(fh)
    for art in ("plus", "ausschluss", "warnung", "nicht_jugend"):
        for regel in r.get(art, []):
            regel["re"] = re.compile(regel["muster"])
    return r


def _ausschnitt(text, m, rand=40):
    """Textstelle um den Treffer, an Wortgrenzen geschnitten (kein „ache mit …“ mitten im Wort)."""
    a, b = max(0, m.start() - rand), min(len(text), m.end() + rand)
    if a and not text[a - 1].isspace():
        a = text.find(" ", a, m.start()) + 1 or a      # angeschnittenes erstes Wort weglassen
    if b < len(text) and not text[b].isspace():
        b = text.rfind(" ", m.end(), b) if text.rfind(" ", m.end(), b) > 0 else b
    return ("…" if a else "") + text[a:b].strip() + ("…" if b < len(text) else "")


def _suche(regel, titel, text, verneinung_pruefen, roh=None):
    """Sucht im kleingeschriebenen Text; der Ausschnitt kommt aus roh (Originalschreibung), wenn gleich lang."""
    quelle = titel if regel.get("nur_titel") else text   # titel = Titel + Berufsbezeichnung
    for m in regel["re"].finditer(quelle):
        if verneinung_pruefen and VERNEINUNG_RE.search(quelle[max(0, m.start() - 30):m.start()]):
            continue
        original = (roh or {}).get("titel" if regel.get("nur_titel") else "text", "")
        return _ausschnitt(original if len(original) == len(quelle) else quelle, m)
    return None


def bewerten(anzeige, regeln):
    titel_roh = anzeige.titel + " " + anzeige.beruf
    titel = titel_roh.lower()
    roh = re.sub(r"\s+", " ", " ".join([anzeige.titel, anzeige.firma, anzeige.text]))
    text = roh.lower()
    original = {"titel": titel_roh, "text": roh}
    p = regeln["punkte"]
    gruende, punkte, jugend, saison, ferien = [], 0, False, bool(anzeige.befristet), False
    if anzeige.befristet:
        gruende.append(Grund("info", "befristet laut Anzeige"))

    for regel in regeln.get("plus", []):
        if (stelle := _suche(regel, titel, text, True, original)) is not None:
            punkte += regel["punkte"]
            jugend |= regel.get("jugend", False)
            saison |= regel.get("saison", False)
            ferien |= regel.get("ferien", False)
            gruende.append(Grund("plus", regel["grund"], regel["punkte"], stelle))
    for art in ("ausschluss", "warnung"):
        for regel in regeln.get(art, []):
            if (stelle := _suche(regel, titel, text, True, original)) is not None:
                gruende.append(Grund(art, regel["grund"], fundstelle=stelle,
                                     kategorie=regel.get("kategorie", "")))

    for regel in regeln.get("nicht_jugend", []):
        if jugend and (stelle := _suche(regel, titel, titel, False, {"titel": titel_roh, "text": titel_roh})) is not None:
            jugend = False
            gruende.append(Grund("info", regel["grund"], fundstelle=stelle))

    # „befristet“ oder „Aushilfe für …“ im Text, aber der Vertrag ist laut Anzeige unbefristet: kein Ferienjob
    if saison and anzeige.befristet is not True and not ferien and (stelle := _suche(UNBEFRISTET, text, text, False, original)):
        saison = False
        gruende.append(Grund("info", "laut Anzeige unbefristet", fundstelle=stelle))

    if anzeige.schicht_nacht_wochenende:
        gruende.append(Grund("warnung", "laut Anzeige Schicht-, Nacht- oder Wochenendarbeit"))
    if anzeige.minijob:
        punkte += p["minijob"]
        gruende.append(Grund("plus", "Minijob", p["minijob"]))

    # Strukturierte Angaben der Quelle gelten nur in derselben Spanne wie Angaben aus dem Text (sonst „1e9 €“ oben in der Sortierung)
    lohn_h = anzeige.lohn_stunde if isinstance(anzeige.lohn_stunde, (int, float)) and 5 <= anzeige.lohn_stunde <= 60 else None
    lohn_m = anzeige.lohn_monat if isinstance(anzeige.lohn_monat, (int, float)) and 100 <= anzeige.lohn_monat <= 6000 else None
    lohn_quelle = "Angabe" if (lohn_h or lohn_m) else ""
    if not lohn_quelle:
        lohn_h, lohn_m = lohn_finden(roh)
        lohn_quelle = "Text" if (lohn_h or lohn_m) else ""
    if lohn_h:
        punkte += p["lohn_angegeben"]
        gruende.append(Grund("plus", "Stundenlohn genannt", p["lohn_angegeben"]))

    aus = [g for g in gruende if g.art == "ausschluss"]
    if aus:
        punkte -= p["ausschluss_abzug"]
        eignung = "ab 18" if any(g.kategorie == "ab18" for g in aus) else "ungeeignet"
    elif jugend and punkte >= p["schwelle_passt"] and not any(g.art == "warnung" for g in gruende):
        eignung = "passt"
    else:
        eignung = "prüfen"
    if not anzeige.details_geladen and anzeige.quelle == "Jobbörse":
        gruende.append(Grund("info", "nur Titel geprüft, Anzeigentext nicht geladen"))

    gruppen = [] if aus else ["ferien"] if ferien or jugend else ["saison"] if saison else ["weitere"]
    return Bewertung(punkte, eignung, gruende, lohn_h, lohn_m, lohn_quelle, gruppen)
