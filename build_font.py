#!/usr/bin/env python3
"""Build a font from filled-out flow-template scans.

Usage:
    python3 build_font.py --scans scans/*.png --layout template_v3_layout.json \
        --family "My Hand" --out out/

Scans: one image per page, in page order (or named so they sort in page order).
Requires: numpy, opencv-python, scipy, scikit-image, fonttools, Pillow.
"""
import argparse, glob, json, os, sys
import numpy as np, cv2
from scipy import ndimage
from PIL import Image
from skimage.morphology import skeletonize
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString

# ============================================================ config
SCALE = 4.0            # registered px per PDF point (~288 dpi)
THR = 100              # ink threshold on the registered greyscale
UPM, CAP_UNITS = 1000, 700
SB0 = 40
UP, SMOOTH, RESAMPLE, CORNER = 4, 9, 7.0, 78
TARGET_SB, MIN_SB, TARGET_GAP = 95, 30, 105
MAX_KERN, MIN_KERN, DEPTH = -165, 40, 150
CAP_RATIO, DIG_RATIO = 1.45, 1.38          # vs x-height
NORM_CLIP = (0.7, 1.4)

DESCENDERS = set('gjpqyß,;()[]{}/\\@$§„‚çµ')
NOSNAP = set('"\'“‘·-–=+*°^~¿¡')
XSET = set('aceimnorsuvwxzæøœ')
ASET = set('bdfhkltß')
DSET = set('gjpqy')
ACC_LOW = set('äöüåàâéèêëîïôùûÿáíóúñç')
CAPS = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
ACC_UP = set('ÄÖÜÅÆØÀÂÇÉÈÊËÎÏÔŒÙÛŸÁÍÓÚÑ')
DIGITS = set('0123456789')
MULTI = set('«»"„“=:;!?%&@…*#¿¡')

NAMES = {'.': 'period', ',': 'comma', ';': 'semicolon', ':': 'colon', '!': 'exclam',
         '?': 'question', '-': 'hyphen', '–': 'endash', "'": 'quotesingle',
         '"': 'quotedbl', '(': 'parenleft', ')': 'parenright', '/': 'slash',
         '&': 'ampersand', '@': 'at', '€': 'Euro', '$': 'dollar', '£': 'sterling',
         '%': 'percent', '*': 'asterisk', '+': 'plus', '=': 'equal', '#': 'numbersign',
         '„': 'quotedblbase', '“': 'quotedblleft', '‚': 'quotesinglbase', '‘': 'quoteleft',
         '«': 'guillemotleft', '»': 'guillemotright', '·': 'periodcentered',
         '¿': 'questiondown', '¡': 'exclamdown',
         'Ä': 'Adieresis', 'Ö': 'Odieresis', 'Ü': 'Udieresis', 'Å': 'Aring', 'Æ': 'AE', 'Ø': 'Oslash',
         'À': 'Agrave', 'Â': 'Acircumflex', 'Ç': 'Ccedilla', 'É': 'Eacute', 'È': 'Egrave',
         'Ê': 'Ecircumflex', 'Ë': 'Edieresis', 'Î': 'Icircumflex', 'Ï': 'Idieresis',
         'Ô': 'Ocircumflex', 'Œ': 'OE', 'Ù': 'Ugrave', 'Û': 'Ucircumflex', 'Ÿ': 'Ydieresis',
         'Á': 'Aacute', 'Í': 'Iacute', 'Ó': 'Oacute', 'Ú': 'Uacute', 'Ñ': 'Ntilde',
         'ä': 'adieresis', 'ö': 'odieresis', 'ü': 'udieresis', 'å': 'aring', 'ß': 'germandbls',
         'æ': 'ae', 'ø': 'oslash', 'à': 'agrave', 'â': 'acircumflex', 'ç': 'ccedilla',
         'é': 'eacute', 'è': 'egrave', 'ê': 'ecircumflex', 'ë': 'edieresis', 'î': 'icircumflex',
         'ï': 'idieresis', 'ô': 'ocircumflex', 'œ': 'oe', 'ù': 'ugrave', 'û': 'ucircumflex',
         'ÿ': 'ydieresis', 'á': 'aacute', 'í': 'iacute', 'ó': 'oacute', 'ú': 'uacute', 'ñ': 'ntilde'}
DIG = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']


def gname(ch):
    if ch in NAMES: return NAMES[ch]
    if ch.isdigit(): return DIG[int(ch)]
    if ch.isascii() and ch.isalpha(): return ch
    return f'uni{ord(ch):04X}'


