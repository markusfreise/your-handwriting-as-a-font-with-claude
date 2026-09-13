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
F = 6 * mm                      # fiducial size
OUT = "handwriting_template_cells.pdf"

# ---- glyph rows --------------------------------------------------------
UPPER = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + list("ÄÖÜÅ")
LOWER = list("abcdefghijklmnopqrstuvwxyz") + list("äöüåß")
DIGPUN1 = list("0123456789") + list(".,;:!?")
DIGPUN2 = list("-–'\"()/&@€%*+=") + ["„", "“", "‚", "‘", "«", "»"]
ROWSETS = [("upper", UPPER), ("lower", LOWER), ("digpun1", DIGPUN1), ("digpun2", DIGPUN2)]

ROW_H = 26 * mm
# guides measured from the row's baseline (mm)
DESC, XH, CAP, ASC = -6 * mm, 6.5 * mm, 9.5 * mm, 10.5 * mm
BASE_FROM_BOTTOM = 8 * mm       # baseline sits 8 mm above the row's bottom edge

c = canvas.Canvas(OUT, pagesize=(W, H))
layout = {"page_w_pt": W, "page_h_pt": H, "margin_pt": M, "fiducial_pt": F,
          "row_h_pt": ROW_H, "base_from_bottom_pt": BASE_FROM_BOTTOM,
          "guides_pt": {"descender": DESC, "xheight": XH, "capheight": CAP, "ascender": ASC},
          "cells": [], "lines": []}


def fiducial(x, y):
    c.setFillGray(0); c.rect(x, y, F, F, fill=1, stroke=0)
    c.setFillGray(1); c.rect(x + F / 3, y + F / 3, F / 3, F / 3, fill=1, stroke=0)
    c.setFillGray(0)


def page_frame(title, page, npages):
    c.setFont("DVB", 11); c.drawString(M, H - M - 3 * mm, f"Handschrift-Vorlage (Zellen)  ·  {title}  ·  Blatt {page}/{npages}")
    fiducial(M - F - 2 * mm, H - M - F); fiducial(W - M + 2 * mm, H - M - F)
    fiducial(M - F - 2 * mm, M); fiducial(W - M + 2 * mm, M)
    c.setFont("DV", 6); c.drawRightString(W - M, M - 3 * mm, f"P{page}")


def guides(x0, x1, ybase, heavy=True, asc=True):
    gl = ((DESC, 0.8, 0.3), (XH, 0.75, 0.3), (CAP, 0.75, 0.3)) + (((ASC, 0.85, 0.3),) if asc else ())
    for off, gray, lw in gl:
        c.setStrokeGray(gray); c.setLineWidth(lw); c.line(x0, ybase + off, x1, ybase + off)
    c.setStrokeGray(0.35 if heavy else 0.5); c.setLineWidth(0.9); c.line(x0, ybase, x1, ybase)


def glyph_row(y_bottom, chars, variant, kind, page):
    n = len(chars)
    cw = (W - 2 * M) / n
    ybase = y_bottom + BASE_FROM_BOTTOM
    c.setStrokeGray(0); c.setLineWidth(0.4); c.rect(M, y_bottom, W - 2 * M, ROW_H)
    guides(M + 1 * mm, W - M - 1 * mm, ybase)
    for i, ch in enumerate(chars):
        x = M + i * cw
        if i:
            c.setStrokeGray(0.55); c.setLineWidth(0.3)
            c.setDash(1, 2); c.line(x, y_bottom, x, y_bottom + ROW_H); c.setDash()
        c.setFillGray(0.86); c.setFont("DV", 14)
        c.drawCentredString(x + cw / 2, ybase + 1, ch)
        c.setFillGray(0.45); c.setFont("DV", 5)
        c.drawString(x + 0.8 * mm, y_bottom + ROW_H - 2.5 * mm, ch)
        layout["cells"].append(dict(glyph=ch, cp=ord(ch), variant=variant, kind=kind, page=page,
                                    x_pt=x, y_pt=y_bottom, w_pt=cw, h_pt=ROW_H, ybase_pt=ybase))
    c.setFillGray(0.45); c.setFont("DV", 6)
    c.drawRightString(W - M - 1 * mm, y_bottom + ROW_H - 2.5 * mm, f"v{variant}")


