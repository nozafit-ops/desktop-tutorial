# 東京チェイスの盤面を組み立てる（仮想の東京。実際の路線にはこだわらず、遊びやすさで設計する）
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
while True:
    best = None
    for a, b in TAXI:
        if (a, b) in skip or KIND[a] == "b" or KIND[b] == "b": continue
        if len(adj[a]) <= 3 or len(adj[b]) <= 3: continue
        sc = -min(angle_gap(adj, a, b), angle_gap(adj, b, a)) * 300 + dist(a, b)
        if best is None or sc > best[0]: best = (sc, (a, b))
    if best is None: break
    a, b = best[1]
    adj[a].discard(b); adj[b].discard(a)
    if len(bfs(adj, land[0])) < len(LAND):
        adj[a].add(b); adj[b].add(a); skip.add((a, b))
        continue
    TAXI.discard((a, b))
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
# バス：長い道から順に、1つおきに停まる路線にする（道の曲線に沿って走る）
# ======================================================================
BUSES = []
stops = set()
for r in sorted(ROADS, key=len, reverse=True):
    if len(r) < 4: continue
    best = max((r[k::2] for k in (0, 1)), key=lambda s: sum(1 for v in s if v not in stops))
    if len(best) < 2 or sum(1 for v in best if v not in stops) < 2: continue
    BUSES.append({"stops": best, "road": r[r.index(best[0]): r.index(best[-1]) + 1]})
    stops |= set(best)
    if len(stops) >= 0.36 * N or len(BUSES) >= 10: break

# ======================================================================
# 鉄道：外周環状線・センターサークル・中心を貫く4路線（仮想）
# ======================================================================
LANDP = [i for i in land if KIND[i] != "b"]
cx = sum(P[i][0] for i in LANDP) / len(LANDP); cy = sum(P[i][1] for i in LANDP) / len(LANDP)
CX, CY = cx - 120, cy - 60   # 都心（湾の分だけ左上に寄せる）
def ang(i): return math.atan2(P[i][1] - CY, P[i][0] - CX)
def pick_ring(score, n):
    """中心から見た角度で n 等分し、それぞれの方角で得点のいちばん高い駅を選ぶ"""
    out = []
    for k in range(n):
        a0 = -math.pi + 2 * math.pi * k / n
        sect = [i for i in score if (ang(i) - a0) % (2 * math.pi) < 2 * math.pi / n]
        if sect: out.append(max(sect, key=lambda i: score[i]))
    return sorted(set(out), key=ang)
# 外周：盤面の縁に近い駅。湾に面した駅も「外側」とみなす
edge_score = {i: -min(P[i][0], W - P[i][0], P[i][1], H - P[i][1]) for i in LANDP}
for i in LANDP:
    x, y = P[i]
    if in_bay((x, y + 160)) or in_bay((x + 120, y + 120)) or in_bay((x - 120, y + 120)): edge_score[i] = max(edge_score[i], -60)
# 縁（または湾岸）から近い駅を角度順に並べ、約380おきに拾って外周をなぞる
rim = sorted([i for i in LANDP if edge_score[i] > -230], key=ang)
start = max(rim, key=lambda i: -P[i][0] - P[i][1])   # 左上から
k0 = rim.index(start); rim = rim[k0:] + rim[:k0]
OUTER = [rim[0]]
for i in rim[1:]:
    if dist(i, OUTER[-1]) > 380 and dist(i, OUTER[0]) > 250: OUTER.append(i)
# センターサークル：都心から半径 R あたりの駅
R = 330
center_score = {i: -abs(math.hypot(P[i][0] - CX, P[i][1] - CY) - R) for i in LANDP}
CENTER = pick_ring(center_score, 7)
# 中心を貫く直線：直線に近い駅を約300おきに拾い、環状線の駅に寄せて乗換駅にする
def through_line(theta, shift):
    """都心を shift だけ横にずらした直線に沿う駅を約300おきに拾う。環状線の駅に寄せて乗換駅にする"""
    ux, uy = math.cos(theta), math.sin(theta)
    def along(i): return (P[i][0] - CX) * ux + (P[i][1] - CY) * uy
    def off(i): return -(P[i][0] - CX) * uy + (P[i][1] - CY) * ux - shift
    pts = sorted([i for i in LANDP if abs(off(i)) < 150], key=along)
    line, last = [], None
    for i in pts:
        if last is None or along(i) - along(last) > 300:
            line.append(i); last = i
    for k, i in enumerate(line):
        for ring in (CENTER, OUTER):
            j = min(ring, key=lambda r: dist(r, i))
            if dist(j, i) < 190 and j not in line: line[k] = j; break
    # 外周環状線の外へはみ出した端は切る
    while len(line) > 2 and line[0] not in OUTER and any(dist(line[1], o) < 10 for o in OUTER): line.pop(0)
    return line
