# 東京チェイスの盤面（スコットランドヤード東京を参考にした版）を組み立てる
#  - 駅の位置は geo.json（relax.py が作る。盤面いっぱい・区間はバラバラ）
#  - タクシー：道路。1駅から3〜4本、行き止まりなし。隅田川は橋の駅でしか渡れない
#  - バス：道路に沿って走り、1つおきに停まる（全体の4割ほどがバス停）
#  - 鉄道：外周環状線・センターサークルと、中心を貫く4路線。路線ごとに色分け
#  - 水上バス：隅田川と東京湾。島（お台場・羽田空港）へは水上バスかヘリだけ
# 出力: board.json（ゲームに埋め込む）と、引数があれば確認用の路線図 PNG
import json, math, os, sys
from collections import deque
import numpy as np
from scipy.spatial import Delaunay

HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)
from stations import W, H

geo = json.load(open(os.path.join(HERE, "geo.json")))
ST0 = geo["stations"]
RIVER, COAST = geo["river"], geo["coast"]

# 駅番号は読みやすいよう、上の帯から左→右の順に振り直す
BAND = 240
order = sorted(range(len(ST0)), key=lambda i: (int(ST0[i][2] // BAND), ST0[i][1]))
ST = [ST0[i] for i in order]
N = len(ST)
IDX = {s[0]: i for i, s in enumerate(ST)}
KIND = [s[3] for s in ST]
P = [(s[1], s[2]) for s in ST]
dist = lambda i, j: math.hypot(P[i][0] - P[j][0], P[i][1] - P[j][1])

def seg_cross(a, b, c, d):
    def o(p, q, r): return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    return o(a, b, c) * o(a, b, d) < 0 and o(c, d, a) * o(c, d, b) < 0
def crosses_river(a, b): return any(seg_cross(a, b, RIVER[k], RIVER[k + 1]) for k in range(len(RIVER) - 1))
def in_bay(p):
    poly = COAST + [[COAST[-1][0] + 3000, COAST[-1][1]], [COAST[-1][0] + 3000, 99999], [COAST[0][0], 99999]]
    c = False
    for a, b in zip(poly, poly[1:] + poly[:1]):
        if (a[1] > p[1]) != (b[1] > p[1]) and p[0] < a[0] + (p[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1]): c = not c
    return c
def wet(a, b): return any(in_bay((a[0] + (b[0] - a[0]) * t / 20, a[1] + (b[1] - a[1]) * t / 20)) for t in range(1, 20))

def bfs(adj, s):
    d = {s: 0}; q = deque([s])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if v not in d: d[v] = d[u] + 1; q.append(v)
    return d

# ======================================================================
# タクシー（道路）
# ======================================================================
land = [i for i in range(N) if KIND[i] != "i"]
tri = Delaunay(np.array([P[i] for i in land]))
cand = set()
for s in tri.simplices:
    for a in range(3):
        i, j = sorted((land[s[a]], land[s[(a + 1) % 3]]))
        cand.add((i, j))
def road_ok(i, j):
    if wet(P[i], P[j]) or dist(i, j) > 420: return False
    if KIND[i] == "b" or KIND[j] == "b": return dist(i, j) < 330
    return not crosses_river(P[i], P[j])
TAXI = {e for e in cand if road_ok(*e)}

def adj_of(edges):
    adj = {i: set() for i in range(N)}
    for a, b in edges: adj[a].add(b); adj[b].add(a)
    return adj
def angle_gap(adj, v, w):
    """v から w への道と、v のほかの道とのいちばん小さい角度"""
    g = math.pi
    for o in adj[v]:
        if o == w: continue
        u1 = (P[w][0] - P[v][0], P[w][1] - P[v][1]); u2 = (P[o][0] - P[v][0], P[o][1] - P[v][1])
        g = min(g, abs(math.atan2(u1[0] * u2[1] - u1[1] * u2[0], u1[0] * u2[0] + u1[1] * u2[1])))
    return g
# 狭い角度で並ぶ道・長い道から抜き、1駅3〜4本の街路にする（つながりは保つ）
adj = adj_of(TAXI)
LAND = set(land)
skip = set()
THIN_MIN = 3                                        # 道を抜くとき、これより少ない駅は残す
EXTRA = int(os.environ.get("THIN_EXTRA", "0"))      # そのあと、さらに抜く本数（行き止まりの少ない袋小路を作ってバランスを取る）
while True:
    best = None
    for a, b in TAXI:
        if (a, b) in skip or KIND[a] == "b" or KIND[b] == "b": continue
        if len(adj[a]) <= THIN_MIN or len(adj[b]) <= THIN_MIN: continue
        sc = -min(angle_gap(adj, a, b), angle_gap(adj, b, a)) * 300 + dist(a, b)
        if best is None or sc > best[0]: best = (sc, (a, b))
    if best is None: break
    a, b = best[1]
    adj[a].discard(b); adj[b].discard(a)
    if len(bfs(adj, land[0])) < len(LAND):
        adj[a].add(b); adj[b].add(a); skip.add((a, b))
        continue
    TAXI.discard((a, b))
# 追加の間引き：3本の駅を2本にしてよい。長い道・角度の狭い道から EXTRA 本
removed = 0
skip = set()
while removed < EXTRA:
    best = None
    for a, b in TAXI:
        if (a, b) in skip or KIND[a] == "b" or KIND[b] == "b": continue
        if len(adj[a]) <= 2 or len(adj[b]) <= 2: continue
        sc = -min(angle_gap(adj, a, b), angle_gap(adj, b, a)) * 300 + dist(a, b)
        if best is None or sc > best[0]: best = (sc, (a, b))
    if best is None: break
    a, b = best[1]
    adj[a].discard(b); adj[b].discard(a)
    if len(bfs(adj, land[0])) < len(LAND):
        adj[a].add(b); adj[b].add(a); skip.add((a, b)); continue
    TAXI.discard((a, b)); removed += 1
# 行き止まりを作らない：道が1本しかない駅には、近い候補から道を足す
for v in land:
    for e in sorted((e for e in cand if v in e and e not in TAXI and road_ok(*e)), key=lambda e: dist(*e)):
        if len(adj[v]) >= 2: break
        TAXI.add(e); adj[e[0]].add(e[1]); adj[e[1]].add(e[0])
    # それでも足りなければ、少し遠い駅まで（ほかの道と交差しない道だけ）
    for j in sorted((j for j in land if j != v), key=lambda j: dist(v, j)):
        if len(adj[v]) >= 2 or dist(v, j) > 600: break
        e = (min(v, j), max(v, j))
        if e in TAXI or wet(P[v], P[j]) or (KIND[j] != "b" and crosses_river(P[v], P[j])): continue
        if any(seg_cross(P[v], P[j], P[a], P[b]) for a, b in TAXI if len({a, b, v, j}) == 4): continue
        TAXI.add(e); adj[v].add(j); adj[j].add(v)
TAXI = sorted(TAXI)

# 道路を「まっすぐ抜ける」組み合わせでつないだ長い道（曲線で描く単位）
def chains(edge_list):
    inc = {}
    for e in edge_list:
        for v in e: inc.setdefault(v, []).append(e)
    pair = {}
    for v, es in inc.items():
        cands = []
        for x in range(len(es)):
            for y in range(x + 1, len(es)):
                a_ = es[x][0] if es[x][1] == v else es[x][1]
                b_ = es[y][0] if es[y][1] == v else es[y][1]
                u1 = (P[a_][0] - P[v][0], P[a_][1] - P[v][1]); u2 = (P[b_][0] - P[v][0], P[b_][1] - P[v][1])
                cos = (u1[0] * u2[0] + u1[1] * u2[1]) / (math.hypot(*u1) * math.hypot(*u2))
                if cos < -0.5: cands.append((cos, es[x], es[y]))
        used = set()
        for cos, e1, e2 in sorted(cands):
            if e1 in used or e2 in used: continue
            used |= {e1, e2}; pair[(v, e1)] = e2; pair[(v, e2)] = e1
    left, out = set(edge_list), []
    for e in sorted(edge_list, key=lambda e: -dist(*e)):
        if e not in left: continue
        left.discard(e)
        seq = [e[0], e[1]]
        for end in (1, 0):
            cur = e
            while True:
                v = seq[-1] if end == 1 else seq[0]
                nx = pair.get((v, cur))
                if not nx or nx not in left: break
                left.discard(nx)
                w = nx[0] if nx[1] == v else nx[1]
                if end == 1: seq.append(w)
                else: seq.insert(0, w)
                cur = nx
        out.append(seq)
    return out
ROADS = chains(TAXI)

# ======================================================================
# ここから「スコットランドヤード」式：バスと地下鉄は路線ではなく網（ネットワーク）
#  - バス停：全体の約4割。互いにほどよく離れた駅（道の多い駅を優先）。バス停どうしを直線で結ぶ
#  - 地下鉄駅：約15駅。バス停の中からさらに離れた駅。長い距離を一気に移動
#  - 水上バス：隅田川と湾。怪盗Xだけが黒チケットで乗れる（刑事は乗れない）
# ======================================================================
import random
rng = random.Random(int(os.environ.get("SEED", "5")))
tdeg = {i: len(adj[i]) for i in range(N)}
LANDP = [i for i in land if KIND[i] != "b"]

def spread_pick(cands, radius, prefer, must=()):
    """半径 radius 以上離れるように駅を選ぶ（prefer が大きい駅から）"""
    out = list(must)
    order_ = sorted(cands, key=lambda i: -prefer(i))
    for i in order_:
        if i in out: continue
        if all(dist(i, j) >= radius for j in out): out.append(i)
    return out

def net_edges(nodes, maxlen, maxdeg, allow_river=False, planar_with=()):
    """選んだ駅どうしの三角形分割から、短めの辺を採る（角度の狭い辺は捨てる）"""
    pts = np.array([P[i] for i in nodes])
    t = Delaunay(pts)
    cand_ = set()
    for s in t.simplices:
        for k in range(3):
            a, b = sorted((nodes[s[k]], nodes[s[(k + 1) % 3]]))
            cand_.add((a, b))
    out = []
    deg = {i: 0 for i in nodes}
    for a, b in sorted(cand_, key=lambda e: dist(*e)):
        if dist(a, b) > maxlen or wet(P[a], P[b]): continue
        if not allow_river and KIND[a] != "b" and KIND[b] != "b" and crosses_river(P[a], P[b]): continue
        if deg[a] >= maxdeg or deg[b] >= maxdeg: continue
        out.append((a, b)); deg[a] += 1; deg[b] += 1
    # 孤立したバス停・駅は最寄りとつなぐ
    for i in nodes:
        if deg[i] == 0:
            j = min((j for j in nodes if j != i and not wet(P[i], P[j])), key=lambda j: dist(i, j))
            out.append((min(i, j), max(i, j))); deg[i] += 1; deg[j] += 1
    return out

FAMOUS = {"新宿", "渋谷", "池袋", "東京", "上野", "品川", "銀座", "秋葉原", "押上", "錦糸町", "北千住", "新木場", "浅草", "六本木", "中野", "目黒"}
fame = lambda i: 30 if ST[i][0] in FAMOUS else 0
BUS_R = float(os.environ.get("BUS_R", "240"))
bridges = [i for i in range(N) if KIND[i] == "b"]
BUS_ST = spread_pick(LANDP, BUS_R, lambda i: tdeg[i] + rng.random() + fame(i), must=bridges)
BUS_E = net_edges(BUS_ST, BUS_R * 2.1, 4)

SUB_R = float(os.environ.get("SUB_R", "450"))
SUB_ST = spread_pick([i for i in BUS_ST if KIND[i] != "b"], SUB_R, lambda i: tdeg[i] + rng.random() + fame(i))
SUB_E = net_edges(SUB_ST, SUB_R * 1.9, 4, allow_river=True)

# 水上バス：隅田川沿いを下り、湾でお台場・羽田へ（怪盗Xが黒チケットで使う）
isl = [i for i in range(N) if KIND[i] == "i"]
odaiba, haneda = IDX["お台場"], IDX["羽田空港"]
rdist = lambda i: min(math.hypot(P[i][0] - x, P[i][1] - y) for x, y in RIVER)
rpos = lambda i: min(range(len(RIVER)), key=lambda k: math.hypot(P[i][0] - RIVER[k][0], P[i][1] - RIVER[k][1]))
river_side = sorted([i for i in LANDP if rdist(i) < 150], key=rpos)
piers = []
for i in river_side:
    if not piers or dist(i, piers[-1]) > 380: piers.append(i)
def near_bay(i): return any(in_bay((P[i][0] + dx, P[i][1] + dy)) for dx, dy in ((0, 180), (140, 140), (-140, 140), (180, 0)))
shore = [i for i in LANDP if near_bay(i) and i not in piers]
bayw = min((i for i in shore if P[i][0] < P[odaiba][0]), key=lambda i: dist(i, haneda))
baye = max(shore, key=lambda i: P[i][0])
BOAT_E = [(piers[k], piers[k + 1]) for k in range(len(piers) - 1)] + [(piers[-1], odaiba), (odaiba, bayw), (bayw, haneda), (odaiba, baye)]
BOAT_E = [tuple(sorted(e)) for e in BOAT_E]

HELI = [odaiba, haneda]
while len(HELI) < 8:
    HELI.append(max(LANDP, key=lambda i: min(dist(i, h) for h in HELI)))

# ======================================================================
# 検証と書き出し
# ======================================================================
edges = {}
def add(a, b, t):
    edges.setdefault((min(a, b), max(a, b)), set()).add(t)
for a, b in TAXI: add(a, b, "taxi")
for a, b in BUS_E: add(a, b, "bus")
for a, b in SUB_E: add(a, b, "tube")
for a, b in BOAT_E: add(a, b, "boat")
ADJ = adj_of(edges.keys())
report = {
    "stations": N, "connected": len(bfs(ADJ, 0)) == N,
    "taxi edges / avg deg": (len(TAXI), round(2 * len(TAXI) / len(land), 2)),
    "bus stops / edges": (len(BUS_ST), len(BUS_E)), "subway stations / edges": (len(SUB_ST), len(SUB_E)),
    "subway": [ST[i][0] for i in SUB_ST],
    "boat piers": [ST[i][0] for i in sorted({v for e in BOAT_E for v in e})],
    "heli": [ST[i][0] for i in HELI],
}
for k, v in report.items(): print(f"{k}: {v}")
board = {
    "W": W, "H": H, "style": "scotland-yard",
    "stations": [[s[0], s[1], s[2]] for s in ST],
    "taxi": [list(e) for e in TAXI], "busEdges": [list(e) for e in BUS_E], "subwayEdges": [list(e) for e in SUB_E],
    "boatEdges": [list(e) for e in BOAT_E],
    "heli": HELI, "islands": isl, "bridges": bridges, "river": RIVER, "coast": COAST,
}
json.dump(board, open(os.path.join(HERE, "board_sy.json"), "w"), ensure_ascii=False)

if len(sys.argv) > 1:
    from PIL import Image, ImageDraw, ImageFont
    K = 0.75
    im = Image.new("RGB", (int(W * K), int(H * K)), "#EFE8D6")
    dr = ImageDraw.Draw(im)
    f = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 19)
    fb = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 24)
    sc = lambda p: (p[0] * K, p[1] * K)
    dr.polygon([sc(p) for p in COAST] + [(COAST[-1][0] * K + 2000, H), (COAST[0][0] * K, H)], fill="#A9CFE0")
    rw = 50 * K
    pts = [sc(p) for p in RIVER]
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        n_ = max(1, int(math.hypot(x2 - x1, y2 - y1) / 6))
        for k in range(n_ + 1):
            x, y = x1 + (x2 - x1) * k / n_, y1 + (y2 - y1) * k / n_
            dr.ellipse([x - rw, y - rw, x + rw, y + rw], fill="#8DBBD4")
    def lines(E, col, w, off=0.0):
        for a, b in E:
            (x1, y1), (x2, y2) = sc(P[a]), sc(P[b])
            L_ = math.hypot(x2 - x1, y2 - y1) or 1
            nx, ny = -(y2 - y1) / L_ * off, (x2 - x1) / L_ * off
            dr.line([(x1 + nx, y1 + ny), (x2 + nx, y2 + ny)], fill=col, width=w)
    for a, b in BOAT_E:   # 水上バスは破線
        (x1, y1), (x2, y2) = sc(P[a]), sc(P[b])
        n_ = int(math.hypot(x2 - x1, y2 - y1) / 12)
        for k in range(0, n_, 2):
            dr.line([(x1 + (x2 - x1) * k / n_, y1 + (y2 - y1) * k / n_), (x1 + (x2 - x1) * (k + 1) / n_, y1 + (y2 - y1) * (k + 1) / n_)], fill="#1F4E79", width=5)
    lines(TAXI, "#D9A400", 9); lines(TAXI, "#F7C948", 6)
    lines(BUS_E, "#0E6B3A", 11, 6); lines(BUS_E, "#20A35A", 7, 6)
    lines(SUB_E, "#7A1510", 13, -7); lines(SUB_E, "#E03A30", 9, -7)
    bus_set, sub_set = set(BUS_ST), set(SUB_ST)
    for i, (x, y) in enumerate(P):
        x, y = x * K, y * K
        R = 17
        if i in HELI: dr.ellipse([x - R - 8, y - R - 8, x + R + 8, y + R + 8], outline="#7C3AED", width=4)
        if KIND[i] == "b": dr.polygon([(x, y - R - 6), (x + R + 6, y), (x, y + R + 6), (x - R - 6, y)], fill="#CDB98C", outline="#3B2C1E")
        # スコットランドヤード風の駅：上半分を使える乗り物で塗り分け
        dr.ellipse([x - R, y - R, x + R, y + R], fill="#FFFFFF", outline="#222", width=2)
        cols = ["#F7C948"] + (["#20A35A"] if i in bus_set else []) + (["#E03A30"] if i in sub_set else [])
        for k, c in enumerate(cols):
            a0 = 180 + 180 * k / len(cols); a1 = 180 + 180 * (k + 1) / len(cols)
            dr.pieslice([x - R, y - R, x + R, y + R], a0, a1, fill=c)
        dr.line([(x - R, y), (x + R, y)], fill="#222", width=2)
        dr.ellipse([x - R, y - R, x + R, y + R], outline="#222", width=2)
        dr.text((x, y + 8), str(i + 1), fill="#111", font=ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 14), anchor="mm")
        dr.text((x, y + R + 2), ST[i][0], fill="#111", font=f, anchor="ma", stroke_width=3, stroke_fill="#FFFFFF")
    items = [("タクシー", "#F7C948"), ("バス", "#20A35A"), ("地下鉄", "#E03A30"), ("水上バス（怪盗Xのみ・黒チケット）", "#1F4E79")]
    lx, ly = W * K - 430, H * K - 30 - 32 * len(items)
    dr.rectangle([lx - 14, ly - 14, lx + 410, ly + 32 * len(items) + 4], fill="#FFFFFF", outline="#3B2C1E")
    for k, (name, col) in enumerate(items):
        dr.line([(lx, ly + k * 32 + 13), (lx + 50, ly + k * 32 + 13)], fill=col, width=10)
        dr.text((lx + 62, ly + k * 32), name, fill="#1A140C", font=fb)
    im.save(sys.argv[1])
