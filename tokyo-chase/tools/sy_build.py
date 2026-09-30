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
# 盤面をさらに横長に：x を SX 倍に伸ばす。川は太く描くので、川に近すぎる駅は川から RIVER_CLEAR まで離す
SX = float(os.environ.get("SX", "1.3"))
RIVER_CLEAR = float(os.environ.get("RIVER_CLEAR", "135"))
W = W * SX
ST0 = [[s[0], s[1] * SX, s[2], s[3]] for s in geo["stations"]]
RIVER = [[x * SX, y] for x, y in geo["river"]]
COAST = [[x * SX, y] for x, y in geo["coast"]]
def _river_near(p):
    best = None
    for a, b in zip(RIVER, RIVER[1:]):
        vx, vy = b[0] - a[0], b[1] - a[1]; L = vx * vx + vy * vy or 1e-9
        t = max(0, min(1, ((p[0] - a[0]) * vx + (p[1] - a[1]) * vy) / L))
        q = (a[0] + vx * t, a[1] + vy * t); d = math.hypot(p[0] - q[0], p[1] - q[1])
        if best is None or d < best[0]: best = (d, q)
    return best
for st in ST0:
    if st[3] == "b": continue
    d, q = _river_near((st[1], st[2]))
    if d < RIVER_CLEAR:
        k = RIVER_CLEAR / max(d, 1e-6)
        st[1], st[2] = q[0] + (st[1] - q[0]) * k, q[1] + (st[2] - q[1]) * k

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
def seg_pt(a, b, p):
    vx, vy = b[0] - a[0], b[1] - a[1]
    L = vx * vx + vy * vy or 1e-9
    t = max(0, min(1, ((p[0] - a[0]) * vx + (p[1] - a[1]) * vy) / L))
    return math.hypot(p[0] - a[0] - vx * t, p[1] - a[1] - vy * t)
def clear(i, j, gap):
    """線が、止まらない駅のすぐそばを通らないこと（停車駅がまぎらわしくならないように）"""
    return all(seg_pt(P[i], P[j], P[k]) >= gap for k in range(N) if k != i and k != j)
def road_ok(i, j):
    if wet(P[i], P[j]) or dist(i, j) > 420 or not clear(i, j, 55): return False
    if KIND[i] == "b" or KIND[j] == "b": return False   # 橋は下でまとめてつなぐ
    return not crosses_river(P[i], P[j])
TAXI = {e for e in cand if road_ok(*e)}
# 橋：両岸それぞれいちばん近い駅とだけつなぐ（橋からの分岐は2本）
BRIDGE_NB = {}
for bi in [i for i in range(N) if KIND[i] == "b"]:
    nb = []
    for side in "we":
        j = min((k for k in range(N) if KIND[k] == side and not wet(P[bi], P[k]) and clear(bi, k, 55)), key=lambda k: dist(bi, k))
        nb.append(j); TAXI.add((min(bi, j), max(bi, j)))
    BRIDGE_NB[bi] = nb

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
    if KIND[v] == "b": continue
    for e in sorted((e for e in cand if v in e and e not in TAXI and road_ok(*e)), key=lambda e: dist(*e)):
        if len(adj[v]) >= 2: break
        TAXI.add(e); adj[e[0]].add(e[1]); adj[e[1]].add(e[0])
    # それでも足りなければ、少し遠い駅まで（ほかの道と交差しない道だけ）
    for j in sorted((j for j in land if j != v and KIND[j] != "b"), key=lambda j: dist(v, j)):
        if len(adj[v]) >= 2 or dist(v, j) > 600: break
        e = (min(v, j), max(v, j))
        if e in TAXI or wet(P[v], P[j]) or crosses_river(P[v], P[j]) or not clear(v, j, 55): continue
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

