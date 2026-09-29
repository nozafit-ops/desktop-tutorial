# 路線データを組み立てる：タクシー（近い駅どうし・川と海を越えない）、電車、バス、水上バス、ヘリ
# 出力: board.json（ゲームに埋め込む）と、確認用の路線図 PNG
import json, math, os, sys
from collections import deque
import numpy as np
from scipy.spatial import Delaunay

HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)
from stations import W, H

geo = json.load(open(os.path.join(HERE, "geo.json")))
ST = geo["stations"]
RIVER, COAST = geo["river"], geo["coast"]
N = len(ST)
IDX = {s[0]: i for i, s in enumerate(ST)}
KIND = [s[3] for s in ST]
P = [(s[1], s[2]) for s in ST]
ix = lambda names: [IDX[n] for n in names]

TRAINS = [
    # 盤面の外側をぐるりと回る鉄道
    ("外周環状線", ["練馬", "赤羽", "王子", "西新井", "綾瀬", "青砥", "小岩", "船堀", "葛西", "葛西臨海公園", "新木場", "豊洲",
                "月島", "日の出", "天王洲アイル", "大森", "蒲田", "二子玉川", "下北沢", "荻窪", "練馬"]),
    # 環状線：まわりを囲む山手線と、皇居のまわりの小さなセンターサークル
    ("山手線", ["東京", "上野", "日暮里", "巣鴨", "池袋", "高田馬場", "新宿", "原宿", "渋谷", "目黒", "品川", "浜松町", "東京"]),
    ("センターサークル", ["東京", "神保町", "飯田橋", "四ツ谷", "赤坂", "虎ノ門", "銀座", "東京"]),
    ("中央・総武線", ["荻窪", "中野", "新宿", "四ツ谷", "御茶ノ水", "秋葉原", "両国", "錦糸町", "新小岩", "小岩"]),
    ("京浜東北線", ["赤羽", "王子", "上野", "東京", "品川", "大井町", "蒲田"]),
    # 東側（隅田川の向こう）の路線
    ("東西線", ["日本橋", "門前仲町", "東陽町", "葛西"]),
    ("半蔵門線", ["神保町", "清澄白河", "住吉", "押上"]),
    ("常磐線", ["上野", "日暮里", "北千住", "綾瀬"]),
]
BUSES = [
    ["赤羽", "王子", "田端", "日暮里", "町屋", "南千住", "千住大橋", "北千住", "西新井"],
    ["練馬", "江古田", "池袋", "茗荷谷", "後楽園", "本郷三丁目", "上野", "浅草"],
    ["浅草", "言問橋", "押上", "曳舟", "堀切", "青砥"],
    ["秋葉原", "浅草橋", "両国橋", "両国", "錦糸町", "亀戸", "平井", "新小岩"],
    ["荻窪", "高円寺", "中野", "中野坂上", "新宿", "四ツ谷", "市ヶ谷", "飯田橋", "神保町"],
    ["方南町", "笹塚", "初台", "代々木", "原宿", "表参道", "青山一丁目", "赤坂", "永田町"],
    ["下北沢", "代々木上原", "渋谷", "恵比寿", "広尾", "麻布十番", "浜松町", "日の出"],
    ["二子玉川", "自由が丘", "学芸大学", "中目黒", "目黒", "五反田", "品川", "天王洲アイル"],
    ["蒲田", "大森", "大井町", "品川", "田町", "浜松町", "新橋", "銀座", "築地", "勝鬨橋", "月島", "豊洲"],
    ["東京", "日本橋", "人形町", "清洲橋", "清澄白河", "門前仲町", "東陽町", "南砂町", "葛西", "葛西臨海公園"],
    ["高田馬場", "早稲田", "神楽坂", "飯田橋"],
    ["錦糸町", "住吉", "東陽町", "豊洲", "新木場", "葛西臨海公園"],
    ["綾瀬", "堀切", "曳舟", "押上", "錦糸町"],
    ["六本木", "麻布十番", "田町", "天王洲アイル"],
]
BOATS = [
    ("隅田川ライン", ["浅草", "両国", "越中島", "日の出", "お台場", "天王洲アイル", "羽田空港"]),
    ("臨海ライン", ["葛西臨海公園", "お台場"]),
]
HELI = ["赤羽", "荻窪", "新宿", "六本木", "押上", "葛西臨海公園", "お台場", "羽田空港"]

