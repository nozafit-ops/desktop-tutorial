# 駅を実際の位置から、重ならない間隔まで押し広げる。隅田川と湾岸線も一緒に歪ませ、
# 駅が川・海の正しい側に残るようにする。結果を geo.json に書き出し、確認用の図を描く
import json, math, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from stations import RAW, W, H, proj
from PIL import Image, ImageDraw, ImageFont

RIVER_LL = [(35.803, 139.690), (35.7835, 139.723), (35.772, 139.742), (35.760, 139.762), (35.752, 139.780),
            (35.7405, 139.7975), (35.728, 139.8065), (35.713, 139.8015), (35.703, 139.7975), (35.693, 139.790),
            (35.683, 139.7925), (35.674, 139.789), (35.666, 139.781), (35.663, 139.776), (35.652, 139.770)]
COAST_LL = [(35.530, 139.742), (35.585, 139.744), (35.608, 139.747), (35.628, 139.757), (35.642, 139.764),
            (35.652, 139.770), (35.650, 139.790), (35.641, 139.812), (35.637, 139.838), (35.633, 139.862),
            (35.640, 139.910)]

def densify(pl, step=45.0):
    out = []
    for a, b in zip(pl, pl[1:]):
        n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
        for k in range(n): out.append([a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n])
    out.append(list(pl[-1]))
    return out

def nearest(pl, p):
    """折れ線上の最寄り点・距離・符号（左右）"""
    best = (1e9, None, 0)
    for a, b in zip(pl, pl[1:]):
        vx, vy = b[0] - a[0], b[1] - a[1]
        L = vx * vx + vy * vy or 1e-9
        t = max(0, min(1, ((p[0] - a[0]) * vx + (p[1] - a[1]) * vy) / L))
        q = (a[0] + vx * t, a[1] + vy * t)
        d = math.hypot(p[0] - q[0], p[1] - q[1])
        if d < best[0]:
            s = 1 if vx * (p[1] - a[1]) - vy * (p[0] - a[0]) > 0 else -1
            best = (d, q, s)
    return best

DMIN, GAP = 215, 100
kind = [k for *_, k in RAW]
# 中心（東京駅あたり）を広げる魚眼の逆変換。川・海岸も同じ変換なので左右関係は崩れない
C = (35.688, 139.775)
GAMMA = 0.72
def km(lat, lon): return ((lon - C[1]) * 90.4, (C[0] - lat) * 111.0)
def warp(lat, lon):
    x, y = km(lat, lon)
    r = math.hypot(x, y) or 1e-9
    k = r ** GAMMA / r
    return [x * k, y * k]
raw_pts = [warp(la, lo) for _, la, lo, _ in RAW]
raw_river = [warp(*p) for p in densify(RIVER_LL, 0.002)]
raw_coast = [warp(*p) for p in densify(COAST_LL, 0.002)]
# 盤面に収める（縦横それぞれ）
xs = [p[0] for p in raw_pts]; ys = [p[1] for p in raw_pts]
x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
fit = lambda p: [110 + (p[0] - x0) / (x1 - x0) * (W - 220), 100 + (p[1] - y0) / (y1 - y0) * (H - 200)]
pts = [fit(p) for p in raw_pts]
river = [fit(p) for p in raw_river]
coast = [fit(p) for p in raw_coast]
home = [p[:] for p in pts]
side_r = {i: nearest(river, pts[i])[2] for i in range(len(pts)) if kind[i] in "we"}
sw = side_r[0]
print("near-river side check:", [RAW[i][0] for i in side_r if nearest(river, pts[i])[0] < 400 and (side_r[i] == sw) != (kind[i] == "w")])
sea = nearest(coast, pts[[r[0] for r in RAW].index("お台場")])[2]
bad = [RAW[i][0] for i in side_r if (side_r[i] == sw) != (kind[i] == "w")]
print("wrong side after warp:", bad)