# ============================================================ registration
def register(path, L):
    W, H, M, F = L['page_w_pt'], L['page_h_pt'], L['margin_pt'], L['fiducial_pt']
    MMpt = 72 / 25.4
    FID = {'tl': (M - F - 2 * MMpt + F / 2, M + F / 2), 'tr': (W - M + 2 * MMpt + F / 2, M + F / 2),
           'bl': (M - F - 2 * MMpt + F / 2, H - M - F / 2), 'br': (W - M + 2 * MMpt + F / 2, H - M - F / 2)}
    img = np.array(Image.open(path).convert('L'))
    if img.shape[0] > img.shape[1] and W > H:        # portrait scan of a landscape sheet
        img = np.rot90(img, -1)
    h, w = img.shape
    side = F / 72 * (w / (W / 72))
    _, b = cv2.threshold(img, 110, 255, cv2.THRESH_BINARY_INV)
    cnts, hier = cv2.findContours(b, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    cands = []
    for i, cnt in enumerate(cnts):
        if hier[0][i][3] != -1 or hier[0][i][2] == -1: continue
        x, y, cw, ch = cv2.boundingRect(cnt)
        if not (0.6 * side < cw < 1.5 * side and 0.6 * side < ch < 1.5 * side): continue
        if abs(cw - ch) > 0.3 * side or cv2.contourArea(cnt) / (cw * ch) < 0.7: continue
        cands.append((x + cw / 2, y + ch / 2))
    src, dst = [], []
    for k, (fx, fy) in FID.items():
        ex, ey = fx / W * w, fy / H * h
        best = min(cands, key=lambda p: (p[0] - ex) ** 2 + (p[1] - ey) ** 2, default=None)
        if best is None or abs(best[0] - ex) > 0.08 * w or abs(best[1] - ey) > 0.08 * h:
            raise RuntimeError(f'{path}: fiducial {k} not found — is the whole sheet in the scan?')
        src.append(best); dst.append((fx * SCALE, fy * SCALE))
    Hm = cv2.getPerspectiveTransform(np.float32(src), np.float32(dst))
    return cv2.warpPerspective(img, Hm, (int(W * SCALE), int(H * SCALE)), flags=cv2.INTER_CUBIC, borderValue=255)


# ============================================================ line segmentation
def strip(page_img, ln, L):
    H = L['page_h_pt']
    x0, x1 = int(ln['x_pt'] * SCALE), int((ln['x_pt'] + ln['w_pt']) * SCALE)
    yt = int((H - ln['y_pt'] - ln['h_pt']) * SCALE) + int(3.5 * SCALE)   # skip the grey caption row? no: caption sits above cap line, handled by threshold
    yb = int((H - ln['y_pt']) * SCALE)
    sub = page_img[yt:yb, x0:x1]
    ybase = (H - ln['ybase_pt']) * SCALE - yt
    guides = [ybase - g * SCALE for g in L['guides_pt'].values()] + [ybase]
    return sub, ybase, guides


def ink_mask(sub, guides):
    b = sub < THR
    linemask = np.zeros_like(b)
    for y in guides:
        y = int(round(y))
        if not (10 < y < b.shape[0] - 10): continue
        band = slice(max(0, y - 11), y + 12)
        seg = b[band, :].astype(np.uint8)
        thick = cv2.morphologyEx(seg, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 12)))
        thin = seg & ~thick
        line = cv2.morphologyEx(thin, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (15, 1)))
        line = cv2.dilate(line, np.ones((3, 3), np.uint8)) & ~thick
        linemask[band, :] |= line.astype(bool)
    b &= ~linemask
    m = cv2.morphologyEx(b.astype(np.uint8), cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 15)))
    return (m & (sub < THR)).astype(bool)


def components(mask, minarea=40):
    lab, n = ndimage.label(mask, structure=np.ones((3, 3)))
    out = []
    for i, sl in enumerate(ndimage.find_objects(lab)):
        m = lab[sl] == i + 1; a = int(m.sum())
        if a < minarea: continue
        ys, xs = sl
        out.append(dict(idx=i + 1, x0=xs.start, x1=xs.stop, y0=ys.start, y1=ys.stop, area=a,
                        w=xs.stop - xs.start, h=ys.stop - ys.start))
    return lab, out


def is_scribble(k, lab):
    if k['area'] < 2500: return False
    sl = (slice(k['y0'], k['y1']), slice(k['x0'], k['x1']))
    m = np.pad((lab[sl] == k['idx']).astype(np.uint8), 20)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    return int(cv2.erode(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (23, 23))).sum()) > 150