def seg_cross(a, b, c, d):
    def o(p, q, r): return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    return o(a, b, c) * o(a, b, d) < 0 and o(c, d, a) * o(c, d, b) < 0

def crosses_river(a, b):
    return any(seg_cross(a, b, RIVER[k], RIVER[k + 1]) for k in range(len(RIVER) - 1))

def in_bay(p):
    poly = COAST + [[COAST[-1][0] + 3000, COAST[-1][1]], [COAST[-1][0] + 3000, 99999], [COAST[0][0], 99999]]
    c = False
    for a, b in zip(poly, poly[1:] + poly[:1]):
        if (a[1] > p[1]) != (b[1] > p[1]) and p[0] < a[0] + (p[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1]):
            c = not c
    return c

def wet(a, b):
    return any(in_bay((a[0] + (b[0] - a[0]) * t / 20, a[1] + (b[1] - a[1]) * t / 20)) for t in range(1, 20))

dist = lambda i, j: math.hypot(P[i][0] - P[j][0], P[i][1] - P[j][1])

# タクシー：陸の駅の三角形分割から、短い辺だけ。川は橋の駅でしか渡れない
land = [i for i in range(N) if KIND[i] != "i"]
tri = Delaunay(np.array([P[i] for i in land]))
cand = set()
for s in tri.simplices:
    for a in range(3):
        i, j = sorted((land[s[a]], land[s[(a + 1) % 3]]))
        cand.add((i, j))
TAXI = []
for i, j in sorted(cand):
    d = dist(i, j)
    if d > 330: continue
    if wet(P[i], P[j]): continue
    br = KIND[i] == "b" or KIND[j] == "b"
    if br:
        # 橋の駅は、川の両岸それぞれいちばん近い駅（数駅）とだけつなぐ
        if d > 300: continue
    elif crosses_river(P[i], P[j]):
        continue
    TAXI.append((i, j))
# 橋の駅：両岸に最低1本ずつつながるように補う
for b in [i for i in range(N) if KIND[i] == "b"]:
    for side in "we":
        if not any((b in e) and KIND[e[0] if e[1] == b else e[1]] == side for e in TAXI):
            j = min((k for k in range(N) if KIND[k] == side), key=lambda k: dist(b, k))
            TAXI.append(tuple(sorted((b, j))))

def thin(edge_list, target=4):
    adj = {}
    for a, b in edge_list: adj.setdefault(a, set()).add(b); adj.setdefault(b, set()).add(a)
    def conn():
        start = next(iter(adj)); seen = {start}; q = deque([start])
        while q:
            u = q.popleft()
            for v in adj[u]:
                if v not in seen: seen.add(v); q.append(v)
        return len(seen) == len(adj)
    # 長い辺・ほかの辺と角度が近い辺から抜く
    def score(e):
        a, b = e
        ang = []
        for v, w in ((a, b), (b, a)):
            for o in adj[v]:
                if o == w: continue
                u1 = (P[w][0] - P[v][0], P[w][1] - P[v][1]); u2 = (P[o][0] - P[v][0], P[o][1] - P[v][1])
                ang.append(abs(math.atan2(u1[0] * u2[1] - u1[1] * u2[0], u1[0] * u2[0] + u1[1] * u2[1])))
        return -min(ang) * 200 + dist(a, b)
    out = list(edge_list)
    for e in sorted(edge_list, key=score, reverse=True):
        a, b = e
        if KIND[a] == "b" or KIND[b] == "b": continue
        if len(adj[a]) <= target - 1 or len(adj[b]) <= target - 1: continue
        if len(adj[a]) <= target and len(adj[b]) <= target: continue
        adj[a].discard(b); adj[b].discard(a)
        if conn(): out.remove(e)
        else: adj[a].add(b); adj[b].add(a)
    return out
