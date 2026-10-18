import ftplib
import ssl

from finder import hochladen


class FakeFTP:
    """Minimaler FTP-Server im Speicher: Ordner als Pfad-Strings, Dateien als Bytes."""
    dateien = {}

    def __init__(self, host, timeout=None, context=None):
        assert context.verify_mode == ssl.CERT_REQUIRED and context.check_hostname  # Zertifikat wird geprüft
        self.ordner, self.dirs = "/home", {"/", "/home"}

    def __enter__(self): return self
    def __exit__(self, *a): pass
    def login(self, u, p): assert p == "geheim"
    def prot_p(self): pass
    def voidcmd(self, c): pass
    def pwd(self): return self.ordner

    def cwd(self, d):
        ziel = d if d.startswith("/") else f"{self.ordner.rstrip('/')}/{d}"
        if ziel not in self.dirs:
            raise ftplib.error_perm("550")
        self.ordner = ziel

    def mkd(self, d): self.dirs.add(f"{self.ordner.rstrip('/')}/{d}")
    def _p(self, n): return f"{self.ordner}/{n}"

    def size(self, n):
        if self._p(n) not in self.dateien:
            raise ftplib.error_perm("550")
        return len(self.dateien[self._p(n)])

    def storbinary(self, cmd, fh): self.dateien[self._p(cmd.split(" ", 1)[1])] = fh.read()

    def retrbinary(self, cmd, cb):
        n = self._p(cmd.split(" ", 1)[1])
        if n not in self.dateien:
            raise ftplib.error_perm("550")
        cb(self.dateien[n])
    def rename(self, a, b): self.dateien[self._p(b)] = self.dateien.pop(self._p(a))
    def nlst(self): return [k.rsplit("/", 1)[1] for k in self.dateien if k.rsplit("/", 1)[0] == self.ordner]
    def delete(self, n): del self.dateien[self._p(n)]


def test_hochladen(tmp_path, monkeypatch):
    monkeypatch.setattr(ftplib, "FTP_TLS", FakeFTP)
    (tmp_path / "kern").mkdir()
    (tmp_path / "index.html").write_text("a")
    (tmp_path / "kern" / "kern.min.css").write_text("css")
    FakeFTP.dateien = {"/home/web/alt-seite-9.html": b"x", "/home/web/fremd.html": b"y",
                       "/home/web/ferienjob-dateien.txt": b"index.html\nalt-seite-9.html"}
    cfg = {"host": "h", "benutzer": "u", "verzeichnis": "web"}
    meldungen = []
    hochladen.hochladen(tmp_path, cfg, "geheim", log=meldungen.append)
    assert FakeFTP.dateien["/home/web/index.html"] == b"a"
    assert FakeFTP.dateien["/home/web/kern/kern.min.css"] == b"css"
    assert "/home/web/alt-seite-9.html" not in FakeFTP.dateien      # alte Seite entfernt
    assert "/home/web/fremd.html" in FakeFTP.dateien                # fremde Dateien bleiben
    assert FakeFTP.dateien["/home/web/ferienjob-dateien.txt"] == b"index.html\nkern/kern.min.css"
    assert not any(k.endswith(".neu") for k in FakeFTP.dateien)
    hochladen.hochladen(tmp_path, cfg, "geheim", log=meldungen.append)
    assert "unverändert: 1" in meldungen[-1]                        # KERN-Datei beim zweiten Mal übersprungen


def test_hochladen_schuetzt_fremde_ordner(tmp_path, monkeypatch):
    import pytest
    monkeypatch.setattr(ftplib, "FTP_TLS", FakeFTP)
    (tmp_path / "index.html").write_text("neu")
    (tmp_path / ".ferienjob-ausgabe").write_text("x")
    # Fremder Ordner mit Inhalt, aber ohne eigene Dateiliste: nichts überschreiben
    FakeFTP.dateien = {"/home/andere-seite/index.html": b"fremd", "/home/andere-seite/.htaccess": b"fremd"}
    cfg = {"host": "h", "benutzer": "u", "verzeichnis": "andere-seite"}
    orig = FakeFTP.__init__
    def init(self, *a, **k):
        orig(self, *a, **k); self.dirs.add("/home/andere-seite")
    monkeypatch.setattr(FakeFTP, "__init__", init)
    with pytest.raises(SystemExit):
        hochladen.hochladen(tmp_path, cfg, "geheim", log=lambda m: None)
    assert FakeFTP.dateien["/home/andere-seite/index.html"] == b"fremd"
    # Leeres Zielverzeichnis in der Konfiguration ist ein Fehler
    with pytest.raises(SystemExit):
        hochladen.hochladen(tmp_path, {**cfg, "verzeichnis": ""}, "geheim", log=lambda m: None)
    # Eigene Liste mit Pfaden außerhalb des Zielordners: diese Einträge werden nie gelöscht
    FakeFTP.dateien = {"/home/web/ferienjob-dateien.txt": b"../wichtig.txt\nalt.html", "/home/web/alt.html": b"a",
                       "/home/wichtig.txt": b"w"}
    hochladen.hochladen(tmp_path, {**cfg, "verzeichnis": "web"}, "geheim", log=lambda m: None)
    assert "/home/wichtig.txt" in FakeFTP.dateien and "/home/web/alt.html" not in FakeFTP.dateien
    assert "/home/web/.ferienjob-ausgabe" not in FakeFTP.dateien      # Markierung des Baus wird nicht hochgeladen
