"""Verkleinerte Fira-Sans-Dateien für die Seite (Subsetting): nur Latein mit Umlauten und Erweiterung A, Satzzeichen, €.
Quelle sind die unveränderten KERN-Schriften in static/kern/fonts/fira-sans/, Ziel static/schriften/. Die OFL erlaubt das,
Fira Sans hat keinen Reserved Font Name. Zeichen außerhalb des Bereichs zeigt der Browser in einer Systemschrift.
Aufruf (braucht fontTools mit Brotli, im System-Python vorhanden): python3 werkzeuge/schriften.py
"""
from pathlib import Path

from fontTools import subset

WURZEL = Path(__file__).resolve().parent.parent
QUELLE = WURZEL / "static/kern/fonts/fira-sans"
ZIEL = WURZEL / "static/schriften"
BEREICH = "U+0000-017F,U+0218-021B,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,U+20AC,U+2122,U+2190-2193,U+2212,U+2215,U+FEFF,U+FFFD"
SCHNITTE = [("Regular", 400, "normal"), ("Italic", 400, "italic"), ("Medium", 500, "normal"), ("SemiBold", 600, "normal"), ("Bold", 700, "normal")]

ZIEL.mkdir(exist_ok=True)
css = ["/* erzeugt mit werkzeuge/schriften.py aus KERN (Fira Sans, SIL OFL 1.1, siehe kern/fonts/LICENSE-fira-sans.txt).\n"
       "   font-display: swap: Text steht sofort in der Ersatzschrift und wechselt, sobald Fira Sans geladen ist. */\n"]
for name, gewicht, stil in SCHNITTE:
    opt = subset.Options()
    opt.flavor = "woff2"
    opt.layout_features = ["*"]
    opt.name_IDs = ["*"]
    opt.notdef_outline = True
    s = subset.Subsetter(opt)
    font = subset.load_font(str(QUELLE / f"FiraSans-{name}.woff2"), opt)
    s.populate(unicodes=subset.parse_unicodes(BEREICH))
    s.subset(font)
    subset.save_font(font, str(ZIEL / f"FiraSans-{name}.woff2"), opt)
    css.append(f"@font-face {{ font-family: 'Fira Sans'; src: url(\"FiraSans-{name}.woff2\") format('woff2'); font-weight: {gewicht}; "
               f"font-style: {stil}; font-display: swap; unicode-range: {BEREICH.replace(',', ', ')}; }}\n")
(ZIEL / "schriften.css").write_text("".join(css), "utf-8")
for f in sorted(ZIEL.glob("*.woff2")):
    print(f.name, f.stat().st_size)
