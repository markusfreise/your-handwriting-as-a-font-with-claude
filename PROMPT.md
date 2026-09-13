# Prompt for Claude

Use this if you'd rather have Claude run the pipeline than run it yourself.
Start a fresh chat (claude.ai with code execution enabled), attach:

- your page scans (300 dpi, greyscale, one file per page)
- `template_flow_layout.json`
- `build_font.py`

Then paste one of the prompts below. Claude will run the script in its sandbox,
show you the specimen and the check sheet, and give you the TTF/OTF to download.

---

## English

```
I'm turning my handwriting into a font. Attached are scans of a filled-out
template (300 dpi, one image per page, in page order), the template's layout
file template_flow_layout.json, and the build script build_font.py from the
repo "Your handwriting as a font with Claude".

Please:
1. Save the scans and run
   python3 build_font.py --scans <scans> --layout template_flow_layout.json
       --family "<NAME>" --out out/
   (install numpy, opencv-python-headless, scipy, scikit-image, fonttools,
   Pillow if missing). Note: potracer does not work for this — the script
   uses OpenCV contours on purpose.
2. Show me out/<NAME>-Regular-specimen.png and out/glyphs-check.png before
   anything else. Tell me which lines aligned fewer characters than expected.
3. If a glyph is misassigned or broken, say which one and ask me whether to
   drop that variant, take it from another line, or have me rewrite it —
   don't silently substitute.
4. Then give me the TTF and OTF from out/ to download.

Family name: "<NAME>". If I ask for a bolder or lighter cut, rebuild with
--weight (1.1 = 10 % bolder). If I upload a later build to Adobe Express or
Canva, it will refuse a font with the same PostScript name as an earlier one,
so number test builds ("<NAME> 2", "<NAME> 3") and use the clean name only
for the final version.
```

## Deutsch

```
Ich mache aus meiner Handschrift eine Schrift. Angehängt sind Scans der
ausgefüllten Vorlage (300 dpi, ein Bild pro Seite, in Seitenreihenfolge), die
Layoutdatei template_flow_layout.json und das Build-Skript build_font.py aus
dem Repo „Your handwriting as a font with Claude".

Bitte:
1. Scans speichern und ausführen:
   python3 build_font.py --scans <scans> --layout template_flow_layout.json
       --family "<NAME>" --out out/
   (numpy, opencv-python-headless, scipy, scikit-image, fonttools, Pillow
   installieren, falls sie fehlen). Hinweis: potracer funktioniert dafür
   nicht — das Skript nutzt absichtlich OpenCV-Konturen.
2. Zeig mir zuerst out/<NAME>-Regular-specimen.png und out/glyphs-check.png.
   Sag mir, bei welchen Zeilen weniger Zeichen zugeordnet wurden als erwartet.
3. Wenn eine Glyphe falsch zugeordnet oder kaputt ist, benenne sie und frag,
   ob ich die Variante streichen, aus einer anderen Zeile nehmen oder neu
   schreiben will — nicht stillschweigend ersetzen.
4. Dann gib mir TTF und OTF aus out/ zum Download.

Familienname: „<NAME>". Wenn ich einen fetteren oder leichteren Schnitt will,
mit --weight neu bauen (1,1 = 10 % fetter). Adobe Express oder Canva lehnen
einen späteren Build mit demselben PostScript-Namen ab — Testbuilds also
durchnummerieren („<NAME> 2", „<NAME> 3") und den sauberen Namen erst für die
finale Version verwenden.
```

---

## If you don't want to use the template at all

You can also just hand Claude a scan of freely written lines (alphabet, digits,
a few sentences) and say what each line contains. That's how this project
started. It works, but expect to iterate: without the fiducials and the layout
file, Claude has to find the rows and baselines itself, and the result depends
much more on scan resolution. The template exists because of what went wrong
on that path — see the "Lessons learned" section in the README.
