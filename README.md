# Your handwriting as a font — with Claude

Turn a few sheets of your own handwriting into an installable font (TTF/OTF) with
2–3 alternates per letter, automatic spacing and kerning measured from your own
writing. German, Swedish, French and Spanish characters included.

Everything here was built in a conversation with Claude. You can either run the
scripts yourself or hand the whole folder to Claude and use the prompt in
[`PROMPT.md`](PROMPT.md).

*Deutsche Fassung weiter unten.*

---

## How it works

1. **Print** `handwriting_template_flow.pdf` at 100 % (no "fit to page"). Five
   landscape A4 pages: alphabet lines (3× upper, 3× lower, 3× digits, 2× punctuation,
   2× accented characters), nine sample sentences (EN/DE/SV/FR/ES), eight lines of
   kerning pairs.
2. **Write** each line in one flow, the way you'd write the alphabet from memory.
   Black fineliner, 0.7–1.0 mm. Baseline is the thick line; lowercase up to the
   x-line, capitals and digits up to the upper line. Don't connect letters. If you
   make a mistake, strike it through and carry on.
3. **Scan** at 300 dpi, greyscale, one image per page. The four black squares in the
   corners must be in the scan — they are used to register the page.
4. **Build:**

   ```bash
   pip install -r requirements.txt
   python3 build_font.py --scans scans/*.png --family "My Hand" --out out/
   ```

   You get `out/MyHand-Regular.ttf`, `.otf`, a specimen image and
   `glyphs-check.png` showing every extracted glyph with its assigned character.
   **Look at that sheet.** Flow writing means the script has to work out which
   strokes belong to which letter; it prints how many characters it aligned per
   line, and the check sheet shows where it guessed wrong.

5. **Fix** misassigned letters by writing them again on `handwriting_template_cells.pdf`
   (one character per cell — unambiguous, but you will write slightly differently)
   or simply by rewriting that line of the flow template.

### What the script does

- registers each page with the corner fiducials (perspective transform)
- removes the printed guide lines by stroke thickness (the pen is ~2× thicker than the lines)
- attaches dots, umlauts, accents and cedillas to their base letter
- aligns strokes to the expected text per line with dynamic programming using
  width, height and descender priors — multi-stroke letters (H, K, T, F …) are reassembled
- normalises heights per class (x-height, ascender, capital, digit) and equalises
  stroke width afterwards, so letters written slightly larger don't come out thinner
- traces outlines as smoothed cubic Béziers (quadratic in the TTF)
- optical sidebearings from ink profiles, class kerning computed from profiles and
  **overridden by the gaps you actually left** in the sentence and kerning lines
- alternates cycle automatically (`calt`, 1→2→3)

### Options

```
--family "Name"      font family name (PostScript name is derived from it)
--style Regular      style name
--weight 1.1         stroke multiplier: 1.1 = 10 % bolder, 0.9 = lighter
--version 1.0
```

Adobe Express, Canva etc. identify fonts by PostScript name. If you upload a second
build, change `--family` (e.g. "My Hand 2") or delete the first one there.

### Files

| file | what |
|---|---|
| `handwriting_template_flow.pdf` + `template_flow_layout.json` | the template to print, and its machine-readable layout |
| `handwriting_template_cells.pdf` + `template_cells_layout.json` | fallback: one character per cell |
| `make_template.py`, `make_template_cells.py` | regenerate the templates (edit the character sets or sentences there) |
| `build_font.py` | the whole pipeline, standalone |
| `PROMPT.md` | prompts (EN/DE) to hand the job to Claude instead of running the script |

### Lessons learned along the way

- **Resolution matters.** A phone photo of a page at ~150 dpi gives 40-pixel letters
  and visible stair-steps in the outlines. 300 dpi scans of properly sized writing are
  the minimum.
- **Don't write letters in isolation** if you can avoid it. Cells give clean data
  but people write differently letter by letter than in flow — sizes drift,
  baselines float, the result looks stiff.
- **Never let a glyph poke past its own advance width.** A sidebearing of −155 units
  on the `e` made everything collide; the minimum is now clamped at 30.
- **Per-glyph scaling changes stroke weight.** Scaling a small `a` up by 33 % also
  makes its stroke 33 % thicker. Measure stroke width on the skeleton and correct it.
- **Handwritten capitals are often barely taller than the x-height.** Lift them
  (default 1.45× x-height) or a `H` in running text reads as lowercase.
- Font uploaders reject files with an incomplete `name` table (IDs 3, 4, 16, 17)
  or `fsType ≠ 0`. Both are set here.

Made by Markus Freise with Claude (Anthropic). MIT licence.

---

# Deine Handschrift als Font — mit Claude

Ein paar Blätter eigene Handschrift werden zu einer installierbaren Schrift
(TTF/OTF) mit 2–3 Varianten pro Buchstabe, automatischem Spacing und Kerning, das
aus deinem eigenen Schreibfluss gemessen wird. Deutsche, schwedische, französische
und spanische Sonderzeichen sind dabei.