# 路線は仮想。遊びやすさで手で決める（乗換駅を散らし、どの地域にも駅があるように）
def L(names): return [IDX[n] for n in names]
LINES = [
    ("外周環状線", "#7AC943", L(["練馬", "赤羽", "西新井", "綾瀬", "青砥", "小岩", "船堀", "葛西", "新木場", "越中島", "日の出",
                              "大森", "蒲田", "武蔵小山", "二子玉川", "方南町", "荻窪", "練馬"])),
    ("センターサークル", "#E4007F", L(["神楽坂", "後楽園", "御茶ノ水", "東京", "築地", "虎ノ門", "赤坂", "神楽坂"])),
    ("東西線", "#00A7DB", L(["荻窪", "中野坂上", "早稲田", "神楽坂", "御茶ノ水", "秋葉原", "錦糸町", "船堀"])),
    ("京葉線", "#C1272D", L(["下北沢", "原宿", "青山一丁目", "虎ノ門", "新橋", "月島", "豊洲", "葛西臨海公園", "葛西"])),
    ("銀座線", "#F39700", L(["赤羽", "池袋", "早稲田", "四ツ谷", "代々木", "表参道", "恵比寿", "目黒", "蒲田"])),
    ("半蔵門線", "#8F76D6", L(["西新井", "南千住", "浅草", "人形町", "門前仲町", "豊洲"])),
]
LINES = [(n, c, s) for n, c, s in LINES if len(s) >= 2]

# ======================================================================
# 水上バス・ヘリ
# ======================================================================
isl = [i for i in range(N) if KIND[i] == "i"]
odaiba, haneda = IDX["お台場"], IDX["羽田空港"]
rdist = lambda i: min(math.hypot(P[i][0] - x, P[i][1] - y) for x, y in RIVER)
def near_bay(i): return any(in_bay((P[i][0] + dx, P[i][1] + dy)) for dx, dy in ((0, 180), (140, 140), (-140, 140), (180, 0)))
up = sorted([i for i in LANDP if rdist(i) < 170],
            key=lambda i: min(range(len(RIVER)), key=lambda k: math.hypot(P[i][0] - RIVER[k][0], P[i][1] - RIVER[k][1])))
river_line = []
for i in up[len(up) // 3:]:
    if not river_line or dist(i, river_line[-1]) > 330: river_line.append(i)
river_line = river_line[-3:]
shore = [i for i in LANDP if near_bay(i) and i not in river_line]
bayw = min((i for i in shore if P[i][0] < P[odaiba][0]), key=lambda i: dist(i, haneda))
baye = max(shore, key=lambda i: P[i][0])
BOATS = [("隅田川ライン", river_line + [odaiba, bayw, haneda]), ("臨海ライン", [baye, odaiba])]
# ヘリ：ほかのヘリポートから遠い駅を順に選ぶ（島は必ず入れる）
HELI = [odaiba, haneda]
while len(HELI) < 8:
    HELI.append(max(LANDP, key=lambda i: min(dist(i, h) for h in HELI)))

# ======================================================================
# 検証と書き出し
# ======================================================================
edges = {}
def add(a, b, t, name):
    edges.setdefault((min(a, b), max(a, b)), {}).setdefault(t, set()).add(name)
for a, b in TAXI: add(a, b, "taxi", "タクシー")
for k, bus in enumerate(BUSES):
    for a, b in zip(bus["stops"], bus["stops"][1:]): add(a, b, "bus", f"バス {k + 1}番")
for name, col, seq in LINES:
    for a, b in zip(seq, seq[1:]): add(a, b, "tube", name)
for name, seq in BOATS:
    for a, b in zip(seq, seq[1:]): add(a, b, "boat", name)
ADJ = adj_of(edges.keys())
tadj = adj_of(TAXI)
tube_st = {i for _, _, s in LINES for i in s}
report = {
    "stations": N, "connected": len(bfs(ADJ, 0)) == N,
    "taxi edges": len(TAXI),
    "taxi degree min/avg/max": (min(len(tadj[i]) for i in land), round(2 * len(TAXI) / len(land), 2), max(len(tadj[i]) for i in land)),
    "bus routes": len(BUSES), "bus stops": len(stops), "rail stations": len(tube_st),
    "rail lines": [(n, [ST[i][0] for i in s]) for n, _, s in LINES],
    "boat": [(n, [ST[i][0] for i in s]) for n, s in BOATS],
    "heli": [ST[i][0] for i in HELI],
}
for k, v in report.items(): print(f"{k}: {v}")

board = {
    "W": W, "H": H,
    "stations": [[s[0], s[1], s[2]] for s in ST],
    "taxi": [list(e) for e in TAXI],
    "roads": ROADS,
    "bus": [b["stops"] for b in BUSES], "busRoads": [b["road"] for b in BUSES],
    "tube": [[n, c, s] for n, c, s in LINES],
    "boat": [[n, s] for n, s in BOATS],
    "heli": HELI, "islands": isl,
    "bridges": [i for i in range(N) if KIND[i] == "b"],
    "river": RIVER, "coast": COAST,
}
json.dump(board, open(os.path.join(HERE, "board.json"), "w"), ensure_ascii=False)

def catmull(pts, closed=False, steps=12):
    if closed and pts[0] == pts[-1]: pts = pts[:-1]
    n = len(pts); out = []
    for i in (range(n) if closed else range(n - 1)):
        p0 = pts[(i - 1) % n] if closed else pts[max(0, i - 1)]
        p1, p2 = pts[i], pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if closed else pts[min(n - 1, i + 2)]
        for k in range(steps):
            t = k / steps; t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 +
                                   (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in range(2)))
    out.append(tuple(pts[0] if closed else pts[-1]))
    return out