def group_marks(comps, xh_px):
    """attach dots, accents, cedillas to the base letter they sit over/under"""
    comps = sorted(comps, key=lambda k: -k['area'])
    bases, marks = [], []
    for k in comps:
        (marks if (k['area'] < 0.5 * xh_px * xh_px * 0.35 and k['h'] < 0.6 * xh_px) else bases).append(k)
    groups = [dict(parts=[b], x0=b['x0'], x1=b['x1'], y0=b['y0'], y1=b['y1']) for b in bases]
    for m in marks:
        cx = (m['x0'] + m['x1']) / 2
        cand = [g for g in groups if g['x0'] - 8 <= cx <= g['x1'] + 8]
        if not cand:
            groups.append(dict(parts=[m], x0=m['x0'], x1=m['x1'], y0=m['y0'], y1=m['y1'])); continue
        g = min(cand, key=lambda g: min(abs(m['y1'] - g['y0']), abs(m['y0'] - g['y1'])))
        g['parts'].append(m)
        g['x0'] = min(g['x0'], m['x0']); g['x1'] = max(g['x1'], m['x1'])
        g['y0'] = min(g['y0'], m['y0']); g['y1'] = max(g['y1'], m['y1'])
    groups.sort(key=lambda g: g['x0'])
    return groups


def split_group(g, lab, mask, n):
    """split one merged group into n pieces at the shallowest column-profile valleys"""
    x0, x1 = g['x0'], g['x1']
    prof = mask[g['y0']:g['y1'], x0:x1].sum(0).astype(float)
    if n <= 1 or x1 - x0 < 8 * n: return [g]
    # candidate cuts: local minima of a smoothed profile, away from the edges
    sm = np.convolve(prof, np.ones(5) / 5, 'same')
    cand = [i for i in range(4, len(sm) - 4) if sm[i] <= sm[i - 1] and sm[i] <= sm[i + 1]]
    if len(cand) < n - 1: return [g]
    # choose n-1 cuts closest to equal spacing, preferring low profile values
    want = [(x1 - x0) * (i + 1) / n for i in range(n - 1)]
    cuts = []
    for wpos in want:
        best = min(cand, key=lambda i: abs(i - wpos) * 0.6 + sm[i] * 2)
        cuts.append(best); cand = [c for c in cand if abs(c - best) > 6]
    cuts = sorted(cuts)
    edges = [0] + cuts + [x1 - x0]
    out = []
    for a, b in zip(edges[:-1], edges[1:]):
        sub = mask[g['y0']:g['y1'], x0 + a:x0 + b]
        ys = np.where(sub.any(1))[0]
        if len(ys) == 0: continue
        out.append(dict(parts=None, x0=x0 + a, x1=x0 + b, y0=g['y0'] + ys.min(), y1=g['y0'] + ys.max() + 1,
                        cut=True))
    return out or [g]


EXP_W = {}
for c in "iljI1!.,;:'|‚‘¡": EXP_W[c] = 0.45
for c in "ftrsJ()[]{}/\\": EXP_W[c] = 0.75
for c in "mwMWÆŒ%@„“«»&": EXP_W[c] = 1.45
for c in "ABCDEFGHKLNOPQRSTUVXYZÄÖÜÅØÀÂÇÉÈÊËÎÏÔÙÛŸÁÍÓÚÑ": EXP_W[c] = 1.15