def relax(iters):
    for it in range(iters):
        mv = [[0, 0] for _ in pts]
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                dx, dy = pts[j][0] - pts[i][0], pts[j][1] - pts[i][1]
                d = math.hypot(dx, dy) or 0.01
                if d < DMIN:
                    f = (DMIN - d) / d * 0.2
                    mv[i][0] -= dx * f; mv[i][1] -= dy * f
                    mv[j][0] += dx * f; mv[j][1] += dy * f
        for i, p in enumerate(pts):
            mv[i][0] += (home[i][0] - p[0]) * 0.01
            mv[i][1] += (home[i][1] - p[1]) * 0.01
            L = math.hypot(*mv[i])
            if L > 4: mv[i][0] *= 4 / L; mv[i][1] *= 4 / L
            p[0] = min(W - 90, max(90, p[0] + mv[i][0])); p[1] = min(H - 90, max(90, p[1] + mv[i][1]))
        constrain()

def push(p, line, want, need):
    d, q, s = nearest(line, p)
    if s != want or d < need:
        ux, uy = (p[0] - q[0]), (p[1] - q[1])
        L = math.hypot(ux, uy) or 1
        if s != want: ux, uy = -ux, -uy
        p[0] = q[0] + ux / L * need; p[1] = q[1] + uy / L * need

def in_bay(p):
    poly = coast + [[coast[-1][0] + 3000, coast[-1][1]], [coast[-1][0] + 3000, 99999], [coast[0][0], 99999]]
    c = False
    for a, b in zip(poly, poly[1:] + poly[:1]):
        if (a[1] > p[1]) != (b[1] > p[1]) and p[0] < a[0] + (p[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1]):
            c = not c
    return c

def push_bay(p, island):
    d, q, s = nearest(coast, p)
    ok = in_bay(p) == island
    need = 170 if island else GAP
    if not ok or d < need:
        ux, uy = (p[0] - q[0]), (p[1] - q[1])
        L = math.hypot(ux, uy) or 1
        if not ok: ux, uy = -ux, -uy
        p[0] = q[0] + ux / L * need; p[1] = q[1] + uy / L * need

def constrain():
    for i, p in enumerate(pts):
        if kind[i] == "b":
            p[0], p[1] = nearest(river, p)[1]
            continue
        if kind[i] in "we" and nearest(river, p)[0] < 400: push(p, river, side_r[i], GAP)
        push_bay(p, kind[i] == "i")

relax(700)

out = {
    "stations": [[RAW[i][0], round(p[0], 1), round(p[1], 1), kind[i]] for i, p in enumerate(pts)],
    "river": [[round(x, 1), round(y, 1)] for x, y in river],
    "coast": [[round(x, 1), round(y, 1)] for x, y in coast],
}
json.dump(out, open(os.path.join(os.path.dirname(__file__), "geo.json"), "w"), ensure_ascii=False)
if __name__ == "__main__":
    im = Image.new("RGB", (W // 2, H // 2), "#EEE6D0")
    dr = ImageDraw.Draw(im)
    f = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 13)
    dr.polygon([(x / 2, y / 2) for x, y in coast] + [(W, H), (W, H)], fill="#9CC6D8")
    dr.line([(x / 2, y / 2) for x, y in river], fill="#6FA8C8", width=30)
    col = {"w": "#333", "e": "#1A5FB4", "i": "#C01C28", "b": "#8A6A00"}
    for i, (x, y) in enumerate(pts):
        x, y = x / 2, y / 2
        dr.ellipse([x - 7, y - 7, x + 7, y + 7], fill=col[kind[i]])
        dr.text((x - 20, y + 8), f"{i}{RAW[i][0]}", fill=col[kind[i]], font=f)
    im.save(sys.argv[1] if len(sys.argv) > 1 else "/tmp/relax.png")
    print("min dist", min(math.hypot(a[0]-b[0], a[1]-b[1]) for i, a in enumerate(pts) for b in pts[i+1:]))
