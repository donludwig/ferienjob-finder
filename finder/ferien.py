"""Schulferien aus der OpenHolidays API (https://www.openholidaysapi.org, Daten unter ODbL-1.0)."""

import urllib.parse
from datetime import date, timedelta

from . import netz

API = "https://openholidaysapi.org/SchoolHolidays"
QUELLE = "OpenHolidays API (ODbL-1.0)"


def naechste(land="DE-BE", heute=None, tage_voraus=120):
    """Laufende oder nächste Ferien als (Name, Start, Ende) oder None."""
    heute = heute or date.today()
    return next(((n, s, e) for n, s, e in liste(land, heute, heute + timedelta(days=tage_voraus)) if e >= heute), None)


EINZELTAG = ("Unterrichtsfreier Tag", "Variabler Ferientag", "Beweglicher Ferientag")


def liste(land, von, bis):
    """Alle Schulferien eines Landes zwischen von und bis als (Name, Start, Ende), nach Start sortiert."""
    q = urllib.parse.urlencode({"countryIsoCode": land[:2], "subdivisionCode": land, "languageIsoCode": "DE",
                                "validFrom": von.isoformat(), "validTo": bis.isoformat()})
    daten = netz.get_json(f"{API}?{q}", headers={"Accept": "application/json"}, cache_stunden=24) or []
    return sorted(((next((n["text"] for n in f["name"] if n["language"] == "DE"), f["name"][0]["text"]),
                    date.fromisoformat(f["startDate"]), date.fromisoformat(f["endDate"])) for f in daten),
                  key=lambda x: x[1])


def tabelle(laender, von, bis):
    """Ferien mehrerer Länder nebeneinander, je Jahr: {Jahr: [(Name, {Land: (Start, Ende)}), …]}.
    Zeilen werden über Name und Jahr des Beginns zusammengeführt, einzelne freie Tage (je Land anders benannt) zusätzlich über den Monat."""
    zeilen = {}
    for land in laender:
        for name, start, ende in liste(land, von, bis):
            name = "Einzelner freier Tag" if name in EINZELTAG else name
            # Gleiche Ferien beginnen in den Ländern teils in verschiedenen Monaten (Sommer 2028: Juni und Juli)
            monat = start.month if name == "Einzelner freier Tag" else 0
            zeilen.setdefault((start.year, monat, name), {})[land] = (start, ende)
    jahre = {}
    for (jahr, monat, name), werte in sorted(zeilen.items(), key=lambda z: min(v[0] for v in z[1].values())):
        jahre.setdefault(jahr, []).append((name, werte))
    return jahre