def text_line(y_bottom, text, tag, page, line_h=ROW_H):
    ybase = y_bottom + BASE_FROM_BOTTOM
    guides(M, W - M, ybase, heavy=False, asc=False)
    c.setFillGray(0.45); c.setFont("DV", 7)
    c.drawString(M, ybase + CAP + 0.8 * mm, text)
    layout["lines"].append(dict(text=text, tag=tag, page=page, x_pt=M, y_pt=y_bottom,
                                w_pt=W - 2 * M, h_pt=line_h, ybase_pt=ybase))


NPAGES = 4
top = H - M - 8 * mm

# --- page 1: upper + lower, 3 variants each ---
page_frame("Buchstaben", 1, NPAGES)
y = top
for v in (1, 2, 3):
    y -= ROW_H; glyph_row(y, UPPER, v, "upper", 1)
y -= 2 * mm
for v in (1, 2, 3):
    y -= ROW_H; glyph_row(y, LOWER, v, "lower", 1)
c.setFont("DV", 7); c.setFillGray(0.3)
c.drawString(M, y - 4 * mm, "Grundlinie dick · Kleinbuchstaben bis zur x-Linie · Großbuchstaben und Ziffern bis zur Versallinie darüber · "
             "Varianten bewusst leicht unterschiedlich schreiben")
c.drawString(M, y - 7.5 * mm, "Fehler: durchstreichen und die Zelle leer lassen — nicht daneben wiederholen. "
             "Sätze und Paare auf Blatt 3/4 in natürlichem Tempo, Buchstaben nicht verbinden.")
c.showPage()

# --- page 2: digits + punctuation, 3 variants ---
page_frame("Ziffern & Zeichen", 2, NPAGES)
y = top
for v in (1, 2, 3):
    y -= ROW_H; glyph_row(y, DIGPUN1, v, "digpun1", 2)
y -= 2 * mm
for v in (1, 2, 3):
    y -= ROW_H; glyph_row(y, DIGPUN2, v, "digpun2", 2)
c.showPage()

# --- page 3: sentences ---
SENTENCES = [
    "Falsches Üben von Xylophonmusik quält jeden größeren Zwerg.",
    "Victor jagt zwölf Boxkämpfer quer über den großen Sylter Deich.",
    "Flygande bäckasiner söka hwila på mjuka tuvor.",
    "Ja, ich fahre. Guten Morgen, Göteborg! Heute schon gejournaled?",
    "Träume nicht dein Leben – lebe deinen Traum.",
    "„Wirklich?“ – ‚Ja.‘ (Kein Witz.) & Punkt.",
]
page_frame("Sätze", 3, NPAGES)
y = top
for i, t in enumerate(SENTENCES):
    y -= ROW_H; text_line(y, t, f"s{i+1}", 3)
c.showPage()

# --- page 4: kerning pairs + numbers ---
PAIRS = [
    "non ono nnn ooo HOH OHO HHH OOO",
    "ob oc oe og os bo do po qo nc ne no nu cn en on",
    "AV VA AW WA AY YA AT TA LT TL LV LY KO OK XO OX",
    "Ta Te To Tu Ty Tr Ts Tä Va Ve Vo Wa We Wo Ya Ye Yo Fa Fe Fo Pa Pe La Le Lo",
    "ra re ro ru rn rt rv ry fa fe fo fu ft fl fi il li it ti lt tl ij ji ll ii",
    "a, a. o, o. r, r. y, y. f, f. T, T. V, V. a; a: a! a? o) (o „a“ ‚a‘",
    "ÄO ÖA ÜA ÅO äo öa üa åo år åt ån Åa Åo Ä. Ö, Ü!",
]
NUMBERS = [
    "0123456789 11 17 71 74 47 10 01 44 77 00 19 91",
    "19,50 € · 100 % · 2026 · 13.09.2026 · 07:45 Uhr · 1.234.567 · +49 521 000000",
]
page_frame("Paare & Zahlen", 4, NPAGES)
y = top
for i, t in enumerate(PAIRS):
    y -= 20 * mm; text_line(y, t, f"k{i+1}", 4, line_h=20 * mm)
y -= 3 * mm
for i, t in enumerate(NUMBERS):
    y -= 20 * mm; text_line(y, t, f"n{i+1}", 4, line_h=20 * mm)
c.showPage()

c.save()
json.dump(layout, open("template_cells_layout.json", "w"), ensure_ascii=False, indent=1)
print(len(layout["cells"]), "cells,", len(layout["lines"]), "lines")