def align_runs(cl, word, xh_px, ybase=None):
    """assign consecutive stroke groups to the characters of `word` by dynamic
    programming, so multi-stroke letters (H, K, T, F ...) are reassembled"""
    n, m = len(cl), len(word)
    exp = np.array([EXP_W.get(ch, 1.0) for ch in word])
    total = cl[-1]['x1'] - cl[0]['x0']
    unit = max(total / exp.sum(), 1.0)
    INF = 1e18
    CAPH = xh_px * 9.5 / 6.5
    def exp_top(ch):
        if ch in ASET or ch in 'ij!?': return CAPH
        if ch in CAPS or ch in ACC_UP or ch in DIGITS: return CAPH
        if ch in XSET or ch in DSET or ch in ACC_LOW or ch in 'ß': return xh_px
        return None
    def exp_desc(ch):
        return 0.6 * xh_px if ch in DSET or ch in ',;()[]{}/„‚' else 0.0
    dp = np.full((n + 1, m + 1), INF); back = np.zeros((n + 1, m + 1), int)
    dp[0][0] = 0
    for j in range(1, m + 1):
        e = exp[j - 1] * unit
        for i in range(j, n + 1):
            best, bk = INF, 0
            for k in range(j - 1, i):            # comps k..i-1 form char j-1
                if dp[k][j - 1] >= INF: continue
                run = cl[k:i]
                w = run[-1]['x1'] - run[0]['x0']
                gaps = [run[t + 1]['x0'] - run[t]['x1'] for t in range(len(run) - 1)]
                cost = abs(w - e) / e + ((max(gaps) / (0.5 * xh_px)) ** 2 if gaps else 0.0)
                if ybase is not None:
                    ch = word[j - 1]
                    top = ybase - min(r['y0'] for r in run); desc = max(r['y1'] for r in run) - ybase
                    et, ed = exp_top(ch), exp_desc(ch)
                    if et is not None: cost += 1.5 * abs(top - et) / xh_px
                    cost += 1.5 * abs(max(desc, 0) - ed) / xh_px
                if dp[k][j - 1] + cost < best: best, bk = dp[k][j - 1] + cost, k
            dp[i][j], back[i][j] = best, bk
    if dp[n][m] >= INF: return cl
    out, i = [], n
    for j in range(m, 0, -1):
        k = back[i][j]; run = cl[k:i]
        parts = []
        for r in run: parts += (r.get('parts') or [])
        out.append(dict(parts=parts or None, x0=run[0]['x0'], x1=run[-1]['x1'],
                        y0=min(r['y0'] for r in run), y1=max(r['y1'] for r in run), cut=any(r.get('cut') for r in run)))
        i = k
    return out[::-1]


def words_of(text):
    return [w for w in text.split(' ') if w]


def segment_line(sub, ybase, guides, text, xh_px):
    """returns list of (char, glyphdict) for the expected text of this line"""
    mask = ink_mask(sub, guides)
    lab, comps = components(mask)
    comps = [k for k in comps if not is_scribble(k, lab)]
    groups = group_marks(comps, xh_px)
    if not groups: return []
    # cluster groups into words by gap
    gaps = [groups[i + 1]['x0'] - groups[i]['x1'] for i in range(len(groups) - 1)]
    words = words_of(text)
    if len(words) > 1 and gaps:
        thr = sorted(gaps)[-(len(words) - 1)] if len(gaps) >= len(words) - 1 else max(gaps) + 1
        thr = max(thr, 0.5 * xh_px)
        clusters, cur = [], [groups[0]]
        for g, gap in zip(groups[1:], gaps):
            if gap >= thr and len(clusters) < len(words) - 1:
                clusters.append(cur); cur = [g]
            else:
                cur.append(g)
        clusters.append(cur)
    else:
        clusters = [groups]
    if len(clusters) != len(words):
        clusters = [groups]; words = [''.join(words)]
    result = []
    for word, cl in zip(words, clusters):
        need = len(word)
        while len(cl) < need:                    # touching letters: split the widest
            i = max(range(len(cl)), key=lambda i: cl[i]['x1'] - cl[i]['x0'])
            pieces = split_group(cl[i], lab, mask, 2)
            if len(pieces) < 2: break
            cl[i:i + 1] = pieces
        if len(cl) > need:                       # multi-stroke letters: DP alignment
            cl = align_runs(cl, word, xh_px, ybase)
        if len(cl) != need:
            print(f'  ! could not align "{word}" ({len(cl)} strokes for {need} chars) — skipped')
            continue
        for ch, g in zip(word, cl):
            if g.get('parts'):
                gm = np.zeros_like(mask)
                for k in g['parts']: gm |= (lab == k['idx'])
            else:
                gm = np.zeros_like(mask); gm[g['y0']:g['y1'], g['x0']:g['x1']] = mask[g['y0']:g['y1'], g['x0']:g['x1']]
            ys, xs = np.where(gm)
            if len(xs) == 0: continue
            result.append((ch, dict(mask=gm, bbox=(xs.min(), ys.min(), xs.max() + 1, ys.max() + 1), ybase=ybase,
                                    main_bbox=(g['x0'], g['y0'], g['x1'], g['y1']))))
    return result


# ============================================================ glyph prep
def body_top(ch, g):
    if ch in ACC_LOW or ch in ACC_UP or ch in 'ij':
        return g['ybase'] - g['main_bbox'][1]
    return g['ybase'] - g['bbox'][1]


def prepared(ch, g):
    x0, y0, x1, y1 = g['bbox']
    if ch not in DESCENDERS and ch not in NOSNAP:
        if abs(y1 - g['ybase']) > 7:
            return dict(g, ybase=y1 - 1.5)
    return g