TAXI = thin(TAXI)
# どの駅にもタクシーの道が2本以上あるように、近い候補から補う（川・海を越えない）
for v in land:
    have = sum(1 for e in TAXI if v in e)
    for i, j in sorted((e for e in cand if v in e and e not in TAXI), key=lambda e: dist(*e)):
        if have >= 2: break
        if wet(P[i], P[j]) or KIND[i] == "b" or KIND[j] == "b" or crosses_river(P[i], P[j]): continue
        TAXI.append((i, j)); have += 1

edges = {}
def add(a, b, t, line):
    key = (min(a, b), max(a, b))
    edges.setdefault(key, {}).setdefault(t, set()).add(line)
for a, b in TAXI: add(a, b, "taxi", "タクシー")
for name, seq in TRAINS:
    s = ix(seq)
    for a, b in zip(s, s[1:]): add(a, b, "tube", name)
for r, seq in enumerate(BUSES):
    s = ix(seq)
    for a, b in zip(s, s[1:]):
        add(a, b, "bus", f"バス {r + 1}番")
        if dist(a, b) > 480: print("long bus hop", ST[a][0], ST[b][0], round(dist(a, b)))
        if KIND[a] != "b" and KIND[b] != "b" and crosses_river(P[a], P[b]): print("bus crosses river", ST[a][0], ST[b][0])
        if wet(P[a], P[b]): print("bus in bay", ST[a][0], ST[b][0])
for name, seq in BOATS:
    s = ix(seq)
    for a, b in zip(s, s[1:]): add(a, b, "boat", name)

ADJ = [set() for _ in range(N)]
for (a, b) in edges: ADJ[a].add(b); ADJ[b].add(a)
seen = {0}; q = deque([0])
while q:
    u = q.popleft()
    for v in ADJ[u]:
        if v not in seen: seen.add(v); q.append(v)
print("stations", N, "connected", len(seen) == N, "edges", len(edges), "taxi", len(TAXI))
deg = [len(ADJ[i]) for i in range(N)]
print("low degree:", [(ST[i][0], deg[i]) for i in range(N) if deg[i] < 3])
print("taxi degree min/avg:", min(sum(1 for e in TAXI if i in e) for i in land), round(2 * len(TAXI) / len(land), 2))

board = {
    "W": W, "H": H,
    "stations": [[s[0], s[1], s[2]] for s in ST],
    "taxi": [list(e) for e in TAXI],
    "tube": [[name, ix(seq)] for name, seq in TRAINS],
    "bus": [ix(seq) for seq in BUSES],
    "boat": [[name, ix(seq)] for name, seq in BOATS],
    "heli": ix(HELI),
    "islands": [i for i in range(N) if KIND[i] == "i"],
    "bridges": [i for i in range(N) if KIND[i] == "b"],
    "river": RIVER, "coast": COAST,
}
json.dump(board, open(os.path.join(HERE, "board.json"), "w"), ensure_ascii=False)