if len(sys.argv) > 1:
    from PIL import Image, ImageDraw, ImageFont
    K = 0.75
    im = Image.new("RGB", (int(W * K), int(H * K)), "#EFE6CF")
    dr = ImageDraw.Draw(im)
    f = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 19)
    fb = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 24)
    sc = lambda p: (p[0] * K, p[1] * K)
    dr.polygon([sc(p) for p in COAST] + [(COAST[-1][0] * K + 2000, H), (COAST[0][0] * K, H)], fill="#A9CFE0")
    rw = 55 * K
    for x, y in catmull([sc(p) for p in RIVER[::3]] + [sc(RIVER[-1])], steps=20):
        dr.ellipse([x - rw, y - rw, x + rw, y + rw], fill="#8DBBD4")
    for r in ROADS: dr.line(catmull([sc(P[i]) for i in r]), fill="#9A968C", width=int(30 * K), joint="curve")
    for r in ROADS: dr.line(catmull([sc(P[i]) for i in r]), fill="#FFFFFF", width=int(20 * K), joint="curve")
    for b in BUSES: dr.line(catmull([sc(P[i]) for i in b["road"]]), fill="#16935B", width=int(5 * K), joint="curve")
    for name, seq in BOATS: dr.line([sc(P[i]) for i in seq], fill="#2F7FB0", width=int(6 * K))
    for name, col, seq in LINES:
        pts = [sc(P[i]) for i in seq]
        dr.line(pts, fill="#222222", width=int(17 * K), joint="curve")
        dr.line(pts, fill=col, width=int(12 * K), joint="curve")
    for i, (x, y) in enumerate(P):
        x, y = x * K, y * K
        if i in HELI: dr.ellipse([x - 22, y - 22, x + 22, y + 22], outline="#7C3AED", width=4)
        if KIND[i] == "b": dr.polygon([(x, y - 19), (x + 19, y), (x, y + 19), (x - 19, y)], fill="#CDB98C", outline="#3B2C1E")
        fill = "#333333" if i in tube_st else "#BFE3C9" if i in stops else "#FFFFFF"
        dr.ellipse([x - 17, y - 13, x + 17, y + 13], fill=fill, outline="#3B2C1E", width=2)
        dr.text((x, y), str(i + 1), fill="#FFFFFF" if i in tube_st else "#1A140C", font=f, anchor="mm")
        dr.text((x, y + 15), ST[i][0], fill="#1A140C", font=f, anchor="ma", stroke_width=3, stroke_fill="#FFFFFF")
    lx, ly = 24, 24
    dr.rectangle([lx - 10, ly - 10, lx + 250, ly + 30 * len(LINES) + 4], fill="#FFFFFF", outline="#3B2C1E")
    for k, (name, col, seq) in enumerate(LINES):
        dr.line([(lx, ly + k * 30 + 13), (lx + 50, ly + k * 30 + 13)], fill=col, width=11)
        dr.text((lx + 62, ly + k * 30), name, fill="#1A140C", font=fb)
    im.save(sys.argv[1])
