# Hinweise für Coding-Agenten

Ferienjob-Finder: ein Python-Programm, das Anzeigen aus der Jobbörse der Bundesagentur für Arbeit und aus Stellen-Feeds holt, bewertet und daraus eine statische Website mit dem KERN UX-Standard baut. Die README beschreibt Aufbau und Konfiguration; Sicherheit und Prüfungen stehen in `doku/pruefbericht.md` und `doku/bedrohungsmodell.md`.

## Vor jedem Commit

```
.venv/bin/pytest -q                                  # ohne Netzzugriff
.venv/bin/python werkzeuge/pruefen/mutationen.py     # jede Schutzmaßnahme muss einen Test auslösen
.venv/bin/python -m finder bauen && python3 -I werkzeuge/pruefen/kern_klassen.py
```

Dazu bei Änderungen an Vorlagen, CSS oder JavaScript die Browser-Prüfungen aus dem Abschnitt „Prüfungen wiederholen“ in `doku/pruefbericht.md`.

## Regeln

- `static/kern/` bleibt unverändert. Nur `kern-`-Klassen, die im Kit existieren; eigene Klassen mit Präfix `fj-` oder `start-`.
- Keine Inline-Skripte, keine Inline-Stile, keine `style`-Attribute: Die Seiten laufen unter einer Content-Security-Policy mit `default-src 'self'`.
- Keine Anfragen an fremde Server aus den erzeugten Seiten; Schriften, Symbole und Kit liegen lokal.
- Anzeigen aus Jobbörse und Feeds gelten als nicht vertrauenswürdig: nach Typ prüfen, Steuerzeichen entfernen, Links nur mit http oder https, beim Einsetzen maskieren. Jede neue Schutzmaßnahme bekommt einen Test und eine Zeile in `werkzeuge/pruefen/mutationen.py`.
- Die Seiten müssen ohne JavaScript funktionieren; Barrierefreiheit nach WCAG 2.1 AA ist Anforderung.
- Hochgeladen wird nie automatisch. `python -m finder hochladen` nur nach ausdrücklicher Freigabe durch die Person, die die Seite betreibt.
- Keine Zugangsdaten, lokalen Pfade oder persönlichen Daten ins Repositorium; `ftp.toml` und `betreiber.toml` bleiben lokal.
- Neue Änderungen in `CHANGELOG.md` eintragen.
