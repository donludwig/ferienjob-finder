"""Gemeinsames Format aller Quellen und das Ergebnis der Bewertung."""

import re
import unicodedata
from dataclasses import dataclass, field


@dataclass
class Anzeige:
    quelle: str            # z. B. "Jobbörse", "Vapiano"
    id: str                # eindeutig innerhalb der Quelle
    titel: str
    firma: str = ""
    ort: str = ""
    plz: str = ""
    region: str = ""       # Bundesland laut Quelle, z. B. "BERLIN", "BRANDENBURG"
    link: str = ""
    text: str = ""         # Volltext, soweit geladen
    veroeffentlicht: str = ""
    eintritt: str = ""
    minijob: bool | None = None
    befristet: bool | None = None      # laut Quelle; None = keine Angabe
    beruf: str = ""                    # Berufsbezeichnung der Quelle (Jobbörse: hauptberuf)
    schicht_nacht_wochenende: bool = False
    lohn_stunde: float | None = None   # strukturierte Angabe der Quelle
    lohn_monat: float | None = None
    details_geladen: bool = False
    suchbegriffe: list[str] = field(default_factory=list)


@dataclass
class Grund:
    art: str               # "plus", "ausschluss", "warnung", "info"
    text: str
    punkte: int = 0
    fundstelle: str = ""   # Textausschnitt, in dem die Regel gegriffen hat
    kategorie: str = ""    # bei Ausschlüssen: "ab18" oder leer


@dataclass
class Bewertung:
    punkte: int
    eignung: str           # "passt", "prüfen", "ab 18", "ungeeignet"
    gruende: list[Grund]
    lohn_stunde: float | None
    lohn_monat: float | None
    lohn_quelle: str       # "Angabe", "Text" oder ""
    gruppen: list[str] = field(default_factory=list)   # "ferien", "schueler", "weitere"

    @property
    def ausschluesse(self):
        return [g.text for g in self.gruende if g.art == "ausschluss"]

    @property
    def warnungen(self):
        return [g.text for g in self.gruende if g.art == "warnung"]


@dataclass
class Treffer:
    anzeige: Anzeige
    bewertung: Bewertung


_DATUM = re.compile(r"\d{4}-\d{2}-\d{2}")


def _sichtbar(s):
    # Steuer- und Formatzeichen (Bidi, Zero-Width) können Titel optisch umdrehen oder verstecken
    return "".join(c for c in s if c in "\n\t" or unicodedata.category(c) not in ("Cc", "Cf"))


def bereinigen(a):
    """Daten von außen vor der Ausgabe: sichtbare Zeichen, nur http(s)-Links (kein javascript: o. ä.)."""
    for f in ("id", "titel", "firma", "ort", "plz", "region", "text", "beruf"):
        setattr(a, f, _sichtbar(getattr(a, f) or ""))
    for f in ("veroeffentlicht", "eintritt"):   # nur echte Datumsangaben (JJJJ-MM-TT…), sonst leer
        wert = str(getattr(a, f) or "")
        setattr(a, f, wert if _DATUM.match(wert) else "")
    if not a.link.lower().startswith(("https://", "http://")):
        a.link = ""
    return a
