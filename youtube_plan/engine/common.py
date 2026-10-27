import json, math, re, subprocess, os
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1920, 1080, 30
import sys
JOB = os.environ.get('YT_JOB') or (sys.argv[0] and '')
JOB = os.path.abspath(JOB) if JOB else JOB
A = JOB + '/assets/'
V = JOB + '/voix/'
OUTDIR = os.environ.get('YT_OUT', '/tmp/yt_out')
os.makedirs(OUTDIR, exist_ok=True)
if JOB + '/code' not in sys.path: sys.path.insert(0, JOB + '/code')
GREEN = (15, 91, 89); ORANGE = (240, 138, 46); DARK = (30, 41, 51); LIGHT = (245, 247, 249)
GOLD = (231, 195, 108); GREY = (107, 114, 128); WHITE = (255, 255, 255); TERRA = (199, 91, 58)


@lru_cache(None)
def font(sz):
    return ImageFont.truetype(A + 'Poppins-Bold.ttf', sz)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def lerp(a, b, t):
    return a + (b - a) * t


def e_out(t):
    t = clamp(t); return 1 - (1 - t) ** 3


def e_io(t):
    t = clamp(t); return 3 * t * t - 2 * t * t * t


def e_back(t):
    t = clamp(t); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


@lru_cache(None)
def img(name, mode='RGBA'):
    return Image.open(A + name).convert(mode)


def tw(txt, sz):
    return font(sz).getlength(txt)


def text(d, xy, txt, sz, fill=DARK, anchor='la', stroke=0, stroke_fill=None):
    d.text(xy, txt, font=font(sz), fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=stroke_fill)


def rrect(d, box, r, fill=None, outline=None, width=1):
    d.rounded_rectangle(box, r, fill=fill, outline=outline, width=width)


