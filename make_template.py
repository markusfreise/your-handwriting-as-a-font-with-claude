"""Flow-based handwriting template.

Each line shows the sequence to write in grey above a ruled line. You write it
in one flow, like writing down the alphabet — no cells. The layout JSON records
every line's expected text and baseline so the build script can match your
strokes to characters afterwards.
"""
import json
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pdfmetrics.registerFont(TTFont("DV", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DVB", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))

W, H = landscape(A4)
M = 12 * mm
F = 6 * mm
OUT = "handwriting_template_flow.pdf"
LAYOUT = "template_flow_layout.json"

LINE_H = 24 * mm
BASE = 8 * mm                          # baseline above the line's bottom edge
DESC, XH, CAP = -6 * mm, 6.5 * mm, 9.5 * mm

# ---- what to write ----------------------------------------------------
UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
LOWER = "abcdefghijklmnopqrstuvwxyz"
DIGITS = "0123456789"
PUNCT1 = ". , ; : ! ? - – ' \" ( ) / & @"
PUNCT2 = "€ $ £ % * + = # „ “ ‚ ‘ « » ¿ ¡"
# German + Swedish + French + Spanish
SPECIAL_UP = "Ä Ö Ü Å Æ Ø  À Â Ç É È Ê Ë Î Ï Ô Œ Ù Û Ÿ  Á Í Ó Ú Ñ"
SPECIAL_LO = "ä ö ü ß å æ ø  à â ç é è ê ë î ï ô œ ù û ÿ  á í ó ú ñ"

# glyph lines: (tag, text, repeat)
GLYPH_LINES = [
    ("upper", UPPER, 3),
    ("lower", LOWER, 3),
    ("digits", DIGITS, 3),
    ("punct1", PUNCT1, 2),
    ("punct2", PUNCT2, 2),
    ("special_up", SPECIAL_UP, 2),
    ("special_lo", SPECIAL_LO, 2),
]

SENTENCES = [
    ("en", "The quick brown fox jumps over the lazy dog. Sphinx of black quartz, judge my vow!"),
    ("en", "When the noise fades, you will hear your soul's real longings."),
    ("de", "Falsches Üben von Xylophonmusik quält jeden größeren Zwerg."),
    ("de", "Victor jagt zwölf Boxkämpfer quer über den großen Sylter Deich."),
    ("de", "Ja, ich fahre. Guten Morgen, Göteborg! Heute schon gejournaled?"),
    ("sv", "Flygande bäckasiner söka hwila på mjuka tuvor. Så är det bara."),
    ("fr", "Voix ambiguë d'un cœur qui, au zéphyr, préfère les jattes de kiwis."),
    ("es", "El veloz murciélago hindú comía feliz cardillo y kiwi. ¿Qué? ¡Sí!"),
    ("mix", "„Wirklich?“ – ‚Ja.‘ (Kein Witz.) & 19,50 € · 100 % · 13.09.2026 · 07:45 Uhr · +49 521 000000"),
]

KERNING = [
    "non ono nnn ooo HOH OHO HHH OOO",
    "ob oc oe og os bo do po qo nc ne no nu cn en on",
    "AV VA AW WA AY YA AT TA LT TL LV LY KO OK XO OX",
    "Ta Te To Tu Ty Tr Ts Va Ve Vo Wa We Wo Ya Ye Yo Fa Fe Fo Pa Pe La Le Lo",
    "ra re ro ru rn rt rv ry fa fe fo fu ft fl fi il li it ti lt tl ij ji ll ii",
    "a, a. o, o. r, r. y, y. f, f. T, T. V, V. a; a: a! a? o) (o „a“ ‚a‘",
    "ÄO ÖA ÜA ÅO äo öa üa åo år åt ån Åa Åo Ä. Ö, Ü!",
    "0123456789 11 17 71 74 47 10 01 44 77 00 19 91 1.234.567",
]

c = canvas.Canvas(OUT, pagesize=(W, H))
layout = {"page_w_pt": W, "page_h_pt": H, "margin_pt": M, "fiducial_pt": F,
          "line_h_pt": LINE_H, "base_pt": BASE,
          "guides_pt": {"descender": DESC, "xheight": XH, "capheight": CAP},
          "lines": []}


def fiducial(x, y):
    c.setFillGray(0); c.rect(x, y, F, F, fill=1, stroke=0)
    c.setFillGray(1); c.rect(x + F / 3, y + F / 3, F / 3, F / 3, fill=1, stroke=0)
    c.setFillGray(0)


def page_frame(title, page, npages):
    c.setFont("DVB", 11)
    c.drawString(M, H - M - 3 * mm, f"Handschrift-Vorlage (Fluss)  ·  {title}  ·  Blatt {page}/{npages}")
    fiducial(M - F - 2 * mm, H - M - F); fiducial(W - M + 2 * mm, H - M - F)
    fiducial(M - F - 2 * mm, M); fiducial(W - M + 2 * mm, M)
    c.setFont("DV", 6); c.drawRightString(W - M, M - 3 * mm, f"P{page}")


def line(y_bottom, text, tag, page, kind):
    ybase = y_bottom + BASE
    for off, gray in ((DESC, 0.8), (XH, 0.72), (CAP, 0.72)):
        c.setStrokeGray(gray); c.setLineWidth(0.3); c.line(M, ybase + off, W - M, ybase + off)
    c.setStrokeGray(0.4); c.setLineWidth(0.9); c.line(M, ybase, W - M, ybase)
    c.setFillGray(0.45); c.setFont("DV", 7.5)
    c.drawString(M, ybase + CAP + 1 * mm, text)
    layout["lines"].append(dict(text=text, tag=tag, kind=kind, page=page, x_pt=M,
                                y_pt=y_bottom, w_pt=W - 2 * M, h_pt=LINE_H, ybase_pt=ybase))


per_page = int((H - 2 * M - 10 * mm) // LINE_H)      # 7 lines
items = []
for tag, text, rep in GLYPH_LINES:
    for v in range(1, rep + 1):
        items.append((f"{tag}_v{v}", text, "glyphs"))
for lang, text in SENTENCES:
    items.append((f"sentence_{lang}", text, "sentence"))
for i, text in enumerate(KERNING):
    items.append((f"kerning_{i+1}", text, "kerning"))

npages = -(-len(items) // per_page)
for p in range(npages):
    chunk = items[p * per_page:(p + 1) * per_page]
    title = {"glyphs": "Zeichen", "sentence": "Sätze", "kerning": "Paare"}[chunk[0][2]]
    page_frame(title, p + 1, npages)
    y = H - M - 8 * mm
    for tag, text, kind in chunk:
        y -= LINE_H
        line(y, text, tag, p + 1, kind)
    if p == 0:
        c.setFillGray(0.3); c.setFont("DV", 7)
        c.drawString(M, M + 1 * mm,
                     "In einem Zug schreiben wie beim Alphabet aufsagen · Buchstaben nicht verbinden · Grundlinie dick, "
                     "Kleinbuchstaben bis zur x-Linie, Große und Ziffern bis zur oberen Linie · Fehler durchstreichen und "
                     "einfach weiterschreiben")
    c.showPage()

c.save()
json.dump(layout, open(LAYOUT, "w"), ensure_ascii=False, indent=1)
print(f"{len(items)} lines on {npages} pages -> {OUT}, {LAYOUT}")
