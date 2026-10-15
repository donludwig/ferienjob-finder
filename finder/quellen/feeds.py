"""Offene Stellen-Feeds einzelner Arbeitgeber (Liste in arbeitgeber.toml)."""

import html
import json
import re
import xml.etree.ElementTree as ET

from .. import netz
from ..modell import Anzeige

TT = "{https://teamtailor.com/locations}"


def _klartext(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def personio(xml_text, name, url):
    basis = url.rsplit("/xml", 1)[0]
    out = []
    for p in ET.fromstring(xml_text).iter("position"):
        texte = [d.findtext("value") or "" for d in p.iter("jobDescription")]
        pid = p.findtext("id", "")
        out.append(Anzeige(
            quelle=name, id=pid, titel=p.findtext("name", ""), firma=name,
            ort=p.findtext("office", ""), link=f"{basis}/job/{pid}",
            text=_klartext(" ".join(texte + [p.findtext("schedule", ""), p.findtext("employmentType", "")])),
            veroeffentlicht=(p.findtext("createdAt") or "")[:10],
            befristet={"temporary": True, "permanent": False}.get(p.findtext("employmentType", "")),
            details_geladen=True,
        ))
    return out


def _zahl(x):
    try:
        wert = float(x)
    except (TypeError, ValueError):
        return None
    return wert if 0 < wert < 1e6 else None


def recruitee(json_data, name, url):
    """JSON fremder Herkunft: Einträge, die kein Objekt sind, und Felder mit falschem Typ gelten als leer (Prüfhandbuch 3.1)."""
    t = lambda x: x if isinstance(x, str) else ""
    angebote = json_data.get("offers") if isinstance(json_data, dict) else None
    out = []
    for o in angebote if isinstance(angebote, list) else []:
        if not isinstance(o, dict):
            continue
        sal = o.get("salary") if isinstance(o.get("salary"), dict) else {}
        lohn_h = _zahl(sal.get("min")) if sal.get("period") == "hour" else None
        lohn_m = _zahl(sal.get("min")) if sal.get("period") == "month" else None
        art = t(o.get("employment_type_code"))
        out.append(Anzeige(
            quelle=name, id=str(o.get("id") or ""), titel=t(o.get("title")), firma=name,
            ort=t(o.get("city")), plz=t(o.get("postal_code")), link=t(o.get("careers_url")),
            text=_klartext(" ".join([t(o.get("description")), t(o.get("requirements")), art])),
            veroeffentlicht=t(o.get("published_at"))[:10],
            lohn_stunde=lohn_h, lohn_monat=lohn_m, details_geladen=True,
            befristet=("fixed_term" in art) or None,
        ))
    return [a for a in out if a.id and a.titel]


def teamtailor(xml_text, name, url):
    out = []
    for i in ET.fromstring(xml_text).iter("item"):
        loc = i.find(f"{TT}locations/{TT}location")
        out.append(Anzeige(
            quelle=name, id=i.findtext("guid", ""), titel=i.findtext("title", ""), firma=name,
            ort=(loc.findtext(f"{TT}city", "") if loc is not None else "").strip(),
            plz=(loc.findtext(f"{TT}zip", "") if loc is not None else "").strip(),
            link=i.findtext("link", ""), text=_klartext(i.findtext("description", "")),
            details_geladen=True,
        ))
    return out


LESER = {"personio": (personio, False), "recruitee": (recruitee, True), "teamtailor": (teamtailor, False)}


def im_gebiet(a_ort, plz, ort, umkreis, berlin):
    """Grober Ortsfilter für Feeds, die keine Umkreissuche können."""
    # ponytail: Ortsnamen und PLZ statt Geokodierung. Umland-Liste gibt es nur für Berlin;
    # für andere Orte zählt nur der Ortsname. Koordinaten nachrüsten, wenn weitere Regionen dazukommen.
    a_ort, ort = a_ort.lower(), ort.lower()
    if ort in a_ort:
        return True
    if ort != "berlin":
        return False
    if plz[:2] in berlin["plz_praefix"]:
        return True
    return umkreis >= berlin["umland_ab_km"] and any(o.lower() in a_ort for o in berlin["umland_orte"])


def region_von(a_ort, plz, berlin):
    """Bundesland für Feed-Anzeigen ohne Angabe: Berlin über PLZ oder Ortsnamen, sonst Umland-Liste."""
    if plz[:2] in berlin["plz_praefix"] or "berlin" in a_ort.lower():
        return "BERLIN"
    if any(o.lower() in a_ort.lower() for o in berlin["umland_orte"]):
        return "BRANDENBURG"
    return ""


def suche(feed, ort, umkreis, berlin, cache_stunden=6):
    leser, ist_json = LESER[feed["art"]]
    body = netz.get(feed["url"], cache_stunden=cache_stunden)
    if not body:
        return []
    daten = json.loads(body) if ist_json else body
    anzeigen = leser(daten, feed["name"], feed["url"])
    for a in anzeigen:
        a.ort = feed.get("ort") or a.ort
        a.region = region_von(a.ort, a.plz, berlin)
    return [a for a in anzeigen if im_gebiet(a.ort, a.plz, ort, umkreis, berlin)]