def stroke_width(g):
    x0, y0, x1, y1 = g['bbox']
    m = np.pad(g['mask'][y0:y1, x0:x1].astype(np.uint8), 2)
    dt = cv2.distanceTransform(m, cv2.DIST_L2, 5)
    sk = skeletonize(m.astype(bool))
    return 2.0 * float(np.median(dt[sk])) if sk.any() else 8.0


def _smooth(p, w):
    if len(p) < w * 2: return p
    k = np.ones(w) / w; out = np.empty_like(p)
    for d in (0, 1):
        out[:, d] = np.convolve(np.r_[p[-w:, d], p[:, d], p[:w, d]], k, 'same')[w:-w]
    return out


def _resample(p, step):
    q = np.r_[p, p[:1]]
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(q, axis=0), axis=1))]
    n = max(6, int(d[-1] / step)); t = np.linspace(0, d[-1], n, endpoint=False)
    return np.c_[np.interp(t, d, q[:, 0]), np.interp(t, d, q[:, 1])]


def _corners(p):
    a = np.roll(p, 1, 0) - p; b = np.roll(p, -1, 0) - p
    na = np.linalg.norm(a, axis=1) + 1e-9; nb = np.linalg.norm(b, axis=1) + 1e-9
    return np.degrees(np.arccos(np.clip((a * b).sum(1) / (na * nb), -1, 1))) < CORNER