def shadow_card(base, box, r=28, fill=WHITE, blur=18, off=8, alpha=60):
    x0, y0, x1, y1 = [int(v) for v in box]
    pad = blur * 3
    sh = Image.new('RGBA', (x1 - x0 + 2 * pad, y1 - y0 + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((pad, pad, pad + x1 - x0, pad + y1 - y0), r, fill=(0, 0, 0, alpha))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(sh, (x0 - pad, y0 - pad + off))
    d = ImageDraw.Draw(base)
    d.rounded_rectangle((x0, y0, x1, y1), r, fill=fill)


def paste_alpha(base, im, xy, opacity=1.0):
    if opacity < 1:
        im = im.copy(); a = im.getchannel('A').point(lambda v: int(v * opacity)); im.putalpha(a)
    base.alpha_composite(im, (int(xy[0]), int(xy[1])))


# ---- mots depuis les chunks Gradium
def words_of(name):
    ch = json.load(open(V + name + '.chunks.json'))
    out = []
    for c in ch:
        toks = c['text'].split()
        if not toks:
            continue
        tot = sum(len(t) + 1 for t in toks)
        t0 = c['start_s']; span = c['stop_s'] - c['start_s']
        acc = 0
        for t in toks:
            s = t0 + span * acc / tot; acc += len(t) + 1
            e = t0 + span * acc / tot
            out.append({'w': t, 's': s, 'e': e})
    return out


def norm(w):
    return re.sub(r'[^\wàâäéèêëîïôöùûüçœ\'-]', '', w.lower())


def find(words, pat, nth=0, after=0.0):
    k = 0
    for w in words:
        if w['s'] + 1e-6 >= after and re.fullmatch(pat, norm(w['w'])):
            if k == nth:
                return w['s']
            k += 1
    raise KeyError(pat)


def find_e(words, pat, nth=0, after=0.0):
    k = 0
    for w in words:
        if w['s'] + 1e-6 >= after and re.fullmatch(pat, norm(w['w'])):
            if k == nth:
                return w['e']
            k += 1
    raise KeyError(pat)


# ---- sous-titres Hormozi : un mot à la fois, surfaces « 13 m² »
NUMS = {'quinze': '15', 'seize': '16', 'douze': '12', 'treize': '13', 'dix-huit': '18', 'trente-huit': '38', 'trente-six': '36', 'quatorze': '14', 'vingt-sept': '27', 'vingt-deux': '22', 'sept': '7', 'six': '6', 'cinq': '5', 'quatre': '4', 'huit': '8', 'neuf': '9', 'deux': '2'}


def caption_tokens(words):
    toks = []; i = 0
    while i < len(words):
        w = words[i]; n = norm(w['w'])
        if n == 'trois' and i + 4 < len(words) and norm(words[i + 1]['w']) == 'cent' and norm(words[i + 2]['w']) == 'quatorze' and norm(words[i + 3]['w']) == 'mètres':
            toks.append({'t': '314 m²', 's': w['s'], 'e': words[i + 4]['e'], 'hi': True}); i += 5; continue
        if n in NUMS and i + 2 < len(words) and norm(words[i + 1]['w']) == 'mètres' and norm(words[i + 2]['w']) == 'carrés':
            toks.append({'t': NUMS[n] + ' m²', 's': w['s'], 'e': words[i + 2]['e'], 'hi': True}); i += 3; continue
        if n == 'chambre' and i + 1 < len(words) and re.fullmatch(r'\d', norm(words[i + 1]['w'])):
            toks.append({'t': 'CHAMBRE ' + norm(words[i + 1]['w']), 's': w['s'], 'e': words[i + 1]['e'], 'hi': False}); i += 2; continue
        toks.append({'t': re.sub(r'[,.:;!?]', '', w['w']).upper(), 's': w['s'], 'e': w['e'], 'hi': False}); i += 1
    # prolonger jusqu'au mot suivant pour éviter les clignotements
    for k in range(len(toks) - 1):
        toks[k]['e'] = max(toks[k]['e'], min(toks[k + 1]['s'], toks[k]['e'] + 0.25))
    return toks


def draw_caption(base, toks, t, cy=1030, sz=72):
    return  # sous-titres retirés : YouTube les génère
    cur = None
    for k in toks:
        if k['s'] - 0.02 <= t < k['e'] + 0.02:
            cur = k
    if not cur or not cur['t'].strip():
        return
    p = e_back((t - cur['s']) / 0.14)
    s = int(sz * (0.82 + 0.18 * p))
    d = ImageDraw.Draw(base)
    d.text((W // 2, cy), cur['t'], font=font(s), fill=ORANGE if cur['hi'] else WHITE, anchor='mm', stroke_width=9, stroke_fill=GREEN)


# ---- ffmpeg
class Writer:
    def __init__(self, path, crf=19):
        self.p = subprocess.Popen(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                                   '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', str(crf), '-pix_fmt', 'yuv420p', path],
                                  stdin=subprocess.PIPE)

    def write(self, im):
        self.p.stdin.write(im.convert('RGB').tobytes())

    def close(self):
        self.p.stdin.close(); self.p.wait()


def render(path, dur, fn, start=0):
    wr = Writer(path)
    n = int(round(dur * FPS))
    for i in range(n):
        wr.write(fn(i / FPS))
    wr.close()


def header(base, title_right='4 chambres · 2 niveaux · 314 m²'):
    d = ImageDraw.Draw(base)
    d.rectangle((0, 0, W, 104), fill=GREEN)
    text(d, (48, 52), 'DUPLEX D4-004', 44, WHITE, 'lm')
    text(d, (W - 250, 52), title_right, 32, GOLD, 'rm')
    lg = img('logo_white.png').copy(); lg.thumbnail((190, 90)); base.alpha_composite(lg, (W - 30 - lg.width, 52 - lg.height // 2))


# ---- durées de séquences (voix + marge) et décalages globaux
import wave as _wave
def _wd(k):
    w = _wave.open(V + k + '.wav'); return w.getnframes() / w.getframerate()
_TAIL = dict(intro=0.6, chiffres=0.6, visite=1.0, visite2=1.0, invit=0.24, rendus=1.0, terrain=1.0, devis=1.0, fin=6.0)
D = {k: math.ceil((_wd(k) + t) * FPS) / FPS for k, t in _TAIL.items()}
D['jingle'] = 4.011; D['catalogue'] = 35.8
ORDER = ['intro', 'jingle', 'chiffres', 'visite', 'visite2', 'invit', 'rendus', 'catalogue', 'terrain', 'devis', 'fin']
OFF = {}
_acc = 0.0
for _k in ORDER:
    OFF[_k] = _acc; _acc += D[_k]
TOTAL = _acc


def finish(im, tg, wm=True, alpha=1.0):
    """filigranes mobiles (2 logos) + pastille wooplans.com ; tg = temps global"""
    im = im.convert('RGBA')
    if not wm:
        return im.convert('RGB')
    lg = img('wm_logo.png')
    w, h = lg.size
    for (a, b, c, d_) in ((0.31, 0.19, 1.3, 0.0), (0.23, 0.27, 2.6, 4.1)):
        x = (W - w) * (0.5 + 0.5 * math.sin(tg * a + (0 if a == 0.31 else c)))
        y = (H - h) * (0.5 + 0.5 * math.sin(tg * b + (c if a == 0.31 else d_)))
        paste_alpha(im, lg, (x, y), 0.17 * alpha)
    bd = img('badge_url.png')
    paste_alpha(im, bd, (36, H - bd.height - 18), alpha)
    return im.convert('RGB')


# ---- boîte de rendus qui défilent (maison toujours visible)
_RS = {}
def rsrc(i):
    i %= 10
    if i not in _RS:
        _RS[i] = Image.open(A + f'R{i}.png').convert('RGB').resize((1280, 720), Image.LANCZOS)
    return _RS[i]
_RM = {}
def render_box(base, box, t, period=4.4, start=0, pan=0.05):
    x0, y0, x1, y1 = [int(v) for v in box]; w, h = x1 - x0, y1 - y0
    T = t / period + start; i = int(T); fr = T - i
    def sl(k, u):
        src = rsrc(k); sw, sh = src.size
        z = 1.10 + 0.12 * u if k % 2 == 0 else 1.22 - 0.12 * u
        cw, chh = sw / z, sh / z
        asp = w / h
        if cw / chh > asp: cw = chh * asp
        else: chh = cw / asp
        px = 0.5 + (pan if k % 3 == 0 else -pan if k % 3 == 1 else 0) * (u - 0.5) * 2
        cx0 = clamp(px * sw - cw / 2, 0, sw - cw); cy0 = clamp(0.5 * sh - chh / 2, 0, sh - chh)
        return src.resize((w, h), Image.LANCZOS, box=(cx0, cy0, cx0 + cw, cy0 + chh))
    cur = sl(i, fr)
    if fr > 0.82:
        cur = Image.blend(cur, sl(i + 1, 0.0), e_io((fr - 0.82) / 0.18))
    key = (w, h)
    if key not in _RM:
        m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), 22, fill=255); _RM[key] = m
    shadow_card(base, (x0 - 6, y0 - 6, x1 + 6, y1 + 6), r=26)
    base.paste(cur.convert('RGBA'), (x0, y0), _RM[key])