def net_edges(nodes, maxlen, maxdeg, allow_river=False, gap=65, minang=28):
    """選んだ駅どうしを、短い順に直線で結ぶ網。止まらない駅のそばを通る線・ほかの線と交わる線は採らない"""
    nodes = [i for i in nodes if KIND[i] != "b"]
    def ok(a, b):
        if wet(P[a], P[b]) or not clear(a, b, gap): return False
        return allow_river or not crosses_river(P[a], P[b])
    pairs = sorted(((a, b) for x, a in enumerate(nodes) for b in nodes[x + 1:] if dist(a, b) <= maxlen), key=lambda e: dist(*e))
    out, deg = [], {i: 0 for i in nodes}
    def crosses_any(a, b):
        return any(seg_cross(P[a], P[b], P[c], P[d]) for c, d in out if len({a, b, c, d}) == 4)
    def narrow(a, b):
        """同じ駅から出るほかの線と角度が近すぎる（重なって見える）"""
        for v, w in ((a, b), (b, a)):
            for c, d in out:
                if v not in (c, d): continue
                o = d if c == v else c
                u1 = (P[w][0] - P[v][0], P[w][1] - P[v][1]); u2 = (P[o][0] - P[v][0], P[o][1] - P[v][1])
                if abs(math.degrees(math.atan2(u1[0] * u2[1] - u1[1] * u2[0], u1[0] * u2[0] + u1[1] * u2[1]))) < minang: return True
        return False
    for a, b in pairs:
        if deg[a] >= maxdeg or deg[b] >= maxdeg or not ok(a, b) or crosses_any(a, b) or narrow(a, b): continue
        out.append((a, b)); deg[a] += 1; deg[b] += 1
    # ばらばらの塊をつなぐ（いちばん近い組から）
    while True:
        adj_ = {i: set() for i in nodes}
        for a, b in out: adj_[a].add(b); adj_[b].add(a)
        comp = bfs(adj_, nodes[0])
        rest = [i for i in nodes if i not in comp]
        if not rest: break
        best = min(((a, b) for a in comp for b in rest if ok(a, b)), key=lambda e: dist(*e), default=None)
        if best is None: break
        out.append((min(best), max(best))); deg[best[0]] += 1; deg[best[1]] += 1
    return out

FAMOUS = {"新宿", "渋谷", "池袋", "東京", "上野", "品川", "銀座", "秋葉原", "押上", "錦糸町", "北千住", "新木場", "浅草", "六本木", "中野", "目黒"}
fame = lambda i: 30 if ST[i][0] in FAMOUS else 0
BUS_R = float(os.environ.get("BUS_R", "265"))
bridges = [i for i in range(N) if KIND[i] == "b"]
# 橋とその両岸の隣駅はバス停。バスは橋を「両岸の隣駅 → 橋 → 隣駅」と渡る（タクシーと同じ道）
must_bus = bridges + [j for nb in BRIDGE_NB.values() for j in nb]
BUS_ST = spread_pick(LANDP, BUS_R, lambda i: tdeg[i] + rng.random() + fame(i), must=must_bus)
BUS_E = net_edges(BUS_ST, BUS_R * 2.1, 4) + [(min(b, j), max(b, j)) for b, nb in BRIDGE_NB.items() for j in nb]

SUB_N = int(os.environ.get("SUB_N", "14"))
def subway_grow(target, lo=380, hi=850, gap=55, minang=35):
    """地下鉄：1駅から始め、はっきり見える直線でつながる遠めの駅を1つずつ足していく。最後に環を少し足す"""
    cands = [i for i in LANDP if KIND[i] != "b"]
    start = min((i for i in cands if ST[i][0] in FAMOUS), key=lambda i: dist(i, min(cands, key=lambda j: (P[j][0] - W / 2) ** 2 + (P[j][1] - H / 2.3) ** 2)))
    S, E, deg = [start], [], {start: 0}
    def good(a, c):
        if not (lo <= dist(a, c) <= hi) or wet(P[a], P[c]) or not clear(a, c, gap): return False
        if any(seg_cross(P[a], P[c], P[x], P[y]) for x, y in E if len({a, c, x, y}) == 4): return False
        for v, w in ((a, c), (c, a)):
            for x, y in E:
                if v not in (x, y): continue
                o = y if x == v else x
                u1 = (P[w][0] - P[v][0], P[w][1] - P[v][1]); u2 = (P[o][0] - P[v][0], P[o][1] - P[v][1])
                if abs(math.degrees(math.atan2(u1[0] * u2[1] - u1[1] * u2[0], u1[0] * u2[0] + u1[1] * u2[1]))) < minang: return False
        return True
    while len(S) < target:
        best = None
        for a in S:
            if deg[a] >= 4: continue
            for c in cands:
                if c in S or min(dist(c, x) for x in S) < lo or not good(a, c): continue
                sc_ = min(dist(c, x) for x in S) + fame(c) * 2 - dist(a, c) * 0.3
                if best is None or sc_ > best[0]: best = (sc_, a, c)
        if best is None: break
        _, a, c = best
        S.append(c); E.append((min(a, c), max(a, c))); deg[a] += 1; deg[c] = 1
    # 環：まだ結ばれていない地下鉄駅どうしで、はっきり見える組を短い順に少し足す
    extra = sorted(((x, y) for k, x in enumerate(S) for y in S[k + 1:] if (min(x, y), max(x, y)) not in E), key=lambda e: dist(*e))
    added = 0
    for x, y in extra:
        if added >= target // 3: break
        if deg[x] >= 4 or deg[y] >= 4 or not good(x, y): continue
        E.append((min(x, y), max(x, y))); deg[x] += 1; deg[y] += 1; added += 1
    return S, E
