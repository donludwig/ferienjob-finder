# Bedrohungsmodell des Ferienjob-Finders

Kurzfassung: was geschützt wird, wem vertraut wird, über welche Wege Daten hereinkommen und welche Prüfung jede Annahme absichert. Das Dokument wird bei jeder neuen Quelle, jedem neuen Ausgabeformat und jedem neuen Weg auf den Server angepasst.

## Aufbau

Ein Python-Generator läuft auf einem Rechner, fragt die Jobbörse der Bundesagentur für Arbeit, einige Arbeitgeber-Feeds und die OpenHolidays-Schnittstelle ab, bewertet die Anzeigen und baut statische Seiten (HTML, CSV, JSON). Die Seiten werden von Hand per FTPS auf einen Webspace geladen. Auf dem Server läuft kein eigener Code; JavaScript im Browser filtert und sortiert nur, was schon in der Seite steht.

## Was geschützt wird

- Die Besucher:innen, meist Jugendliche und Eltern: Die Seite darf kein fremdes Skript, keinen fremden Stil und keinen irreführenden Link ausliefern, keine Daten über sie sammeln und keine Formel in ihr Tabellenprogramm schmuggeln.
- Die Website selbst: Niemand außer Don darf sie verändern; ein Fehler im Upload darf keine fremden Dateien auf dem Webspace überschreiben oder löschen.
- Der Rechner, auf dem gebaut wird: Antworten der Quellen dürfen den Bau nicht abbrechen, keinen Ordner außerhalb der Ausgabe leeren und keinen Speicher fluten.

## Vertrauen

| Wer oder was | Vertrauen |
|---|---|
| Besucher:in | keines; Adresszeile und Browserspeicher gelten als feindlich |
| Jobbörse, Arbeitgeber-Feeds, OpenHolidays | keines; jedes Feld kann fehlen, den falschen Typ haben, Markup, Steuerzeichen, Formeln oder gefährliche Links enthalten |
| KERN, Lucide, Python-Pakete | geprüft beim Einbinden (feste Versionen, Byte-Vergleich, OSV, Trivy), danach vertraut |
| Don und der Rechner, auf dem gebaut wird | volles Vertrauen; ein kompromittierter Rechner liegt außerhalb des Modells |
| Hoster (manitu) | vertraut für Auslieferung, HSTS und Log-Anonymisierung; geregelt im AV-Vertrag |

## Wege hinein

| Weg | Annahme | Abgesichert durch |
|---|---|---|
| Suche und Details der Jobbörse (JSON) | beliebige Typen, Riesenwerte, Markup, Steuerzeichen, `javascript:`-Links, unplausible Löhne | Typprüfung beim Einlesen, `modell.bereinigen` (Links nur http(s), Steuerzeichen raus, Datum nur als Datum), Lohnspannen, Größengrenze 20 MB; Tests mit Nutzlasten durch die ganze Strecke, Fuzzing mit 1000 Anzeigen, Mutationstest |
| Arbeitgeber-Feeds (XML, JSON) | kaputt, bösartig, Entity-Angriffe | expat mit Schutz gegen Entity-Expansion, ein kaputter Feed fällt einzeln aus; Fuzzing mit 600 beschädigten Feeds |
| Fehler der Quellen | Meldungen enthalten Adressen und technische Details | auf der Seite nur der Name der Quelle, Details nur im Terminal; Test |
| Adresszeile (`?theme=`) und Browserspeicher | beliebiger Text | nur feste Werte (`light`, `dark`), Ausgabe nie als Markup |
| Konfiguration (`ftp.toml`, Einstellungen) | Tippfehler | leerer Zielordner ist ein Fehler, Upload nur in einen leeren oder eigenen Ordner, Bau leert nur einen markierten Ausgabeordner; Tests |
| Dateiliste auf dem Server | kann manipuliert sein | gelöscht wird nur, was in der eigenen Liste steht, ohne `..` und absolute Pfade; Test |

## Wege hinaus

| Weg | Annahme | Abgesichert durch |
|---|---|---|
| HTML-Seiten | jeder Wert aus den Quellen ist feindlich | Jinja2 maskiert alles, keine Inline-Skripte und -Stile, Content-Security-Policy `default-src 'self'` mit `object-src`, `base-uri`, `form-action`, `frame-ancestors` auf allen Antworten; axe, html-validate, Browser-Prüfung in drei Engines, OWASP ZAP |
| CSV | Tabellenprogramme führen Formeln aus | Zellen mit `= + - @`, Tab, Wagenrücklauf als Text markiert; Test, Mutationstest |
| JSON | wird von Dritten weiterverarbeitet | nur bereinigte Werte |
| Upload | Passwort und Inhalt dürfen nicht mitgelesen werden | FTPS mit Zertifikatsprüfung, Passwort nur im Schlüsselbund; Upload nur von Hand nach ausdrücklicher Freigabe durch Don, kein Zeitplan, kein anderes Skript |

## Bekannte Grenzen

- Ob eine Anzeige seriös ist, prüft der Ferienjob-Finder nicht.
- Die Schnittstelle der Jobbörse ist öffentlich, aber nicht offiziell dokumentiert.
- Keine unabhängige Prüfung durch Dritte, kein Screenreader-Test.
- Die Prüfkette läuft lokal von Hand.