def trace(g, pen, K, delta_pre=0.0):
    x0, y0, x1, y1 = g['bbox']; pad = 4
    sub = g['mask'][max(0, y0 - pad):y1 + pad, max(0, x0 - pad):x1 + pad].astype(np.uint8) * 255
    oy, ox = max(0, y0 - pad), max(0, x0 - pad)
    big = cv2.resize(sub, None, fx=UP, fy=UP, interpolation=cv2.INTER_CUBIC)
    big = cv2.GaussianBlur(big, (0, 0), UP * 0.6)
    _, big = cv2.threshold(big, 127, 255, cv2.THRESH_BINARY)
    r = int(round(abs(delta_pre) / 2 * UP))
    if r >= 1:
        ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
        big = cv2.dilate(big, ker) if delta_pre > 0 else cv2.erode(big, ker)
    cnts, _ = cv2.findContours(big, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    ybase = g['ybase']
    P = lambda px, py: (int(round((ox + px / UP - x0) * K + SB0)), int(round((ybase - (oy + py / UP)) * K)))
    for cnt in cnts:
        if cv2.contourArea(cnt) < 30 * UP * UP / 16: continue
        p = _resample(_smooth(cnt.reshape(-1, 2).astype(float), SMOOTH), RESAMPLE)
        if len(p) < 6: continue
        corner = _corners(p); pts = [P(*q) for q in p]; n = len(pts)
        pen.moveTo(pts[0])
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            if corner[i] or corner[(i + 1) % n]:
                pen.lineTo(b); continue
            pm, pa, pb, pp = (np.array(pts[j], float) for j in ((i - 1) % n, i, (i + 1) % n, (i + 2) % n))
            c1 = pa + (pb - pm) / 6.0; c2 = pb - (pp - pa) / 6.0
            pen.curveTo(tuple(int(v) for v in np.round(c1)), tuple(int(v) for v in np.round(c2)), b)
        pen.closePath()
    return int(round((x1 - x0) * K)) + 2 * SB0


# ============================================================ spacing / kerning
STEP = 10; ROWS = np.arange(-280, 900, STEP)


def profile(rec):
    left = np.full(len(ROWS), np.nan); right = np.full(len(ROWS), np.nan)
    polys, cur = [], []
    for op, args in rec:
        if op == 'moveTo': cur = [args[0]]
        elif op == 'lineTo': cur.append(args[0])
        elif op == 'curveTo':
            p0 = cur[-1]; c1, c2, p3 = args
            for t in (0.25, 0.5, 0.75, 1.0):
                u = 1 - t
                cur.append((u**3*p0[0] + 3*u*u*t*c1[0] + 3*u*t*t*c2[0] + t**3*p3[0],
                            u**3*p0[1] + 3*u*u*t*c1[1] + 3*u*t*t*c2[1] + t**3*p3[1]))
        elif op == 'closePath':
            if len(cur) > 2: polys.append(np.array(cur, float))
            cur = []
    for i, y in enumerate(ROWS):
        xs = []
        for p in polys:
            a = p; b = np.roll(p, -1, axis=0)
            m = ((a[:, 1] <= y) & (b[:, 1] > y)) | ((b[:, 1] <= y) & (a[:, 1] > y))
            if not m.any(): continue
            t = (y - a[m, 1]) / (b[m, 1] - a[m, 1]); xs.extend(a[m, 0] + t * (b[m, 0] - a[m, 0]))
        if xs: left[i] = min(xs); right[i] = max(xs)
    return left, right


def shift(rec, dx):
    return [(op, tuple((p[0] + dx, p[1]) for p in args)) if args else (op, args) for op, args in rec]


def space_all(shapes, metrics):
    new_s, new_m, prof = {}, {}, {}
    for n, rec in shapes.items():
        adv = metrics[n][0]
        if not rec: new_s[n] = rec; new_m[n] = metrics[n]; continue
        l, r = profile(rec); ok = ~np.isnan(l)
        if ok.sum() < 2: new_s[n] = rec; new_m[n] = metrics[n]; continue
        ys = ROWS[ok]; lo, hi = ys.min() + 20, max(ys.max() - 20, ys.min() + 20)
        band = (ROWS >= lo) & (ROWS <= hi) & ok
        if band.sum() == 0: band = ok
        lmin_b, rmax_b = np.nanmin(l[band]), np.nanmax(r[band])
        ol = np.clip(l[band], lmin_b, lmin_b + DEPTH).mean()
        orr = adv - np.clip(r[band], rmax_b - DEPTH, rmax_b).mean()
        above = (ROWS >= -25) & ok
        lmin, rmax = (np.nanmin(l[above]), np.nanmax(r[above])) if above.sum() >= 2 else (np.nanmin(l), np.nanmax(r))
        dl = max(round(TARGET_SB - ol), MIN_SB - lmin); dr = max(round(TARGET_SB - orr), MIN_SB - (adv - rmax))
        new_s[n] = shift(rec, dl); new_m[n] = (int(round(max(120, adv + dl + dr))), 0)
    for n, rec in new_s.items():
        prof[n] = profile(rec) if rec else (None, None)
    return new_s, new_m, prof


def pair_kern(prof, metrics, names):
    kern = {}
    for a in names:
        la, ra = prof[a]
        if ra is None: continue
        adva = metrics[a][0]; rmax = np.nanmax(ra); ra_c = np.clip(ra, rmax - DEPTH, rmax)
        for b in names:
            lb, rb = prof[b]
            if lb is None: continue
            lmin = np.nanmin(lb); lb_c = np.clip(lb, lmin, lmin + DEPTH)
            both = (~np.isnan(ra)) & (~np.isnan(lb))
            if both.sum() < 2: continue
            k = int(round(TARGET_GAP - ((adva - ra_c[both]) + lb_c[both]).min()))
            k = max(MAX_KERN, min(MIN_KERN, k))
            if abs(k) >= 12: kern[(a, b)] = k
    return kern


# ============================================================ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--scans', nargs='+', required=True)
    ap.add_argument('--layout', default='template_flow_layout.json')
    ap.add_argument('--family', default='My Hand')
    ap.add_argument('--style', default='Regular')
    ap.add_argument('--version', default='1.0')
    ap.add_argument('--weight', type=float, default=1.0, help='stroke width multiplier (1.1 = 10%% bolder)')
    ap.add_argument('--out', default='out')
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    L = json.load(open(args.layout))
    scans = sorted(args.scans)
    pages = {}
    for i, path in enumerate(scans):
        pages[i + 1] = register(path, L); print(f'registered page {i+1}: {path}')

    XH_GUESS = L['guides_pt']['xheight'] * SCALE
    glyphs = {}            # (ch, variant) -> g
    observed = []          # (ch_a, g_a, ch_b, g_b) consecutive pairs from sentences/kerning lines
    for ln in L['lines']:
        if ln['page'] not in pages: continue
        sub, ybase, guides = strip(pages[ln['page']], ln, L)
        seq = segment_line(sub, ybase, guides, ln['text'], XH_GUESS)
        print(f"{ln['tag']}: {len(seq)}/{len(ln['text'].replace(' ', ''))} chars")
        if ln['kind'] == 'glyphs':
            v = int(ln['tag'].rsplit('_v', 1)[1]) if '_v' in ln['tag'] else 1
            for ch, g in seq:
                glyphs.setdefault((ch, v), g)
        else:
            for ch, g in seq:
                key = next((k for k in ((ch, 1), (ch, 2), (ch, 3)) if k not in glyphs), None)
                if key and key[1] > 1 and (ch, 1) in glyphs:   # extra variant from running text
                    pass
            # adjacent pairs inside words for measured kerning
            words = words_of(ln['text']); i = 0
            for w in words:
                chunk = seq[i:i + len(w)]; i += len(w)
                if len(chunk) != len(w): continue
                for (ca, ga), (cb, gb) in zip(chunk[:-1], chunk[1:]):
                    observed.append((ca, ga, cb, gb))
    if not glyphs:
        sys.exit('no glyphs found')

    # contact sheet so you can check every assignment by eye
    keys = sorted(glyphs, key=lambda k: (k[0], k[1])); tw, th, cols = 110, 130, 20
    sheet = np.full(((len(keys) + cols - 1) // cols * th, cols * tw), 255, np.uint8)
    for i, k in enumerate(keys):
        g = glyphs[k]; x0, y0, x1, y1 = g['bbox']
        m = (~g['mask'][y0:y1, x0:x1]).astype(np.uint8) * 255
        sc = min((tw - 10) / max(1, m.shape[1]), (th - 24) / max(1, m.shape[0]), 1.0)
        m = cv2.resize(m, (max(1, int(m.shape[1] * sc)), max(1, int(m.shape[0] * sc))))
        r, c = divmod(i, cols); tile = sheet[r * th:(r + 1) * th, c * tw:(c + 1) * tw]
        tile[20:20 + m.shape[0], 5:5 + m.shape[1]] = m
        cv2.putText(tile, f'{k[0]} v{k[1]}'.encode('ascii', 'replace').decode(), (3, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, 0, 1)
    cv2.imwrite(os.path.join(args.out, 'glyphs-check.png'), sheet)

    glyphs = {k: prepared(k[0], g) for k, g in glyphs.items()}
    med = lambda S: float(np.median([body_top(c, g) for (c, v), g in glyphs.items() if c in S] or [XH_GUESS]))
    XH, ASC, CAP, DIGH = med(XSET), med(ASET), med(CAPS), med(DIGITS)
    CAP_T = max(CAP, CAP_RATIO * XH); DIG_T = max(DIGH, DIG_RATIO * XH)
    K = CAP_UNITS / CAP_T
    print(f'x-height {XH:.1f}px ascender {ASC:.1f} cap {CAP:.1f}->{CAP_T:.1f} digits {DIGH:.1f}->{DIG_T:.1f}')

    def nscale(ch, g):
        top = body_top(ch, g)
        tgt = (XH if ch in XSET or ch in ACC_LOW or ch in DSET else ASC if ch in ASET else
               CAP_T if ch in CAPS or ch in ACC_UP else DIG_T if ch in DIGITS else None)
        return 1.0 if tgt is None else float(np.clip(tgt / max(top, 1), *NORM_CLIP))

    SW = {k: stroke_width(g) * nscale(k[0], g) for k, g in glyphs.items()}
    T_SW = float(np.median([w for (c, v), w in SW.items() if c.isalpha()])) * args.weight

    shapes, metrics, cmap, variants = {}, {}, {}, {}
    for ch in sorted({c for c, v in glyphs}):
        names = []
        for i, v in enumerate(sorted(v for (c, v) in glyphs if c == ch)):
            g = glyphs[(ch, v)]; s = nscale(ch, g)
            n = gname(ch) if i == 0 else f'{gname(ch)}.alt{i}'
            rec = RecordingPen()
            adv = trace(g, rec, K * s, (T_SW - SW[(ch, v)]) / s)
            if not rec.value: continue
            shapes[n] = rec.value; metrics[n] = (adv, 0); names.append(n)
        if names: cmap[ord(ch)] = names[0]; variants[ch] = names
    shapes['.notdef'] = []; metrics['.notdef'] = (500, 0)
    shapes['space'] = []; metrics['space'] = (360, 0)
    cmap[0x20] = cmap[0xA0] = 'space'
    for a, b in ((0x201D, 0x201C), (0x2019, 0x2018), (0x2014, 0x2013)):
        if b in cmap and a not in cmap: cmap[a] = cmap[b]

    shapes, metrics, PROF = space_all(shapes, metrics)
    base = [ns[0] for ns in variants.values()]
    KERN = pair_kern(PROF, metrics, base)
    # measured kerning from running text overrides computed values
    meas = {}
    for ca, ga, cb, gb in observed:
        if ca not in variants or cb not in variants: continue
        na, nb = variants[ca][0], variants[cb][0]
        gap_px = gb['bbox'][0] - ga['bbox'][2]
        sa, sb_ = nscale(ca, ga), nscale(cb, gb)
        gap_u = gap_px * K * (sa + sb_) / 2
        la, ra = PROF[na]; lb, rb = PROF[nb]
        rsb_a = metrics[na][0] - np.nanmax(ra); lsb_b = np.nanmin(lb)
        meas.setdefault((na, nb), []).append(gap_u - (rsb_a + lsb_b))
    for k, vals in meas.items():
        v = int(round(float(np.median(vals))))
        v = max(MAX_KERN, min(MIN_KERN * 3, v))
        if abs(v) >= 12: KERN[k] = v
        else: KERN.pop(k, None)
    print(f'glyphs {len(shapes)}  kern pairs {len(KERN)} ({len(meas)} measured from your writing)')

    order = ['.notdef', 'space'] + sorted(n for n in shapes if n not in ('.notdef', 'space'))
    cls = {}; fea = []
    for ch, ns in variants.items():
        cls[ns[0]] = f'@k_{ns[0].replace(".", "_")}'; fea.append(f'{cls[ns[0]]} = [{" ".join(ns)}];')
    fea.append('feature kern {'); fea += [f'  pos {cls[a]} {cls[b]} {v};' for (a, b), v in sorted(KERN.items())]; fea.append('} kern;')
    multi = [ns for ns in variants.values() if len(ns) >= 2]
    if multi:
        fea.append(f'@set1 = [{" ".join(n[0] for n in multi)}];')
        fea.append(f'@set2 = [{" ".join(n[1] for n in multi)}];')
        fea.append(f'@set3 = [{" ".join(n[2] if len(n) >= 3 else n[1] for n in multi)}];')
        fea += ['feature calt {', "  sub @set1 @set1' by @set2;", "  sub @set2 @set1' by @set3;", '} calt;']
    FEA = '\n'.join(fea)

    ps = f"{args.family.replace(' ', '')}-{args.style}"
    names = dict(familyName=args.family, styleName=args.style, psName=ps, version=f'Version {args.version}',
                 fullName=f'{args.family} {args.style}', uniqueFontIdentifier=f'{ps};{args.version}',
                 typographicFamily=args.family, typographicSubfamily=args.style)

    def common(fb):
        fb.setupGlyphOrder(order); fb.setupCharacterMap(cmap); fb.setupHorizontalMetrics(metrics)
        fb.setupHorizontalHeader(ascent=900, descent=-280, lineGap=0); fb.setupNameTable(names)
        fb.setupOS2(sTypoAscender=900, sTypoDescender=-280, sTypoLineGap=0, usWinAscent=980, usWinDescent=320,
                    sCapHeight=700, sxHeight=int(XH * K), usWeightClass=500, achVendID='HAND', fsType=0)
        fb.setupPost(isFixedPitch=0, italicAngle=0, underlinePosition=-100, underlineThickness=60)
        addOpenTypeFeaturesFromString(fb.font, FEA)

    fb = FontBuilder(UPM, isTTF=True); gl = {}
    for n, rec in shapes.items():
        tp = TTGlyphPen(None); pen = Cu2QuPen(tp, max_err=1.0)
        for op, a in rec: getattr(pen, op)(*a)
        gl[n] = tp.glyph()
    fb.setupGlyf(gl); common(fb); fb.setupDummyDSIG(); fb.save(os.path.join(args.out, ps + '.ttf'))
    fb = FontBuilder(UPM, isTTF=False); css = {}
    for n, rec in shapes.items():
        pen = T2CharStringPen(metrics[n][0], None)
        for op, a in rec: getattr(pen, op)(*a)
        css[n] = pen.getCharString()
    fb.setupGlyphOrder(order)
    fb.setupCFF(ps, {'FullName': f'{args.family} {args.style}', 'FamilyName': args.family, 'Weight': args.style}, css, {})
    common(fb); fb.save(os.path.join(args.out, ps + '.otf'))

    # specimen
    from PIL import ImageDraw, ImageFont
    ttf = os.path.join(args.out, ps + '.ttf')
    im = Image.new('RGB', (1600, 520), (140, 80, 200)); d = ImageDraw.Draw(im)
    f = ImageFont.truetype(ttf, 46); y = 20
    for t in ['ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789', 'abcdefghijklmnopqrstuvwxyz äöü ÄÖÜ ß åÅ',
              'The quick brown fox jumps over the lazy dog.', 'Falsches Üben von Xylophonmusik quält jeden größeren Zwerg.',
              'Voix ambiguë d\'un cœur qui préfère les kiwis. ¿Qué? ¡Sí! Så är det.',
              '„Wirklich?“ – 19,50 € & 100 % (Ja!)']:
        d.text((30, y), t, font=f, fill=(255, 255, 255), features=['kern', 'calt']); y += 78
    im.save(os.path.join(args.out, ps + '-specimen.png'))
    print('written to', args.out)


if __name__ == '__main__':
    main()