SUB_ST, SUB_E = subway_grow(SUB_N)

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
def boat_path(a, b):
    """桟橋 a→b の水上バスの航路。川沿いは川の中心線をたどり、湾はまっすぐ"""
    if rdist(a) < 160 and rdist(b) < 160:
        ka, kb = rpos(a), rpos(b)
        step = 1 if kb >= ka else -1
        return [list(P[a])] + [RIVER[k] for k in range(ka, kb + step, step)] + [list(P[b])]
    if rdist(a) < 160 or rdist(b) < 160:
        r_, o_ = (a, b) if rdist(a) < 160 else (b, a)
        kr = rpos(r_)
        path = [list(P[r_])] + [RIVER[k] for k in range(kr, len(RIVER))] + [list(P[o_])]
        return path if r_ == a else path[::-1]
    return [list(P[a]), list(P[b])]
BOAT_PATHS = [boat_path(a, b) for a, b in BOAT_E]

HELI = [odaiba, haneda]
while len(HELI) < 8:
    HELI.append(max(LANDP, key=lambda i: min(dist(i, h) for h in HELI)))
# 盤面の中央付近のヘリポートは置かない（端と島だけ）
HELI = [h for h in HELI if KIND[h] == "i" or not (abs(P[h][0] - W / 2) < W * 0.3 and abs(P[h][1] - H / 2) < H * 0.3)]

# 夢見島（98番）と材木浜（81番）のヘリポートは置かない
HELI = [h for h in HELI if h not in (97, 80)]

# お台場（夢見島）は大きな島にして、北東と西の岸からバスの橋を渡す（タクシーは渡れない）
def odaiba_bus(side):
    c = [i for i in LANDP if (P[i][0] > P[odaiba][0] + 100 if side == "e" else P[i][0] < P[odaiba][0] - 200) and P[i][1] < P[odaiba][1]]
    for j in sorted(c, key=lambda j: dist(odaiba, j)):
        if clear(odaiba, j, 90) and not any(seg_cross(P[odaiba], P[j], P[a], P[b]) for a, b in BUS_E if len({a, b, odaiba, j}) == 4):
            return (min(odaiba, j), max(odaiba, j))
ODAIBA_BUS = [odaiba_bus("e"), odaiba_bus("w")]
BUS_E += ODAIBA_BUS
ISLAND_SIZE = {odaiba: [230, 150], haneda: [124, 84]}

# ======================================================================
# モノレール：湾岸を走る高架の路線。島（夢見島・空港島）にも刑事が行ける。1駅ずつ停まる
#  広野 – 浜風通 – 夢見島 – 潮月町 – 汐風台 – 材木浜 – 岬町、夢見島 – 空港島（番号は盤面の駅番号−1）
# ======================================================================
MONO_LINES = [[99, 100, 93, 86, 90, 97, 76, 79, 80, 82], [97, 103]]   # 雲雀ヶ丘 – 小鳥台 – 黒松台 – 広野 – …
MONO_E = [tuple(sorted((l[k], l[k + 1]))) for l in MONO_LINES for k in range(len(l) - 1)]
# モノレールと同じ区間を走るバスはなくす（重なって見分けにくいので）
_mono = set(MONO_E)
BUS_DROPPED = [e for e in BUS_E if tuple(sorted(e)) in _mono]
BUS_E = [e for e in BUS_E if tuple(sorted(e)) not in _mono]
# 100番（雲雀ヶ丘）から87番（広野）までは、モノレールと重なるタクシーの道もなくす
_drop_taxi = {tuple(sorted(p)) for p in [(99, 100), (100, 93), (93, 86)]}
# 1–13（風見野–楓町）と 84–99（三つ茶屋–双子川）のタクシーもなくす（駅番号−1で指定）
_drop_taxi |= {tuple(sorted(p)) for p in [(0, 12), (83, 98)]}
TAXI = [e for e in TAXI if tuple(sorted(e)) not in _drop_taxi]