## So geht's

1. **Drucken:** `handwriting_template_flow.pdf` bei 100 % (kein „An Seite anpassen").
   Fünf Seiten A4 quer: Alphabetzeilen (3× groß, 3× klein, 3× Ziffern, 2× Satzzeichen,
   2× Sonderzeichen), neun Beispielsätze (EN/DE/SV/FR/ES), acht Zeilen Kerning-Paare.
2. **Schreiben:** jede Zeile in einem Zug, wie beim Alphabet aufsagen. Schwarzer
   Fineliner 0,7–1,0 mm. Grundlinie ist die dicke Linie, Kleinbuchstaben bis zur
   x-Linie, Große und Ziffern bis zur oberen Linie. Buchstaben nicht verbinden. Fehler
   durchstreichen und weiterschreiben.
3. **Scannen:** 300 dpi, Graustufen, ein Bild pro Seite. Die vier schwarzen Quadrate
   in den Ecken müssen mit drauf sein — daran wird die Seite ausgerichtet.
4. **Bauen:**

   ```bash
   pip install -r requirements.txt
   python3 build_font.py --scans scans/*.png --family "Meine Hand" --out out/
   ```

   Ergebnis: `out/MeineHand-Regular.ttf`, `.otf`, ein Schriftmuster und
   `glyphs-check.png` mit jeder ausgelesenen Glyphe und dem zugeordneten Zeichen.
   **Dieses Blatt anschauen.** Beim Fließtext muss das Skript raten, welche Striche
   zu welchem Buchstaben gehören; es meldet pro Zeile, wie viele Zeichen es
   zuordnen konnte, und das Kontrollblatt zeigt, wo es daneben lag.

5. **Nachbessern:** falsch zugeordnete Buchstaben auf `handwriting_template_cells.pdf`
   nachschreiben (ein Zeichen pro Zelle — eindeutig, aber man schreibt etwas anders)
   oder einfach die betroffene Zeile der Fluss-Vorlage neu schreiben.

### Was das Skript macht

- richtet jede Seite an den Passmarken aus (perspektivische Entzerrung)
- entfernt die gedruckten Hilfslinien über die Strichstärke (Stift ≈ doppelt so dick)
- hängt Punkte, Umlaute, Akzente und Cedillen an ihren Grundbuchstaben
- ordnet Striche per dynamischer Programmierung dem Solltext der Zeile zu, mit
  Breiten-, Höhen- und Unterlängen-Erwartung — mehrteilige Buchstaben (H, K, T, F …)
  werden wieder zusammengesetzt
- normiert Höhen je Klasse (x-Höhe, Oberlänge, Versal, Ziffer) und gleicht danach
  die Strichstärke an, damit größer geschriebene Buchstaben nicht dünner werden
- vektorisiert als geglättete kubische Béziers (quadratisch in der TTF)
- optische Vorbreiten aus Tintenprofilen, Klassen-Kerning berechnet und **durch die
  Abstände überschrieben, die du in den Satz- und Paarzeilen tatsächlich gelassen hast**
- Varianten wechseln automatisch (`calt`, 1→2→3)

### Optionen

```
--family "Name"      Schriftfamilie (der PostScript-Name wird daraus abgeleitet)
--style Regular      Schnittname
--weight 1.1         Strichfaktor: 1,1 = 10 % fetter, 0,9 = leichter
--version 1.0
```

Adobe Express, Canva usw. erkennen Schriften am PostScript-Namen. Für einen zweiten
Upload `--family` ändern (z. B. „Meine Hand 2") oder die erste dort löschen.

### Was unterwegs gelernt wurde

- **Auflösung entscheidet.** Ein Handyfoto mit ~150 dpi liefert 40-Pixel-Buchstaben
  und sichtbare Treppen. 300-dpi-Scans sind das Minimum.
- **Buchstaben nicht einzeln schreiben,** wenn es sich vermeiden lässt. Zellen liefern
  saubere Daten, aber man schreibt einzeln anders als im Fluss — Größen driften,
  Grundlinien schweben, das Ergebnis wirkt steif.
- **Kein Zeichen darf über seine Laufweite ragen.** Eine Vorbreite von −155 beim `e`
  ließ alles zusammenstoßen; das Minimum ist jetzt auf 30 begrenzt.
- **Skalierung pro Glyphe verändert die Strichstärke.** Ein kleines `a` um 33 %
  vergrößern macht seinen Strich 33 % dicker. Strichstärke am Skelett messen und
  korrigieren.
- **Handgeschriebene Versalien sind oft kaum höher als die x-Höhe.** Anheben (Standard
  1,45× x-Höhe), sonst liest sich ein `H` im Fließtext wie ein Kleinbuchstabe.
- Font-Uploader lehnen Dateien mit unvollständiger `name`-Tabelle (IDs 3, 4, 16, 17)
  oder `fsType ≠ 0` ab. Beides ist hier gesetzt.

Von Markus Freise mit Claude (Anthropic). MIT-Lizenz.
