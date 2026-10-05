# The prompt / Der Prompt

Paste one of these into a new chat at [claude.ai](https://claude.ai), with your
five scans attached. Replace `<FONT NAME>` / `<SCHRIFTNAME>`. Nothing else is
needed — Claude fetches everything it requires from this repo.

Full instructions (print, write, scan): [README](README.md).

## English

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

## Deutsch

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
