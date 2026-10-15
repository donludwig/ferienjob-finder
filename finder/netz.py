"""HTTP-Abruf mit Wiederholung, Pause und Datei-Cache.

Gecacht werden nur Antworten der Quellen (Anzeigen), nie Suchanfragen von Personen
zusammen mit Zeit oder Herkunft.
"""

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

UA = "ferienjob-finder/0.1 (Open-Source-Suche nach Ferienjobs)"
CACHE = Path(os.environ.get("FINDER_CACHE", ".cache"))
PAUSE = 0.3  # Sekunden nach jedem echten Abruf, schont die Quellen
GRENZE = 20_000_000  # Bytes je Antwort; größere Antworten gelten als unbrauchbar


class Fehler(Exception):
    """Quelle nicht erreichbar oder Antwort unbrauchbar."""


def get(url, headers=None, cache_stunden=6, versuche=4):
    """Liefert den Antworttext (str). 404 ergibt None."""
    datei = cache_datei(url)
    if cache_stunden and datei.exists() and time.time() - datei.stat().st_mtime < cache_stunden * 3600:
        return json.loads(datei.read_text("utf-8"))["body"]

    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    for i in range(versuche):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                roh = r.read(GRENZE + 1)
            if len(roh) > GRENZE:
                raise Fehler(f"{url}: Antwort größer als {GRENZE // 1_000_000} MB")
            body = roh.decode("utf-8", errors="replace")
            break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                body = None
                break
            if e.code in (429, 500, 502, 503, 504) and i < versuche - 1:
                time.sleep(2 ** i)
                continue
            raise Fehler(f"{url}: HTTP {e.code}") from e
        except (urllib.error.URLError, TimeoutError) as e:
            if i < versuche - 1:
                time.sleep(2 ** i)
                continue
            raise Fehler(f"{url}: {e}") from e
    time.sleep(PAUSE)

    if cache_stunden:
        CACHE.mkdir(parents=True, exist_ok=True)
        datei.write_text(json.dumps({"url": url, "body": body}, ensure_ascii=False), "utf-8")
    return body


def cache_datei(url):
    return CACHE / (hashlib.sha256(url.encode()).hexdigest()[:32] + ".json")


def get_json(url, **kw):
    """Wie get, aber geparst. Ungültiges JSON (Wartungsseite, abgeschnittene Antwort) ist ein Fehler der Quelle und
    bleibt nicht im Cache liegen."""
    body = get(url, **kw)
    if body is None:
        return None
    try:
        return json.loads(body)
    except ValueError as e:
        cache_datei(url).unlink(missing_ok=True)
        raise Fehler(f"{url}: keine gültige JSON-Antwort") from e
