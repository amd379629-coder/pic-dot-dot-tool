import os, sys, time, shutil, pickle, argparse
from PIL import Image, ImageFilter

# ================= সেটিংস (এখানে বদলাও) =================
TITLE    = "GQ ATIKUL"          # বড় অক্ষরের ব্যানার (A-Z ও ডিজিট)
SUBTITLE = "SECURE TERMINAL"    # নিচের ছোট লাইন
STATUS   = "ACCESS GRANTED"     # একদম নিচের স্ট্যাটাস লাইন ("" দিলে বাদ)
COLS    = 0           # 0 = ফোনের পুরো চওড়া জুড়ে, বা সংখ্যা দাও (যেমন 110)
LOOK    = "keep"      # keep = পুরো ছবি, অনুপাত ঠিক রেখে স্ক্রিনে ধরাবে (ডিফল্ট) | wide = চওড়া করতে একটু চাপবে | crop = উপর-নিচ কাটবে
SQUEEZE = 0.85        # wide মোডে উচ্চতা সর্বোচ্চ কতটা চাপবে (0.85 = ১৫% কম; ১ = একদম চাপবে না)
ROWS    = 0           # স্ক্রিনের লাইন সংখ্যা ভুল ধরলে এখানে নিজে দাও (0 = নিজে মাপবে)
MODE    = "auto"      # auto | ink | glow | photo
THEME   = "cyan"      # cyan | gold | red | green | purple | white (সাদাকালো ছবির রঙ)
BRIGHT  = 1.5         # রঙিন ছবির উজ্জ্বলতা
SWEEPS  = 1           # আলোর ঝিলিক কতবার ঘুরবে
ANIMATE = True        # false দিলে অ্যানিমেশন ছাড়া সোজা দেখাবে
FIT     = True        # True = যত লম্বা ছবিই হোক, ফোনের স্ক্রিনে পুরোটা ধরবে
NAMES = ["termux.jpg", "termux.jpeg", "termux.png", "termux.webp"]
DIRS  = ["~", "/sdcard/Download"]   # যেটার ছবি নতুন, সেটাই নেবে
# ========================================================

THEMES = {
    "cyan":   [123, 87, 51, 45, 39, 33],
    "gold":   [229, 227, 220, 214, 208, 202],
    "red":    [217, 210, 203, 196, 160, 124],
    "green":  [157, 120, 84, 46, 40, 34],
    "purple": [225, 219, 213, 177, 171, 135],
    "white":  [255, 253, 251, 249, 247, 245],
}
BITS = [(0,0,0x01),(0,1,0x02),(0,2,0x04),(1,0,0x08),
        (1,1,0x10),(1,2,0x20),(0,3,0x40),(1,3,0x80)]
CACHE = os.path.expanduser("~/.termux_art_cache")
VERSION = "v5"        # কোড বদলালে পুরোনো ক্যাশ নিজে বাতিল হবে

class C:
    RED = "\033[91m"; GREEN = "\033[92m"; BOLD = "\033[1m"; RESET = "\033[0m"