# ======================================================================
# 新港島：湾の南東に足した埋立地（駅番号 105〜110。既存の駅番号は変えない）
#  - 島の中はタクシーの環と十字、北側にバス
#  - 空港島からモノレールが延びる（空港島 → 星見浜 → 海風ヶ丘）
#  - 夢見島からバスの橋、岬町から水上バス、灯台岬にヘリポート
# ======================================================================
LANDS = [[3790, 1530, 560, 215]]   # 埋立地の楕円（中心 x, y, 半径 x, y）
NEW_ST = [("新港埠頭", 3380, 1520), ("白波台", 3640, 1415), ("灯台岬", 3940, 1430),
          ("潮騒ヶ浜", 4190, 1545), ("海風ヶ丘", 3910, 1645), ("星見浜", 3620, 1650)]
n0 = N
for name, x, y in NEW_ST:
    ST.append([name, x, y, "n"]); P.append((x, y)); KIND.append("n")
N = len(ST)
A_, B_, C_, D_, E_, F_ = range(n0, n0 + 6)
TAXI = sorted(set(TAXI) | {tuple(sorted(e)) for e in [(A_, B_), (B_, C_), (C_, D_), (D_, E_), (E_, F_), (F_, A_), (B_, F_), (C_, E_)]})
BUS_E += [tuple(sorted(e)) for e in [(A_, B_), (B_, C_), (C_, D_), (97, A_)]]   # 夢見島からバスの橋
MONO_LINES[1] = MONO_LINES[1] + [F_, E_]                                        # 夢見島 – 空港島 – 星見浜 – 海風ヶ丘
MONO_E = [tuple(sorted((l[k], l[k + 1]))) for l in MONO_LINES for k in range(len(l) - 1)]
BOAT_E.append(tuple(sorted((82, D_)))); BOAT_PATHS.append([list(P[min(82, D_)]), list(P[max(82, D_)])])   # 岬町 – 潮騒ヶ浜
HELI.append(C_)                                                                 # 灯台岬のヘリポート

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
for a, b in MONO_E: add(a, b, "mono")
ADJ = adj_of(edges.keys())
report = {
    "stations": N, "connected": len(bfs(ADJ, 0)) == N,
    "taxi edges / avg deg": (len(TAXI), round(2 * len(TAXI) / len(land), 2)),
    "bus stops / edges": (len(BUS_ST), len(BUS_E)), "subway stations / edges": (len(SUB_ST), len(SUB_E)),
    "subway": [ST[i][0] for i in SUB_ST],
    "boat piers": [ST[i][0] for i in sorted({v for e in BOAT_E for v in e})],
    "heli": [ST[i][0] for i in HELI],
    "bus dropped (monorail)": [(a + 1, b + 1) for a, b in BUS_DROPPED],
    "odaiba bus": [ST[j][0] for e in ODAIBA_BUS for j in e if j != odaiba],
}
for k, v in report.items(): print(f"{k}: {v}")
bdeg = {b: len({v for e in list(TAXI) + BUS_E + SUB_E + BOAT_E if b in e for v in e} - {b}) for b in bridges}
print("bridge branches:", {ST[b][0]: n for b, n in bdeg.items()})
board = {
    "W": W, "H": H, "style": "scotland-yard",
    "stations": [[s[0], s[1], s[2]] for s in ST],
    "taxi": [list(e) for e in TAXI], "busEdges": [list(e) for e in BUS_E], "subwayEdges": [list(e) for e in SUB_E],
    "boatEdges": [list(e) for e in BOAT_E], "monoEdges": [list(e) for e in MONO_E], "monoLines": MONO_LINES, "boatPaths": BOAT_PATHS,
    "heli": HELI, "lands": LANDS, "islands": isl, "islandSize": [ISLAND_SIZE[i] for i in isl], "bridges": bridges, "river": RIVER, "coast": COAST,
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
    for path in BOAT_PATHS:   # 水上バスは川に沿った破線
        pts_ = [sc(q) for q in path]
        acc = 0
        for (x1, y1), (x2, y2) in zip(pts_, pts_[1:]):
            L_ = math.hypot(x2 - x1, y2 - y1); n_ = max(1, int(L_ / 6))
            for k in range(n_):
                if int((acc + L_ * k / n_) / 12) % 2 == 0:
                    dr.line([(x1 + (x2 - x1) * k / n_, y1 + (y2 - y1) * k / n_), (x1 + (x2 - x1) * (k + 1) / n_, y1 + (y2 - y1) * (k + 1) / n_)], fill="#1F4E79", width=5)
            acc += L_
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
