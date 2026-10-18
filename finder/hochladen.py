"""Den Ordner ausgabe/ per FTP(S) hochladen.

Zugang aus ftp.toml (nicht im Repo), Passwort aus dem macOS-Schlüsselbund
(Dienst „ferienjob-finder-ftp“) oder aus der Umgebungsvariable FTP_PASSWORT.
"""

import ftplib
import io
import os
import ssl
import subprocess
import tomllib
from pathlib import Path

from .suche import WURZEL

DIENST = "ferienjob-finder-ftp"
LISTE = "ferienjob-dateien.txt"  # Liste der hochgeladenen Dateien auf dem Server; gelöscht wird nur, was dort steht
MARKE = ".ferienjob-ausgabe"     # kennzeichnet einen Ausgabeordner des Baus (ausgabe.py), wird nicht hochgeladen


def zugang(datei=WURZEL / "ftp.toml"):
    if not datei.exists():
        raise SystemExit(f"{datei.name} fehlt – Vorlage: ftp.beispiel.toml")
    with open(datei, "rb") as fh:
        cfg = tomllib.load(fh)
    pw = os.environ.get("FTP_PASSWORT")
    if not pw:
        r = subprocess.run(["security", "find-generic-password", "-s", DIENST, "-a", cfg["benutzer"], "-w"],
                           capture_output=True, text=True)
        if r.returncode:
            raise SystemExit(f"Kein Passwort im Schlüsselbund (Dienst {DIENST}, Konto {cfg['benutzer']}).")
        pw = r.stdout.strip()
    return cfg, pw


def _ordner(ftp, pfad, start):
    """Wechselt in pfad (absolut oder relativ zum Login-Ordner) und legt fehlende Ordner an."""
    ftp.cwd("/" if pfad.startswith("/") else start)
    for teil in [t for t in pfad.split("/") if t]:
        try:
            ftp.cwd(teil)
        except ftplib.error_perm:
            ftp.mkd(teil)
            ftp.cwd(teil)


def _groesse(ftp, name):
    try:
        return ftp.size(name)
    except ftplib.error_perm:
        return None


def _ersetzen(ftp, neu, name):
    try:
        ftp.rename(neu, name)
    except ftplib.error_perm:  # manche Server benennen nicht über bestehende Dateien
        ftp.delete(name)
        ftp.rename(neu, name)


def _liste_lesen(ftp):
    buf = io.BytesIO()
    try:
        ftp.retrbinary(f"RETR {LISTE}", buf.write)
    except ftplib.error_perm:
        return set()
    return set(buf.getvalue().decode("utf-8").split())


def hochladen(quelle, cfg, passwort, log=print):
    quelle = Path(quelle)
    dateien = sorted(p for p in quelle.rglob("*") if p.is_file() and p.name != MARKE)
    if not (quelle / "index.html").exists():
        raise SystemExit(f"{quelle}/index.html fehlt – erst bauen.")

    # ftplib prüft das Zertifikat ohne eigenen Kontext nicht: dann könnte ein Mittelsmann das Passwort mitlesen
    ftp = (ftplib.FTP_TLS(cfg["host"], timeout=60, context=ssl.create_default_context()) if cfg.get("tls", True)
           else ftplib.FTP(cfg["host"], timeout=60))
    with ftp:
        ftp.login(cfg["benutzer"], passwort)
        if cfg.get("tls", True):
            ftp.prot_p()  # auch die Daten verschlüsselt übertragen
        ftp.voidcmd("TYPE I")
        start = ftp.pwd()
        if not str(cfg.get("verzeichnis", "")).strip():
            raise SystemExit("ftp.toml: verzeichnis ist leer – den Zielordner ausdrücklich angeben (z. B. \"/\").")
        basis = cfg["verzeichnis"].rstrip("/") or "/"
        _ordner(ftp, basis, start)
        vorher = _liste_lesen(ftp)
        # Schutz vor einem falschen Zielordner: Ohne eigene Dateiliste wird nur in einen leeren Ordner hochgeladen.
        # Sonst würden fremde Dateien wie index.html oder .htaccess einer anderen Seite überschrieben.
        if not vorher:
            fremd = [n for n in ftp.nlst() if n.rsplit("/", 1)[-1] not in (".", "..")]
            if fremd and not cfg.get("ordner_uebernehmen"):
                raise SystemExit(f"{cfg['host']}{basis} enthält schon {len(fremd)} Dateien, aber keine {LISTE} – "
                                 "falscher Zielordner? Wenn der Ordner wirklich ersetzt werden soll: ordner_uebernehmen = true "
                                 "in ftp.toml (einmalig).")
        # Gelöscht werden nur Einträge der eigenen Liste, die im Zielordner bleiben (kein .., kein absoluter Pfad)
        vorher = {r for r in vorher if not r.startswith("/") and ".." not in r.split("/")}
        hoch = gleich = 0
        for p in dateien:
            rel = p.relative_to(quelle)
            _ordner(ftp, f"{basis}/{rel.parent}" if str(rel.parent) != "." else basis, start)
            # KERN (Schriften, CSS) ändert sich nur bei Updates: gleiche Größe = überspringen
            if rel.parts[0] == "kern" and _groesse(ftp, p.name) == p.stat().st_size:
                gleich += 1
                continue
            # Erst unter Zwischennamen hochladen, dann umbenennen: niemand sieht halbe Dateien
            with open(p, "rb") as fh:
                ftp.storbinary(f"STOR {p.name}.neu", fh)
            _ersetzen(ftp, f"{p.name}.neu", p.name)
            hoch += 1
        # Dateien früherer Läufe entfernen (z. B. weggefallene Seitenzahlen) – nur eigene, laut Liste
        _ordner(ftp, basis, start)
        jetzt = {p.relative_to(quelle).as_posix() for p in dateien}
        alt = sorted(vorher - jetzt)
        for rel in alt:
            try:
                ftp.delete(rel)
            except ftplib.error_perm:
                pass  # schon weg
        ftp.storbinary(f"STOR {LISTE}", io.BytesIO("\n".join(sorted(jetzt)).encode("utf-8")))
    log(f"Hochgeladen: {hoch}, unverändert: {gleich}, gelöscht: {len(alt)} → {cfg['host']}{basis}")