# ---------- বড় অক্ষরের ফন্ট (৩ লাইন) ----------
FONT = {
    "A": ["▄▀▄", "█▀█", "▀ ▀"], "B": ["█▀▄", "█▀▄", "▀▀ "],
    "C": ["▄▀▀", "█  ", "▀▄▄"], "D": ["█▀▄", "█ █", "▀▀ "],
    "E": ["█▀▀", "█▀▀", "▀▀▀"], "F": ["█▀▀", "█▀ ", "▀  "],
    "G": ["▄▀▀", "█ ▄", "▀▀▀"], "H": ["█ █", "█▀█", "▀ ▀"],
    "I": ["▀█▀", " █ ", "▀▀▀"], "J": ["  █", "  █", "▀▀ "],
    "K": ["█ █", "█▀▄", "▀ ▀"], "L": ["█  ", "█  ", "▀▀▀"],
    "M": ["█▄▄█", "█  █", "▀  ▀"], "N": ["█▄ █", "█ ▀█", "▀  ▀"],
    "O": ["█▀█", "█ █", "▀▀▀"], "P": ["█▀▄", "█▀ ", "▀  "],
    "Q": ["▄▀▄", "█ █", "▀▄█"], "R": ["█▀▄", "█▀▄", "▀ ▀"],
    "S": ["▄▀▀", "▀▀▄", "▄▄▀"], "T": ["▀█▀", " █ ", " ▀ "],
    "U": ["█ █", "█ █", "▀▀▀"], "V": ["█ █", "█ █", " ▀ "],
    "W": ["█  █", "█▄▄█", "▀▀▀▀"], "X": ["▀▄▀", " █ ", "▀ ▀"],
    "Y": ["█ █", " █ ", " ▀ "], "Z": ["▀▀█", " █ ", "█▀▀"],
    "0": ["█▀█", "█ █", "▀▀▀"], "1": ["▄█ ", " █ ", "▀▀▀"],
    "2": ["▀▀█", "▄▀ ", "▀▀▀"], "3": ["▀▀█", " ▀█", "▀▀▀"],
    "4": ["█ █", "▀▀█", "  ▀"], "5": ["█▀▀", "▀▀▄", "▀▀ "],
    "6": ["█▀▀", "█▀█", "▀▀▀"], "7": ["▀▀█", "  █", "  ▀"],
    "8": ["█▀█", "█▀█", "▀▀▀"], "9": ["█▀█", "▀▀█", "▀▀▀"],
    "-": ["   ", "▀▀▀", "   "], ".": ["  ", "  ", " ▀"],
    " ": ["  ", "  ", "  "],
}

def big_text(text):
    rows = ["", "", ""]
    for ch in text.upper():
        g = FONT.get(ch, FONT[" "])
        for i in range(3):
            rows[i] += g[i] + " "
    return [r.rstrip() for r in rows]

def fg(rgb):
    return "\033[38;2;%d;%d;%dm" % rgb

