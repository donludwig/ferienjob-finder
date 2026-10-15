import json
from datetime import date

from finder import ferien, netz


def test_tabelle_fuehrt_laender_zusammen(monkeypatch):
    d = date.fromisoformat
    daten = {
        "DE-BE": [("Sommerferien", d("2028-07-01"), d("2028-08-12")), ("Unterrichtsfreier Tag", d("2028-05-26"), d("2028-05-26")),
                  ("Pfingstferien", d("2028-06-01"), d("2028-06-02"))],
        "DE-BB": [("Sommerferien", d("2028-06-29"), d("2028-08-12")), ("Variabler Ferientag", d("2028-05-26"), d("2028-05-26"))],
    }
    monkeypatch.setattr(ferien, "liste", lambda land, von, bis: daten[land])
    t = ferien.tabelle(["DE-BE", "DE-BB"], d("2028-01-01"), d("2028-12-31"))
    namen = [n for n, _ in t[2028]]
    assert namen == ["Einzelner freier Tag", "Pfingstferien", "Sommerferien"]   # sortiert nach dem frühesten Beginn
    sommer = dict(t[2028])["Sommerferien"]
    assert set(sommer) == {"DE-BE", "DE-BB"}                                       # eine Zeile trotz Juni/Juli
    assert set(dict(t[2028])["Pfingstferien"]) == {"DE-BE"}                       # nur Berlin


def test_naechste_laufende_vor_kommenden(monkeypatch):
    daten = [{"startDate": "2026-12-21", "endDate": "2027-01-02", "name": [{"language": "DE", "text": "Weihnachtsferien"}]},
             {"startDate": "2026-10-19", "endDate": "2026-10-31", "name": [{"language": "EN", "text": "Autumn"}, {"language": "DE", "text": "Herbstferien"}]},
             {"startDate": "2026-07-09", "endDate": "2026-08-22", "name": [{"language": "DE", "text": "Sommerferien"}]}]
    monkeypatch.setattr(netz, "get_json", lambda *a, **k: json.loads(json.dumps(daten)))
    assert ferien.naechste("DE-BE", heute=date(2026, 10, 20)) == ("Herbstferien", date(2026, 10, 19), date(2026, 10, 31))
    assert ferien.naechste("DE-BE", heute=date(2026, 11, 1))[0] == "Weihnachtsferien"
    monkeypatch.setattr(netz, "get_json", lambda *a, **k: None)
    assert ferien.naechste("DE-BE", heute=date(2026, 11, 1)) is None