# ---- 道路：タクシーの辺を「まっすぐ抜ける」組み合わせでつなぎ、長い道にする ----
def chains(edge_list):
    inc = {}
    for e in edge_list:
        for v in e: inc.setdefault(v, []).append(e)
    pair = {}   # (v, e) -> 反対側へ続く辺
    for v, es in inc.items():
        cand = []
        for x in range(len(es)):
            for y in range(x + 1, len(es)):
                a_ = es[x][0] if es[x][1] == v else es[x][1]
                b_ = es[y][0] if es[y][1] == v else es[y][1]
                u1 = (P[a_][0] - P[v][0], P[a_][1] - P[v][1]); u2 = (P[b_][0] - P[v][0], P[b_][1] - P[v][1])
                cos = (u1[0] * u2[0] + u1[1] * u2[1]) / (math.hypot(*u1) * math.hypot(*u2))
                if cos < -0.55: cand.append((cos, es[x], es[y]))
        used = set()
        for cos, e1, e2 in sorted(cand):
            if e1 in used or e2 in used: continue
            used |= {e1, e2}; pair[(v, e1)] = e2; pair[(v, e2)] = e1
    left, out = set(edge_list), []
    for e in edge_list:
        if e not in left: continue
        left.discard(e)
        seq = [e[0], e[1]]
        for end in (1, 0):
            cur_e = e
            while True:
                v = seq[-1] if end == 1 else seq[0]
                nx = pair.get((v, cur_e))
                if not nx or nx not in left: break
                left.discard(nx)
                w = nx[0] if nx[1] == v else nx[1]
                if end == 1: seq.append(w)
                else: seq.insert(0, w)
                cur_e = nx
        out.append(seq)
    return out
ROADS = chains([tuple(e) for e in TAXI])
board["roads"] = ROADS
json.dump(board, open(os.path.join(HERE, "board.json"), "w"), ensure_ascii=False)
print("roads:", len(ROADS), "avg len", round(sum(len(r) for r in ROADS) / len(ROADS), 2))

def catmull(pts, closed=False, steps=12):
    """駅を必ず通るなめらかな曲線（Catmull-Rom）"""
    if closed and pts[0] == pts[-1]: pts = pts[:-1]
    n = len(pts); out = []
    rng = range(n) if closed else range(n - 1)
    for i in rng:
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
    f = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 20)
    sc = lambda p: (p[0] * K, p[1] * K)
    dr.polygon([sc(p) for p in COAST] + [(W, H), (0, H)][:1] + [(COAST[-1][0] * K + 2000, H), (COAST[0][0] * K, H)], fill="#A9CFE0")
    rw = 55 * K
    for x, y in catmull([sc(p) for p in RIVER[::3]] + [sc(RIVER[-1])], steps=20):
        dr.ellipse([x - rw, y - rw, x + rw, y + rw], fill="#8DBBD4")
    # 道路：灰色の縁取りの白い曲線
    for r in ROADS:
        dr.line(catmull([sc(P[i]) for i in r]), fill="#9A968C", width=int(30 * K), joint="curve")
    for r in ROADS:
        dr.line(catmull([sc(P[i]) for i in r]), fill="#FFFFFF", width=int(20 * K), joint="curve")
    for seq in BUSES:
        dr.line(catmull([sc(P[i]) for i in ix(seq)]), fill="#16935B", width=int(7 * K), joint="curve")
    for name, seq in BOATS:
        dr.line(catmull([sc(P[i]) for i in ix(seq)]), fill="#2F7FB0", width=int(6 * K), joint="curve")
    for name, seq in TRAINS:
        pts = [sc(P[i]) for i in ix(seq)]   # 電車はまっすぐ
        dr.line(pts, fill="#7A1510", width=int(16 * K), joint="curve")
        dr.line(pts, fill="#E0413A", width=int(10 * K), joint="curve")
    tube_st = {i for _, seq in TRAINS for i in ix(seq)}
    hs = set(ix(HELI))
    for i, (x, y) in enumerate(P):
        x, y = x * K, y * K
        if i in hs: dr.ellipse([x - 17, y - 17, x + 17, y + 17], outline="#7C3AED", width=3)
        if KIND[i] == "b": dr.polygon([(x, y - 15), (x + 15, y), (x, y + 15), (x - 15, y)], fill="#CDB98C", outline="#3B2C1E")
        dr.ellipse([x - 16, y - 11, x + 16, y + 11], fill="#E0413A" if i in tube_st else "#FFFFFF", outline="#3B2C1E", width=2)
        dr.text((x, y + 13), ST[i][0], fill="#2A1E12", font=f, anchor="ma", stroke_width=3, stroke_fill="#FBF5E4")
    im.save(sys.argv[1])
