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
    ("山手線", ["東京", "上野", "日暮里", "巣鴨", "池袋", "高田馬場", "新宿", "渋谷", "目黒", "品川", "浜松町", "新橋", "東京"]),
    ("中央線", ["荻窪", "中野", "新宿", "四ツ谷", "御茶ノ水", "東京"]),
    ("銀座線", ["渋谷", "表参道", "青山一丁目", "虎ノ門", "銀座", "日本橋", "上野", "浅草"]),
    ("東西線", ["中野", "高田馬場", "飯田橋", "日本橋", "門前仲町", "東陽町", "葛西"]),
    ("半蔵門線", ["渋谷", "永田町", "神保町", "清澄白河", "押上"]),
    ("常磐線", ["上野", "日暮里", "南千住", "北千住", "綾瀬"]),
    ("総武線", ["御茶ノ水", "秋葉原", "両国", "錦糸町", "新小岩", "小岩"]),
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

if len(sys.argv) > 1:
    from PIL import Image, ImageDraw, ImageFont
    K = 0.75
    im = Image.new("RGB", (int(W * K), int(H * K)), "#EFE6CF")
    dr = ImageDraw.Draw(im)
    f = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 20)
    sc = lambda p: (p[0] * K, p[1] * K)
    dr.polygon([sc(p) for p in COAST] + [(W, H), (0, H)][:1] + [(COAST[-1][0] * K + 2000, H), (COAST[0][0] * K, H)], fill="#A9CFE0")
    dr.line([sc(p) for p in RIVER], fill="#8DBBD4", width=int(110 * K))
    col = {"taxi": "#F2B51D", "bus": "#16935B", "tube": "#D2362C", "boat": "#2F7FB0"}
    wid = {"taxi": 3, "bus": 5, "tube": 6, "boat": 4}
    for t in ["boat", "tube", "bus", "taxi"]:
        for (a, b), ty in edges.items():
            if t not in ty: continue
            lst = [x for x in ["boat", "tube", "bus", "taxi"] if x in ty]
            k = lst.index(t)
            off = (k - (len(lst) - 1) / 2) * 7
            (x1, y1), (x2, y2) = sc(P[a]), sc(P[b])
            L = math.hypot(x2 - x1, y2 - y1) or 1
            nx, ny = -(y2 - y1) / L * off / 1, (x2 - x1) / L * off / 1
            dr.line([(x1 + nx, y1 + ny), (x2 + nx, y2 + ny)], fill=col[t], width=wid[t])
    hs = set(ix(HELI))
    for i, (x, y) in enumerate(P):
        x, y = x * K, y * K
        if i in hs: dr.ellipse([x - 17, y - 17, x + 17, y + 17], outline="#7C3AED", width=3)
        if KIND[i] == "b": dr.polygon([(x, y - 15), (x + 15, y), (x, y + 15), (x - 15, y)], fill="#CDB98C", outline="#3B2C1E")
        dr.ellipse([x - 11, y - 11, x + 11, y + 11], fill="#FBF5E4", outline="#3B2C1E", width=2)
        dr.text((x, y + 13), ST[i][0], fill="#2A1E12", font=f, anchor="ma", stroke_width=3, stroke_fill="#FBF5E4")
    im.save(sys.argv[1])
