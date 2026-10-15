"""Jobbörse der Bundesagentur für Arbeit.

Inoffiziell dokumentiert unter https://github.com/bundesAPI/jobsuche-api.
Suche über /pc/v6/jobs (v4 liefert seit Oktober 2026 HTTP 403), Details über /pc/v4/jobdetails.
"""

import base64
import re
import urllib.parse

from .. import netz
from ..modell import Anzeige

API = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service"
HEADER = {"X-API-Key": "jobboerse-jobsuche", "Accept": "application/json"}
QUELLE = "Jobbörse"


def alle_texte(obj):
    """Alle Textwerte eines verschachtelten JSON-Objekts (robust gegen Feldnamen-Änderungen).
    Ohne Feldkennungen (BEFRISTET, STUNDENLOHN), Datumsangaben und reine Zahlen: Die stehen als eigene
    Felder bereit und machten die Textausschnitte in „Warum …?“ unlesbar."""
    if isinstance(obj, str):
        return [] if re.fullmatch(r"[A-Z_]+|[\d\s.:+T-]+", obj.strip()) else [obj]
    if isinstance(obj, dict):
        return [t for v in obj.values() for t in alle_texte(v)]
    if isinstance(obj, list):
        return [t for v in obj for t in alle_texte(v)]
    return []


# Daten der Jobbörse sind fremd: Werte vor dem Zugriff auf den erwarteten Typ prüfen, alles andere gilt als leer
# (eine verstümmelte Anzeige darf die Suche nicht abbrechen, Prüfhandbuch 3.1)
def _obj(x):
    return x if isinstance(x, dict) else {}


def _text(x):
    return x if isinstance(x, str) else ""


def _lohn(j):
    """Strukturierte Lohnangabe der Anzeige: (Stunde, Monat)."""
    wert = j.get("festgehalt") or j.get("gehaltsspanneVon")
    if not isinstance(wert, (int, float)) or isinstance(wert, bool) or not 0 < wert < 1e6:
        return None, None
    art = j.get("verguetungsangabe")
    if art == "STUNDENLOHN":
        return float(wert), None
    if art == "MONATSGEHALT":
        return None, float(wert)
    return None, None


def anzeige_aus(j):
    j = _obj(j)
    orte = j.get("stellenlokationen")
    adr = _obj(_obj(orte[0] if isinstance(orte, list) and orte else {}).get("adresse"))
    ref = _text(j.get("referenznummer"))
    lohn_h, lohn_m = _lohn(j)
    minijob = j.get("istGeringfuegigeBeschaeftigung")
    return Anzeige(
        quelle=QUELLE,
        id=ref,
        titel=_text(j.get("stellenangebotsTitel")) or _text(j.get("hauptberuf")),
        firma=_text(j.get("firma")),
        ort=_text(adr.get("ort")),
        plz=_text(adr.get("plz")),
        region=_text(adr.get("region")),
        link=f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{urllib.parse.quote(ref)}",
        text=" ".join(alle_texte(j.get("alleBerufe") or [])),
        veroeffentlicht=_text(j.get("datumErsteVeroeffentlichung")),
        eintritt=_text(_obj(j.get("eintrittszeitraum")).get("von")),
        minijob=minijob if isinstance(minijob, bool) else None,
        befristet={"BEFRISTET": True, "UNBEFRISTET": False}.get(_text(j.get("vertragsdauer"))),
        beruf=_text(j.get("hauptberuf")),
        schicht_nacht_wochenende=bool(j.get("arbeitszeitSchichtNachtWochenende")),
        lohn_stunde=lohn_h,
        lohn_monat=lohn_m,
    )


def suche(ort, umkreis, *, was=None, arbeitszeit=None, tage=30, seiten=5, cache_stunden=6):
    """Rohsuche, liefert Anzeigen (ohne Volltext)."""
    treffer = []
    for page in range(1, seiten + 1):
        params = {"wo": ort, "umkreis": umkreis, "angebotsart": 1, "page": page, "size": 100,
                  "veroeffentlichtseit": tage, "zeitarbeit": "false"}
        if was:
            params["was"] = was
        if arbeitszeit:
            params["arbeitszeit"] = arbeitszeit
        data = netz.get_json(f"{API}/pc/v6/jobs?{urllib.parse.urlencode(params)}",
                             headers=HEADER, cache_stunden=cache_stunden)
        liste = _obj(data).get("ergebnisliste")
        liste = liste if isinstance(liste, list) else []
        treffer += [a for a in (anzeige_aus(j) for j in liste if isinstance(j, dict)) if a.id and a.titel]
        if len(liste) < 100:
            break
    return treffer


def details_laden(anzeige, cache_stunden=24):
    """Ergänzt Volltext und strukturierte Angaben aus /jobdetails."""
    code = base64.b64encode(anzeige.id.encode()).decode()
    det = netz.get_json(f"{API}/pc/v4/jobdetails/{code}", headers=HEADER, cache_stunden=cache_stunden)
    if not isinstance(det, dict) or not det:
        return anzeige
    anzeige.text = " ".join([anzeige.text] + alle_texte(det))
    anzeige.details_geladen = True
    anzeige.schicht_nacht_wochenende |= bool(det.get("arbeitszeitSchichtNachtWochenende"))
    if anzeige.lohn_stunde is None and anzeige.lohn_monat is None:
        anzeige.lohn_stunde, anzeige.lohn_monat = _lohn(det)
    if str(det.get("externeUrl") or "").lower().startswith(("https://", "http://")):
        anzeige.link = det["externeUrl"]  # sonst bleibt der Link zur Jobbörse
    return anzeige
