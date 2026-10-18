"""Alle Quellen abfragen, entdoppeln, Volltexte nachladen, bewerten, sortieren."""

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from . import netz
from .bewertung import bewerten, regeln_laden
from .modell import Treffer, bereinigen
from .quellen import ba, feeds

WURZEL = Path(__file__).resolve().parent.parent


def toml(name):
    with open(WURZEL / name, "rb") as fh:
        return tomllib.load(fh)


@dataclass
class Ergebnis:
    ort: str
    umkreis: int
    treffer: list[Treffer]
    feste: list[dict]                                 # Arbeitgeber-Hinweise ohne Einzelanzeigen
    fehler: list[str] = field(default_factory=list)   # Quellen, die nicht erreichbar waren, mit Fehlermeldung (nur Terminal)
    ausgefallen: list[str] = field(default_factory=list)   # nur deren Namen, für die Seite: keine Adressen, keine Technik

    @property
    def zahlen(self):
        t = self.treffer
        ohne = [x for x in t if not x.bewertung.ausschluesse]
        gruppe = lambda g: sum(1 for x in t if g in x.bewertung.gruppen)
        return {"anzeigen": len(t), "ohne_ausschluss": len(ohne),
                "mit_lohn": sum(1 for x in ohne if x.bewertung.lohn_stunde or x.bewertung.lohn_monat),
                "passt": sum(1 for x in t if x.bewertung.eignung == "passt"),
                "ferien": gruppe("ferien"), "saison": gruppe("saison"), "weitere": gruppe("weitere"),
                "aussortiert": len(t) - len(ohne)}


def _schluessel(a):
    # ponytail: grobe quellenübergreifende Entdopplung über Firma + Titel + Ort;
    # gleiche Stelle mit abweichendem Titel bleibt doppelt.
    norm = lambda s: re.sub(r"\W+|\b[mwd]\b", "", s.lower())
    return norm(a.firma)[:10], norm(a.titel), norm(a.ort)


def suchen(ort, umkreis, *, region=None, weitere_orte=(), details=None, mit_feeds=True, log=lambda s: None):
    """region (z. B. "BERLIN") filtert nach Bundesland laut Quelle; ohne region alle Treffer im Umkreis.
    weitere_orte: zusätzliche (Ort, Umkreis), z. B. um ein ganzes Bundesland abzudecken; eine Abfrage liefert höchstens 1.000 Treffer."""
    e, ag = toml("einstellungen.toml")["jobboerse"], toml("arbeitgeber.toml")
    regeln = regeln_laden()
    cache, fehler, ausgefallen, gefunden = e["cache_stunden"], [], [], {}

    abfragen = e["abfragen"]
    orte = [(ort, umkreis), *[tuple(o) for o in weitere_orte]]
    for o, u in orte:
        vor = f"{o}: " if len(orte) > 1 else ""
        for a in abfragen:
            for was in a.get("begriffe") or [None]:
                label = was or a["name"]
                try:
                    liste = ba.suche(o, u, was=was, arbeitszeit=a.get("arbeitszeit"),
                                     tage=e["tage"], seiten=e["seiten"], cache_stunden=cache)
                except netz.Fehler as x:
                    fehler.append(f"Jobbörse ({vor}{label}): {x}")
                    ausgefallen.append("Jobbörse der Bundesagentur für Arbeit")
                    continue
                log(f"  Jobbörse {vor}{label}: {len(liste)}")
                for anz in liste:
                    treffer_ = gefunden.setdefault((anz.quelle, anz.id), anz)
                    if label not in treffer_.suchbegriffe:
                        treffer_.suchbegriffe.append(label)

        if mit_feeds:
            for f in ag.get("feed", []):
                try:
                    liste = feeds.suche(f, o, u, ag["berlin"], cache_stunden=cache)
                except Exception as x:  # noqa: BLE001 – ein kaputter Feed darf die Suche nicht abbrechen
                    fehler.append(f"{f['name']}: {type(x).__name__}: {x}")
                    ausgefallen.append(f["name"])
                    continue
                log(f"  {vor}{f['name']}: {len(liste)}")
                for anz in liste:
                    gefunden.setdefault((anz.quelle, anz.id), anz)

    eindeutig = {}
    for anz in gefunden.values():
        eindeutig.setdefault(_schluessel(anz), anz)
    anzeigen = [a for a in eindeutig.values() if not region or a.region == region]

    # Volltext nur für die vielversprechendsten Anzeigen der Jobbörse (schont die Schnittstelle)
    n = e["details"] if details is None else details
    kandidaten = sorted((a for a in anzeigen if a.quelle == ba.QUELLE and not a.details_geladen),
                        key=lambda a: bewerten(a, regeln).punkte, reverse=True)[:n]
    for i, a in enumerate(kandidaten, 1):
        try:
            ba.details_laden(a)
        except netz.Fehler as x:
            fehler.append(f"Jobbörse Details {a.id}: {x}")
            ausgefallen.append("Jobbörse der Bundesagentur für Arbeit (Volltexte)")
        log(f"\r  Volltext {i}/{len(kandidaten)}")

    treffer = [Treffer(bereinigen(a), bewerten(a, regeln)) for a in anzeigen]
    treffer.sort(key=lambda t: (t.bewertung.punkte, t.bewertung.lohn_stunde or 0), reverse=True)
    feste = [f for f in ag.get("fest", []) if (region in f.get("regionen", []) if region else
             f["ort"] == "bundesweit" or feeds.im_gebiet(f["ort"], "", ort, umkreis, ag["berlin"]))]
    return Ergebnis(ort, umkreis, treffer, feste, fehler, list(dict.fromkeys(ausgefallen)))
