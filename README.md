# Your handwriting as a font — with Claude

**[→ Anleitung in deutscher Sprache](#deine-handschrift-als-font--mit-claude)**

Print a template. Write on it. Scan it. Give the scans and one prompt to Claude.
Get back a font of your own handwriting (TTF/OTF) with 2–3 alternates per letter,
spacing measured from the way you actually write. German, Swedish, French and
Spanish characters included.

You never touch any code. The only things you give Claude are your scans and the
prompt. Everything else happens inside Claude. (There *is* a script in this repo —
Claude fetches and runs it, so every font is built the same way. You don't need to
look at it; see *For experts* at the bottom if you want to.)

---

## 1. Print

Download [`handwriting_template_flow.pdf`](handwriting_template_flow.pdf) and print
it at **100 %** — no "fit to page", no scaling. Five pages, A4 landscape, on plain
white paper (100–120 g is nicer than standard copy paper because the pen bleeds less).

## 2. Write

Use a **black fineliner, 0.7–1.0 mm**. Each line shows in grey what to write.
Write it in one flow, the way you'd recite the alphabet — don't think about the
letters one by one, that's exactly what makes fonts look stiff.

- The thick line is the baseline. Lowercase up to the x-line, capitals and digits
  up to the top line.
- Don't connect letters.
- The alphabet lines repeat three times. Write them a little differently each time,
  naturally — those become the alternates.
- Mistakes: strike through and carry on. Don't squeeze a correction in.
- Pages 4–5 are sentences and letter pairs. Write them at your normal speed.

## 3. Scan

**300 dpi, greyscale, one file per page.** A flatbed scanner is ideal. A scanning
app such as Genius Scan or Adobe Scan works just as well — what matters is that the
result has strong contrast: black ink, white paper, no grey shadows. If in doubt,
take the phone outside to photograph; daylight is always good light. During the
day, obviously. 😉 A plain photo without a scanning app is not enough.

The **four black squares in the corners** must be in the scan — they are used to
align the page. Name the files so they sort in page order (`page-1.png` …).

## 4. Hand it to Claude

Open a new chat at [claude.ai](https://claude.ai), attach your five scans, and
paste this (also in [`PROMPT.md`](PROMPT.md), with a German version):

```
I'm turning my handwriting into a font. Attached are the 5 scans of a filled-out
template from https://github.com/markusfreise/your-handwriting-as-a-font-with-claude
(300 dpi, one image per page, in page order).

Please do this, step by step, in your code sandbox:

1. Download these two files from the repo:
   https://raw.githubusercontent.com/markusfreise/your-handwriting-as-a-font-with-claude/main/build_font.py
   https://raw.githubusercontent.com/markusfreise/your-handwriting-as-a-font-with-claude/main/template_flow_layout.json
   If you cannot fetch them, stop and tell me — I'll attach them. Don't rewrite
   the script yourself.
2. Install: numpy opencv-python-headless scipy scikit-image fonttools Pillow
3. Run:
   python3 build_font.py --scans <my scans in page order> \
       --layout template_flow_layout.json --family "<FONT NAME>" --out out/
4. Before anything else, show me out/glyphs-check.png and the specimen image
   from out/, and tell me which lines aligned fewer characters than expected.
5. If a glyph is misassigned, broken, or has a speck of dirt from the scan,
   name it and ask me whether to drop that variant, copy another variant over
   it, or have me rewrite the line — never substitute silently.
6. Then give me the TTF and OTF from out/ to download.

Rules:
- Font name: "<FONT NAME>". Number test builds ("<FONT NAME> 2", "<FONT NAME> 3");
  Adobe Express and Canva refuse a second upload with the same font name. Use
  the clean name only when I say it's final.
- Adobe Express and Canva ignore kerning tables. Spacing fixes must go into the
  sidebearings, not into kerning pairs.
- If I ask for bolder or lighter, rebuild with --weight (1.1 = 10 % bolder).
- Whenever you change a glyph, change it in BOTH the TTF and the OTF, and
  check that both have identical metrics afterwards.
```

Replace `<FONT NAME>` with what you want the font to be called. Claude shows you a
check sheet with every extracted letter and a specimen, you tell it what to fix,
and it gives you the files. Install the TTF on your computer, or upload it to
Adobe Express, Canva, CapCut and the like.

If the chat can't run code: code execution needs to be switched on in Claude's
settings (it is by default on paid plans).

## 5. If something is off

The check sheet (`glyphs-check.png`) shows every glyph with the character Claude
assigned to it. Flow writing means the script has to work out which strokes belong
to which letter — multi-stroke capitals (H, K, T, F) are the usual suspects, and
specks of dirt from the scan sometimes get glued to a letter. Tell Claude what's
wrong; typical fixes are dropping a bad variant, copying a good one over it, or
rewriting one line and re-scanning that page. If a letter refuses to come out
right, write it on [`handwriting_template_cells.pdf`](handwriting_template_cells.pdf)
(one character per cell — unambiguous, but you'll write a bit differently) and
attach that page too.

---

## For experts: run it yourself

Everything Claude does is in [`build_font.py`](build_font.py), standalone, no API
key needed.

```bash
pip install -r requirements.txt
python3 build_font.py --scans scans/*.png --layout template_flow_layout.json --family "My Hand" --out out/
```

Output: `MyHand-Regular.ttf`, `.otf`, `MyHand-Regular-specimen.png`, `glyphs-check.png`.
Options: `--style`, `--weight 1.1` (stroke multiplier), `--version`.

What the script does, in order: register each page on the corner fiducials
(perspective transform) · remove the printed guide lines by stroke thickness ·
attach dots, umlauts, accents, cedillas to their base letter · align strokes to the
expected text of each line by dynamic programming with width/height/descender
priors · normalise heights per class (x-height, ascender, capital, digit) and
equalise stroke width afterwards · trace smoothed cubic Béziers (quadratic in the
TTF) · optical sidebearings from ink profiles · class kerning from profiles,
overridden by the gaps measured in the sentence and pair lines · `calt` cycling
through the alternates · complete `name` table and `fsType 0` so uploaders accept
the file.

`make_template.py` and `make_template_cells.py` regenerate the templates.

### Lessons learned along the way

- **Resolution matters.** A phone photo at ~150 dpi gives 40-pixel letters and
  visible stair-steps. 300 dpi is the minimum.
- **Don't write letters in isolation.** Cells give clean data but people write
  differently letter by letter than in flow — and letters written too wide get
  clipped at the cell border.
- **Never let a glyph poke past its own advance width.** One −155 sidebearing on
  the `e` made everything collide.
- **Per-glyph scaling changes stroke weight.** Scale a small `a` up by 33 % and its
  stroke gets 33 % thicker. Measure stroke width on the skeleton and correct it.
- **Handwritten capitals are often barely taller than the x-height.** Lift them, or
  an `H` in running text reads as lowercase.
- **Adobe Express and Canva ignore kerning.** Everything that has to look right
  there must be right in the sidebearings. Kerning is a bonus for apps that use it.
- **Keep TTF and OTF metric-identical.** We once lost every left sidebearing in the
  TTF while the OTF was fine; the symptom was "ui too tight, ju too wide".
- **Uploaders reject fonts with an incomplete `name` table** (IDs 3, 4, 16, 17) or
  `fsType ≠ 0`, and they identify fonts by PostScript name, not file name.

Made by Markus Freise with Claude (Anthropic). MIT licence.

---
---

# Deine Handschrift als Font — mit Claude

Vorlage drucken. Beschreiben. Scannen. Scans und einen Prompt an Claude geben.
Zurück kommt eine Schrift aus deiner Handschrift (TTF/OTF) mit 2–3 Varianten pro
Buchstabe und Abständen so, wie du tatsächlich schreibst. Deutsche, schwedische,
französische und spanische Sonderzeichen sind dabei.

Du fasst keinen Code an. Du gibst Claude nur deine Scans und den Prompt, alles
andere passiert in Claude. (Es gibt ein Skript in diesem Repo — Claude holt und
startet es selbst, damit jede Schrift auf dieselbe Weise entsteht. Du musst es
nicht ansehen; wer will, findet es ganz unten unter *Für Experten*.)

## 1. Drucken

[`handwriting_template_flow.pdf`](handwriting_template_flow.pdf) herunterladen und
bei **100 %** drucken — kein „An Seite anpassen". Fünf Seiten A4 quer, weißes
Papier (100–120 g ist angenehmer als Kopierpapier, der Stift schlägt weniger durch).

## 2. Schreiben

**Schwarzer Fineliner, 0,7–1,0 mm.** Über jeder Zeile steht in Grau, was
hineingehört. In einem Zug schreiben, wie beim Alphabet aufsagen — nicht Buchstabe
für Buchstabe nachdenken, genau das macht Schriften steif.

- Die dicke Linie ist die Grundlinie. Kleinbuchstaben bis zur x-Linie, Große und
  Ziffern bis zur oberen Linie.
- Buchstaben nicht verbinden.
- Die Alphabetzeilen kommen dreimal. Jedes Mal ein bisschen anders schreiben, ganz
  natürlich — daraus werden die Varianten.
- Fehler: durchstreichen und weiter. Keine Korrektur dazwischenquetschen.
- Seiten 4–5 sind Sätze und Buchstabenpaare. In normalem Tempo schreiben.

## 3. Scannen

**300 dpi, Graustufen, eine Datei pro Seite.** Ein Flachbettscanner ist ideal.
Du kannst auch eine Scan-App wie z. B. Genius Scan nutzen. Wichtig ist, dass das
Ergebnis kontraststark ist: schwarze Tinte, weißes Papier, keine grauen Schatten.
Im Zweifel beim Fotografieren nach draußen gehen. Dann ist das Licht in jedem Fall
gut. Natürlich tagsüber. 😉 Ein einfaches Foto ohne Scan-App reicht nicht.

Die **vier schwarzen Quadrate in den Ecken** müssen mit im Bild sein, daran wird
die Seite ausgerichtet. Dateien so benennen, dass sie in Seitenreihenfolge
sortieren (`seite-1.png` …).

## 4. An Claude geben

Neuen Chat auf [claude.ai](https://claude.ai) öffnen, die fünf Scans anhängen,
das hier einfügen (steht auch in [`PROMPT.md`](PROMPT.md)):

```
Ich mache aus meiner Handschrift eine Schrift. Angehängt sind die 5 Scans der
ausgefüllten Vorlage aus https://github.com/markusfreise/your-handwriting-as-a-font-with-claude
(300 dpi, ein Bild pro Seite, in Seitenreihenfolge).

Bitte mach das Schritt für Schritt in deiner Code-Sandbox:

1. Lade diese zwei Dateien aus dem Repo:
   https://raw.githubusercontent.com/markusfreise/your-handwriting-as-a-font-with-claude/main/build_font.py
   https://raw.githubusercontent.com/markusfreise/your-handwriting-as-a-font-with-claude/main/template_flow_layout.json
   Wenn das nicht geht: Stopp, sag Bescheid, ich hänge sie an. Schreib das
   Skript nicht selbst neu.
2. Installiere: numpy opencv-python-headless scipy scikit-image fonttools Pillow
3. Führe aus:
   python3 build_font.py --scans <meine Scans in Seitenreihenfolge> \
       --layout template_flow_layout.json --family "<SCHRIFTNAME>" --out out/
4. Zeig mir zuallererst out/glyphs-check.png und das Schriftmuster aus out/
   und sag mir, bei welchen Zeilen weniger Zeichen zugeordnet wurden als
   erwartet.
5. Wenn eine Glyphe falsch zugeordnet, kaputt oder mit einem Fussel vom Scan
   verziert ist: benenne sie und frag, ob ich die Variante streichen, eine
   andere Variante drüberkopieren oder die Zeile neu schreiben will — nie
   stillschweigend ersetzen.
6. Dann gib mir TTF und OTF aus out/ zum Download.

Regeln:
- Schriftname: „<SCHRIFTNAME>". Testbuilds nummerieren („<SCHRIFTNAME> 2",
  „<SCHRIFTNAME> 3"); Adobe Express und Canva lehnen einen zweiten Upload mit
  demselben Namen ab. Den sauberen Namen erst, wenn ich sage, dass es final ist.
- Adobe Express und Canva ignorieren Kerning-Tabellen. Abstandskorrekturen
  müssen in die Vorbreiten, nicht in Kerning-Paare.
- Wenn ich fetter oder leichter will: mit --weight neu bauen (1,1 = 10 % fetter).
- Wenn du eine Glyphe änderst, ändere sie in TTF UND OTF und prüfe danach, dass
  beide identische Metriken haben.
```

`<SCHRIFTNAME>` durch den gewünschten Namen ersetzen. Claude zeigt dir ein
Kontrollblatt mit jedem ausgelesenen Buchstaben und ein Schriftmuster, du sagst,
was zu korrigieren ist, und bekommst die Dateien. TTF auf dem Rechner installieren
oder bei Adobe Express, Canva, CapCut und Co. hochladen.

Falls der Chat keinen Code ausführen kann: Die Code-Ausführung muss in Claudes
Einstellungen eingeschaltet sein (in den bezahlten Plänen ist sie das von Haus aus).

## 5. Wenn etwas nicht stimmt

Das Kontrollblatt (`glyphs-check.png`) zeigt jede Glyphe mit dem Zeichen, das
Claude ihr zugeordnet hat. Beim Fließtext muss das Skript raten, welche Striche
zu welchem Buchstaben gehören — mehrteilige Versalien (H, K, T, F) sind die
üblichen Kandidaten, und manchmal klebt ein Fussel vom Scan an einem Buchstaben.
Sag Claude, was falsch ist; meist reicht es, eine Variante zu streichen, eine gute
drüberzukopieren oder eine Zeile neu zu schreiben und die Seite neu zu scannen.
Wenn ein Buchstabe partout nicht will, schreib ihn auf
[`handwriting_template_cells.pdf`](handwriting_template_cells.pdf) (ein Zeichen pro
Zelle — eindeutig, aber man schreibt etwas anders) und häng die Seite mit an.

---

## Für Experten: selbst ausführen

Alles, was Claude macht, steckt in [`build_font.py`](build_font.py), eigenständig,
ohne API-Key.

```bash
pip install -r requirements.txt
python3 build_font.py --scans scans/*.png --layout template_flow_layout.json --family "Meine Hand" --out out/
```

Optionen: `--style`, `--weight 1.1` (Strichfaktor), `--version`.

Ablauf: Seiten an den Passmarken entzerren · gedruckte Hilfslinien über die
Strichstärke entfernen · Punkte, Umlaute, Akzente, Cedillen an ihre Grundbuchstaben
hängen · Striche per dynamischer Programmierung dem Solltext der Zeile zuordnen ·
Höhen je Klasse normieren und danach die Strichstärke angleichen · geglättete
kubische Béziers · optische Vorbreiten aus Tintenprofilen · Klassen-Kerning,
überschrieben durch die in Satz- und Paarzeilen gemessenen Abstände ·
`calt`-Wechsel der Varianten · vollständige `name`-Tabelle und `fsType 0`.

`make_template.py` und `make_template_cells.py` erzeugen die Vorlagen neu.
Die Lektionen aus der Entwicklung stehen oben im englischen Teil.

Von Markus Freise mit Claude (Anthropic). MIT-Lizenz.