def mix(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

def build_banner(tw):
    """ব্যানারের লাইনগুলো বানায় (লাইনের তালিকা ফেরত দেয়)"""
    big = big_text(TITLE)
    bigw = max(len(r) for r in big)
    if bigw * 2 + 10 <= tw:                  # জায়গা থাকলে অক্ষর দ্বিগুণ চওড়া
        big = ["".join(ch*2 for ch in r) for r in big]
        bigw *= 2
    sub = "[ " + " ".join(SUBTITLE.upper()) + " ]" if SUBTITLE else ""
    status = ("▌▌ " + STATUS + " ▐▐") if STATUS else ""
    if bigw + 6 > tw:                        # ফোন খুব সরু হলে সাধারণ লেখা
        big = [TITLE.upper()]; bigw = len(big[0])
        sub = SUBTITLE.upper()
        status = STATUS
    big = [r.ljust(bigw) for r in big]
    inner = max(max(bigw, len(sub), len(status)) + 14, 46)
    inner = min(inner, tw - 2)
    G1, G2 = (0, 255, 120), (0, 210, 255)    # সবুজ → নীল গ্রেডিয়েন্ট
    EDGE = (0, 150, 90)
    def edge(t):
        return fg(EDGE) + t + C.RESET
    def border(l, r, label, lcol):
        if label and inner >= len(label) + 8:
            rest = inner - 2 - len(label)
            return edge(l + "══") + fg(lcol) + C.BOLD + label + C.RESET + edge("═"*rest + r)
        return edge(l + "═"*inner + r)
    def row(txt, color):
        body = txt.center(inner)
        return edge("║") + fg(color) + C.BOLD + body + C.RESET + edge("║")
    # হ্যাকার-স্টাইল বাইনারি লাইন
    seed = 7; bits = ""
    for _ in range(inner - 4):
        seed = (seed * 1103515245 + 12345) & 0x7fffffff
        bits += "01"[(seed >> 16) & 1]
    lines = [border("╔", "╗", "[ ROOT@TERMUX ]", (255, 200, 0))]
    lines.append(edge("║") + fg((0, 95, 55)) + (" " + bits + " ").center(inner) + C.RESET + edge("║"))
    for i, r in enumerate(big):
        lines.append(row(r, mix(G1, G2, i / max(len(big) - 1, 1))))
    if sub:
        lines.append(edge("╟" + "─"*inner + "╢"))
        lines.append(row(sub, (170, 255, 220)))
    if status:
        lines.append(row(status, (255, 70, 70)))
    lines.append(border("╚", "╝", "[ AES-256 // ENCRYPTED ]", (0, 210, 255)))
    out = []
    for ln in lines:
        out.append(" " * max((tw - (inner + 2))//2, 0) + ln)
    return out

# ---------- ছবির কাজ ----------
def get_pixels(img):
    if hasattr(img, "get_flattened_data"):
        return list(img.get_flattened_data())
    return list(img.getdata())

def lum(p):
    return 0.299*p[0] + 0.587*p[1] + 0.114*p[2]

def xterm_rgb(n):
    if n >= 232:
        v = 8 + (n - 232) * 10
        return (v, v, v)
    n -= 16
    lv = [0, 95, 135, 175, 215, 255]
    return (lv[n // 36], lv[(n // 6) % 6], lv[n % 6])

def find_image(arg=None):
    if arg:
        p = os.path.expanduser(arg)
        return p if os.path.exists(p) else None
    best = None
    for d in DIRS:
        for n in NAMES:
            p = os.path.join(os.path.expanduser(d), n)
            if os.path.exists(p) and (best is None or os.path.getmtime(p) > os.path.getmtime(best)):
                best = p
    return best

# ---------- ছবি বিশ্লেষণ: ব্যাকগ্রাউন্ড ও ধরন নিজে বুঝে নেয় ----------
def analyze(path):
    im = Image.open(path)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bgim = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(bgim, im)
    im = im.convert("RGB")
    # ছোট ছবি বড় হবে, বড় ছবি ছোট হবে + ধার বাড়ানো হবে
    S = 700
    sc = S / max(im.size)
    im = im.resize((max(1, int(im.width*sc)), max(1, int(im.height*sc))), Image.LANCZOS)
    im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=120, threshold=3))
    w, h = im.size
    px = get_pixels(im)
    k = max(2, int(min(w, h) * 0.06))
    def corner(x0, y0):
        vals = [px[y*w + x] for y in range(y0, y0+k) for x in range(x0, x0+k)]
        return tuple(sorted(v[i] for v in vals)[len(vals)//2] for i in range(3))
    tl, tr, bl, br = corner(0, 0), corner(w-k, 0), corner(0, h-k), corner(w-k, h-k)
    def bg_at(u, v):
        return tuple((tl[i]*(1-u) + tr[i]*u)*(1-v) + (bl[i]*(1-u) + br[i]*u)*v for i in range(3))
    def dist(p, b):
        return max(abs(p[0]-b[0]), abs(p[1]-b[1]), abs(p[2]-b[2]))
    # কিনারার পিক্সেল কতটা একরঙা?
    ring = []
    for x in range(0, w, 3):
        ring += [(x, 0), (x, h-1)]
    for y in range(0, h, 3):
        ring += [(0, y), (w-1, y)]
    spread = sum(dist(px[y*w + x], bg_at(x/(w-1), y/(h-1))) for x, y in ring) / len(ring)
    uniform = spread < 18
    T = max(30.0, spread * 3.5)
    mask = [dist(px[y*w + x], bg_at(x/(w-1), y/(h-1))) > T for y in range(h) for x in range(w)]
    frac = sum(mask) / len(mask)
    box = (0, 0, w, h)
    valid = 0.004 < frac < 0.88
    keep = lambda u, v: True
    if valid:
        # ব্যাকগ্রাউন্ডের ছায়া/দাগ বাদ: শুধু বড় অংশগুলো রাখে
        B = 8
        gw, gh = (w + B - 1)//B, (h + B - 1)//B
        cnt = [0]*(gw*gh)
        for y in range(h):
            base = (y//B)*gw; ro = y*w
            for x in range(w):
                if mask[ro + x]:
                    cnt[base + x//B] += 1
        on = [c >= 0.2*B*B for c in cnt]
        comp = [-1]*(gw*gh); sizes = []
        for s0 in range(gw*gh):
            if on[s0] and comp[s0] < 0:
                cid = len(sizes); comp[s0] = cid; st = [s0]; sz = 0
                while st:
                    q = st.pop(); sz += 1; qy, qx = divmod(q, gw)
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            ny, nx = qy+dy, qx+dx
                            if 0 <= ny < gh and 0 <= nx < gw:
                                t = ny*gw + nx
                                if on[t] and comp[t] < 0:
                                    comp[t] = cid; st.append(t)
                sizes.append(sz)
        if sizes:
            keepc = set(i for i, z in enumerate(sizes) if z >= 0.15*max(sizes))
            keepb = [False]*(gw*gh)
            for s0 in range(gw*gh):
                if comp[s0] in keepc:
                    qy, qx = divmod(s0, gw)
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            ny, nx = qy+dy, qx+dx
                            if 0 <= ny < gh and 0 <= nx < gw:
                                keepb[ny*gw + nx] = True
            mask = [m and keepb[((i//w)//B)*gw + (i % w)//B] for i, m in enumerate(mask)]
            def keep(u, v, keepb=keepb, w=w, h=h, gw=gw, B=B):
                return keepb[(min(int(v*h), h-1)//B)*gw + min(int(u*w), w-1)//B]
    if valid and (uniform or MODE in ("ink", "glow")):
        cols_n = [0]*w; rows_n = [0]*h
        for y in range(h):
            for x in range(w):
                if mask[y*w + x]:
                    cols_n[x] += 1; rows_n[y] += 1
        xs = [x for x in range(w) if cols_n[x] >= 2]
        ys = [y for y in range(h) if rows_n[y] >= 2]
        if xs and ys:
            box = (max(min(xs)-2, 0), max(min(ys)-2, 0), min(max(xs)+3, w), min(max(ys)+3, h))
    fgp = [px[i] for i in range(w*h) if mask[i]] or px
    colorful = sum(max(p) - min(p) for p in fgp) / len(fgp) > 28
    bgl = lum(bg_at(0.5, 0.5))
    fgl = sum(lum(p) for p in fgp) / len(fgp)
    if MODE != "auto":
        mode = MODE
    elif not (uniform and valid):
        mode = "photo"
    elif colorful or fgl >= bgl:
        mode = "glow"
    else:
        mode = "ink"
    if mode == "photo":
        box = (0, 0, w, h)
    return dict(im=im, box=box, bg_at=bg_at, keep=keep, T=T, mode=mode, colorful=colorful, w=w, h=h, dist=dist)

def rows_for(a, cols, vscale=1.0):
    x0, y0, x1, y1 = a["box"]
    H = int(cols*2 * (y1-y0) / (x1-x0) * vscale); H += (-H) % 4
    return H // 4

# ---------- ছবি থেকে ডট (Braille) বানানো ----------
def render(a, cols, vscale=1.0):
    x0, y0, x1, y1 = a["box"]
    cw, ch = x1-x0, y1-y0
    W = cols*2; H = int(W*ch/cw*vscale); H += (-H) % 4
    img = a["im"].crop(a["box"]).resize((W, H), Image.LANCZOS)
    px = get_pixels(img)
    mode, w, h = a["mode"], a["w"], a["h"]
    fg_ = [True]*(W*H)
    strong = [True]*(W*H)
    tone = []
    if mode == "ink":
        norm = []
        for i, p in enumerate(px):
            xx, yy = i % W, i // W
            u = (x0 + (xx+.5)/W*cw) / w; v = (y0 + (yy+.5)/H*ch) / h
            bl = max(lum(a["bg_at"](u, v)), 1)
            L = min(255.0, lum(p) * 255 / bl)
            norm.append(255 if L > 0.81*255 else int(L / 0.81))
        li = Image.new("L", (W, H)); li.putdata(norm)
        bl_ = get_pixels(li.filter(ImageFilter.GaussianBlur(6)))
        for x, y in zip(norm, bl_):
            r = 255 if x >= 250 else min(255, int(x / (y + 1) * 140))
            tone.append(255 - r)
    elif mode == "glow":
        lums = []
        for i, p in enumerate(px):
            xx, yy = i % W, i // W
            u = (x0 + (xx+.5)/W*cw) / w; v = (y0 + (yy+.5)/H*ch) / h
            dd = a["dist"](p, a["bg_at"](u, v))
            fg_[i] = dd > a["T"] and a["keep"](u, v)
            strong[i] = fg_[i] and dd > 1.6 * a["T"]
            if fg_[i]:
                lums.append(lum(p))
        lo, hi = (min(lums), max(lums)) if lums else (0, 255)
        for i, p in enumerate(px):
            if fg_[i]:
                tone.append(int(255 * (0.85 + 0.15 * (lum(p) - lo) / max(hi - lo, 1))))
            else:
                tone.append(0)
    else:  # photo
        ls = sorted(lum(p) for p in px)
        lo, hi = ls[int(len(ls)*0.02)], ls[int(len(ls)*0.98)]
        for p in px:
            n = min(1.0, max(0.0, (lum(p) - lo) / max(hi - lo, 1)))
            tone.append(int(255 * n ** 0.8))     # ছোট সংখ্যা = বেশি ঘন ডট
    ti = Image.new("L", (W, H)); ti.putdata(tone)
    bw = get_pixels(ti.convert("1"))          # Floyd-Steinberg ডিথারিং
    rows = H // 4
    use_true = a["colorful"] and mode != "ink"
    shades = THEMES.get(THEME, THEMES["cyan"])
    grid = []
    for r in range(rows):
        row = []
        for c in range(cols):
            m = 0; sr = sg = sb = n = 0
            for dx, dy, bit in BITS:
                i = (r*4+dy)*W + c*2 + dx
                if bw[i]:
                    m |= bit
                if fg_[i] and strong[i]:
                    sr += px[i][0]; sg += px[i][1]; sb += px[i][2]; n += 1
            if mode == "glow" and n == 0:
                m = 0                      # কিনারার ফ্যাকাশে পিক্সেল বাদ
            elif mode == "glow" and a["colorful"] and n and \
                    max(sr, sg, sb)/n - min(sr, sg, sb)/n < 25 and (sr+sg+sb)/n/3 > 100:
                m = 0                      # রঙহীন ফ্যাকাশে কিনারা বাদ
            if not m:
                row.append((" ", None)); continue
            if use_true and n:
                col = [sr/n*BRIGHT, sg/n*BRIGHT, sb/n*BRIGHT]
                mx = max(col)
                if mx < 120:
                    f = 120 / max(mx, 1); col = [min(255, v*f) for v in col]
                col = tuple(min(255, int(v)) for v in col)
            else:
                col = xterm_rgb(shades[min(int(r/rows*len(shades)), len(shades)-1)])
            row.append((chr(0x2800 + m), col))
        grid.append(row)
    return grid

def frame_lines(grid, pad, shine=None, upto=None):
    out = []
    for r, row in enumerate(grid[:upto]):
        s, last = pad, None
        for c, (ch, col) in enumerate(row):
            if col is None:
                s += " "; continue
            if shine is not None:
                d = abs((c + r*0.9) - shine)
                if d < 5:
                    k = 1 + 0.55*(1 - d/5)
                    col = tuple(min(255, int(v*k + 40*(1 - d/5))) for v in col)
            if col != last:
                s += "\033[38;2;%d;%d;%dm" % col
                last = col
            s += ch
        out.append(s + C.RESET)
    return out

def moving_line(tw, anim):
    base = "═" * tw
    sys.stdout.write(C.GREEN + C.BOLD)
    if anim:
        for _ in range(3):
            for shift in range(0, tw, 2):
                sys.stdout.write("\r" + base[shift:] + base[:shift])
                sys.stdout.flush()
                time.sleep(0.01)
    sys.stdout.write("\r" + base + "\n" + C.RESET)

def cache_key(path, tw, th):
    st = os.stat(path)
    return repr((VERSION, path, st.st_mtime, st.st_size, tw, th, COLS, MODE, THEME, BRIGHT, FIT, LOOK, SQUEEZE, ROWS,
                 TITLE, SUBTITLE, STATUS))

def load_cache(key):
    try:
        with open(CACHE, "rb") as f:
            k, g, cols = pickle.load(f)
        if k == key:
            return g, cols
    except Exception:
        pass
    return None

def term_size():
    for f in (sys.stdout, sys.stdin, sys.stderr):   # env-এর LINES/COLUMNS এড়িয়ে আসল মাপ
        try:
            z = os.get_terminal_size(f.fileno())
            return z.columns, z.lines
        except Exception:
            pass
    return tuple(shutil.get_terminal_size())

def main(path):
    tw, th = term_size()
    if ROWS > 0:
        th = ROWS
    tty = sys.stdout.isatty()
    anim = ANIMATE and tty
    banner_lines = build_banner(tw)
    n = len(banner_lines)
    after = n + 5            # ছবির নিচের মোট লাইন (ব্যানার + ফাঁকা + চলন্ত লাইন)
    key = cache_key(path, tw, th)
    hit = load_cache(key)               # একই ছবি হলে দ্রুত খুলবে
    if hit:
        grid, cols = hit
    else:
        a = analyze(path)
        cols = tw - 1 if COLS <= 0 else min(COLS, tw - 1)
        vscale = 1.0
        if FIT and tty:
            # উপরে ১ + নিচে after + প্রম্পট/নিরাপত্তা ২ লাইন বাদ দিয়ে যতটা জায়গা থাকে
            max_rows = max(th - after - 3, 8)
            nat = rows_for(a, cols)
            if nat > max_rows:
                if LOOK == "keep":
                    while rows_for(a, cols) > max_rows and cols > 16:
                        cols -= 1
                else:
                    if LOOK == "wide":
                        vscale = min(1.0, max(SQUEEZE, max_rows / nat))
                    if rows_for(a, cols, vscale) > max_rows:
                        # এখনো লম্বা: উপর-নিচ থেকে একটু কেটে নেয় (মুখ থাকে উপরের দিকে)
                        x0, y0, x1, y1 = a["box"]
                        cw, ch = x1 - x0, y1 - y0
                        new_ch = (max_rows * 4) * cw / (cols * 2 * vscale)
                        if new_ch < ch:
                            ny0 = y0 + (ch - new_ch) * 0.35
                            a["box"] = (x0, int(ny0), x1, int(ny0 + new_ch))
        grid = render(a, cols, vscale)
        try:
            with open(CACHE, "wb") as f:
                pickle.dump((key, grid, cols), f)
        except Exception:
            pass
    total = len(grid)
    pad = " " * max((tw - cols)//2, 0)
    sweep_ok = (total + after + 3 <= th)    # পুরোটা স্ক্রিনে ধরলেই ঝিলিক চলবে
    if tty:
        os.system("clear")
    print()
    sys.stdout.write("\033[?25l" if anim else "")
    try:
        if anim:                                   # উপর থেকে নিচে ফুটে ওঠা
            for ln in frame_lines(grid, pad):
                print(ln); sys.stdout.flush(); time.sleep(0.015)
        else:
            for ln in frame_lines(grid, pad):
                print(ln)
        print()
        for ln in banner_lines:                    # ব্যানার একটা একটা লাইন করে ফুটবে
            print(ln)
            if anim:
                sys.stdout.flush(); time.sleep(0.06)
        print(); print()
        moving_line(tw, anim)
        print()
        if anim and sweep_ok:
            up = total + after
            span = cols + int(total*0.9) + 10
            for _ in range(SWEEPS):
                for s in range(-5, span, 4):       # আলোর ঝিলিক
                    sys.stdout.write("\033[%dA" % up)
                    for ln in frame_lines(grid, pad, s):
                        sys.stdout.write("\r" + ln + "\n")
                    sys.stdout.write("\033[%dB" % after)
                    sys.stdout.flush()
                    time.sleep(0.02)
            sys.stdout.write("\033[%dA" % up)
            for ln in frame_lines(grid, pad):
                sys.stdout.write("\r" + ln + "\n")
            sys.stdout.write("\033[%dB" % after)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()

if __name__ == "__main__":
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("image", nargs="?")
    ap.add_argument("--mode"); ap.add_argument("--theme"); ap.add_argument("--cols", type=int)
    ap.add_argument("--title"); ap.add_argument("--sub"); ap.add_argument("--status")
    ap.add_argument("--still", action="store_true")
    ap.add_argument("--nofit", action="store_true")
    ap.add_argument("--look"); ap.add_argument("--squeeze", type=float); ap.add_argument("--rows", type=int)
    ar, _ = ap.parse_known_args()
    if ar.mode: MODE = ar.mode
    if ar.theme: THEME = ar.theme
    if ar.cols: COLS = ar.cols
    if ar.title: TITLE = ar.title
    if ar.sub is not None: SUBTITLE = ar.sub
    if ar.status is not None: STATUS = ar.status
    if ar.still: ANIMATE = False
    if ar.nofit: FIT = False
    if ar.look: LOOK = ar.look
    if ar.squeeze: SQUEEZE = ar.squeeze
    if ar.rows: ROWS = ar.rows
    p = find_image(ar.image)
    if not p:
        print("ছবি পাওয়া যায়নি! ছবির নাম termux.jpg দিয়ে ~ বা /sdcard/Download তে রাখুন।")
    else:
        main(p)
