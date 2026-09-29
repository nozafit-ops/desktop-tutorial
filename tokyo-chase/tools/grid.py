# 格子状の盤面を組み立てる
#  - 道路（タクシー）は格子。駅は交差点
#  - 隅田川が西岸(W)と東岸・北岸(E)を分け、5本の橋でだけ渡れる。右下は東京湾(~)、島(I)
#  - 電車は盤面の外周をまわる環状線と、中央の小さな環状線（センターサークル）、それを結ぶ2路線
#  - 東京の駅名は、実際の位置関係のまま交差点へ割り当てる（geo.json の位置から最小コストの割当て）
# 出力: board.json と確認用の路線図 PNG
import json, math, os, sys, random
from collections import deque
import numpy as np
from scipy.optimize import linear_sum_assignment

HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)
from stations import W, H

MAP = """
. W W W W . E E E E E E E E E
W W W W W W W W W E E E E E E
W W W W W W W W W W E E E E E
W W W W W W W W W E E E E E E
W W W W W W W W W E E E E E E
W W W W W W W ~ ~ E E E E ~ ~
. W W W W W ~ ~ ~ I ~ ~ ~ ~ ~
. W W W W W ~ I ~ ~ ~ ~ ~ ~ ~
"""
GRID = [row.split() for row in MAP.strip().splitlines()]
ROWS, COLS = len(GRID), len(GRID[0])
MX, MY = 150, 140
SX, SY = (W - 2 * MX) / (COLS - 1), (H - 2 * MY) / (ROWS - 1)
cell = lambda c, r: GRID[r][c]
pos = lambda c, r: (MX + c * SX, MY + r * SY)

# 橋：川をまたぐ格子の辺（西岸と東岸の間）の中点に駅を置く
BRIDGES = {("千住大橋"): ((7, 0), (7, 1)), ("言問橋"): ((8, 1), (9, 1)), ("両国橋"): ((9, 2), (10, 2)),
           ("清洲橋"): ((8, 3), (9, 3)), ("勝鬨橋"): ((8, 4), (9, 4))}

# 必ず残したい有名な駅（割当てで落とさない）
FAMOUS = set("""東京 新宿 渋谷 池袋 上野 浅草 品川 銀座 秋葉原 六本木 原宿 表参道 押上 両国 錦糸町 北千住 赤羽 中野 荻窪
恵比寿 目黒 五反田 大井町 蒲田 新橋 浜松町 日本橋 築地 月島 豊洲 門前仲町 葛西 下北沢 三軒茶屋 自由が丘 二子玉川 お台場 羽田空港
高田馬場 飯田橋 御茶ノ水 神保町 四ツ谷 赤坂 永田町 虎ノ門 日暮里 巣鴨 王子 練馬 亀戸 小岩 綾瀬 新木場 葛西臨海公園 天王洲アイル 清澄白河 日の出
西新井 金町 亀有 柴又 曳舟 大森""".split())

geo = json.load(open(os.path.join(HERE, "geo.json")))
NAMES = [s for s in geo["stations"] if s[3] != "b"]

# ---- 駅名の割当て ----
nodes = [(c, r) for r in range(ROWS) for c in range(COLS) if cell(c, r) in "WEI"]
side = {"W": "w", "E": "e", "I": "i"}
# 盤面座標（geo）を格子の範囲に合わせて正規化してから比べる
gx = [s[1] for s in NAMES]; gy = [s[2] for s in NAMES]
nx0, nx1, ny0, ny1 = min(gx), max(gx), min(gy), max(gy)
norm = lambda x, y: ((x - nx0) / (nx1 - nx0) * (W - 2 * MX) + MX, (y - ny0) / (ny1 - ny0) * (H - 2 * MY) + MY)
cost = np.full((len(NAMES), len(nodes) + len(NAMES)), 1e9)
for i, (name, x, y, k) in enumerate(NAMES):
    px, py = norm(x, y)
    for j, (c, r) in enumerate(nodes):
        if side[cell(c, r)] != k: continue
        nxp, nyp = pos(c, r)
        cost[i, j] = math.hypot(px - nxp, py - nyp) ** 2
    cost[i, len(nodes) + i] = 5e6 if name in FAMOUS else 2.5e5   # 割当てから外す費用
rows_, cols_ = linear_sum_assignment(cost)
at = {}
dropped = []
for i, j in zip(rows_, cols_):
    if j < len(nodes): at[nodes[j]] = NAMES[i][0]
    else: dropped.append(NAMES[i][0])
empty = [n for n in nodes if n not in at]

# ---- 駅の番号順：上の行から左→右 ----
ST, NID = [], {}
for (c, r) in nodes:
    NID[(c, r)] = len(ST)
    ST.append([at.get((c, r), "?"), round(pos(c, r)[0], 1), round(pos(c, r)[1], 1)])
BR_ID = {}
for name, (a, b) in BRIDGES.items():
    pa, pb = pos(*a), pos(*b)
    BR_ID[(a, b)] = len(ST)
    ST.append([name, round((pa[0] + pb[0]) / 2, 1), round((pa[1] + pb[1]) / 2, 1)])
N = len(ST)
ID = {s[0]: i for i, s in enumerate(ST)}

# ---- 道路（タクシー）：格子の隣どうし。川は橋でだけ渡る。ところどころ道を抜いて街らしくする ----
rnd = random.Random(7)
TAXI = []
for (c, r) in nodes:
    for dc, dr in ((1, 0), (0, 1)):
        o = (c + dc, r + dr)
        if o not in NID: continue
        a, b = cell(c, r), cell(*o)
        if "I" in (a, b): continue
        if a != b:
            key = next((k for k in BRIDGES.values() if set(k) == {(c, r), o}), None)
            if key:
                TAXI += [(NID[(c, r)], BR_ID[key]), (BR_ID[key], NID[o])]
            continue
        TAXI.append((NID[(c, r)], NID[o]))

def neighbors(edges):
    adj = [set() for _ in range(N)]
    for a, b in edges: adj[a].add(b); adj[b].add(a)
    return adj

def connected(edges, nodes_):
    adj = neighbors(edges)
    s = next(iter(nodes_)); seen = {s}; q = deque([s])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if v not in seen: seen.add(v); q.append(v)
    return nodes_ <= seen

land = {NID[n] for n in nodes if cell(*n) != "I"} | set(BR_ID.values())
order = [e for e in TAXI if ST[e[0]][0] not in BRIDGES and ST[e[1]][0] not in BRIDGES]
rnd.shuffle(order)
removed = 0
for e in order:
    if removed >= 22: break
    adj = neighbors(TAXI)
    if len(adj[e[0]]) <= 3 or len(adj[e[1]]) <= 3: continue
    rest = [x for x in TAXI if x != e]
    if connected(rest, land):
        TAXI = rest; removed += 1

# ---- 電車 ----
def line(cells): return [NID[c] for c in cells]
TRAINS = [
    # 盤面の外周をぐるりと囲む環状線（2区画おきに停車）
    ("山手線", line([(1, 1), (3, 1), (5, 1), (7, 1), (9, 1), (11, 1), (13, 1), (13, 3), (13, 4), (11, 4), (9, 4),
                   (7, 4), (5, 4), (5, 6), (3, 6), (1, 6), (1, 4), (1, 2), (1, 1)])),
    # 都心の小さな環状線（センターサークル）
    ("センターサークル", line([(4, 2), (6, 2), (8, 2), (8, 3), (6, 3), (4, 3), (4, 2)])),
    ("中央・総武線", line([(0, 3), (3, 3), (6, 3), (9, 3), (12, 3), (14, 3)])),
    ("京浜東北線", line([(4, 0), (4, 3), (4, 5), (4, 7)])),
]
# ---- バス：まっすぐな大通りを2区画おきに停まる ----
def bus(cells): return [NID[c] if c in NID else BR_ID[c] for c in cells]
BUSES = [
    bus([(1, 0), (1, 2), (1, 4), (1, 6)]),
    bus([(3, 0), (3, 2), (3, 4), (3, 6)]),
    bus([(5, 1), (5, 3), (5, 5), (5, 7)]),
    bus([(0, 1), (2, 1), (4, 1), (6, 1)]),
    bus([(0, 2), (2, 2), (4, 2), (6, 2), (8, 2)]),
    bus([(0, 4), (2, 4), (4, 4), (6, 4)]),
    bus([(1, 7), (3, 7), (5, 7)]),
    bus([(7, 4), (7, 2), (7, 1)]),
    bus([(10, 1), (12, 1), (14, 1)]),
    bus([(10, 2), (12, 2), (14, 2)]),
    bus([(9, 5), (11, 5), (12, 5)]),
    bus([(11, 0), (11, 2), (11, 4)]),
    bus([(13, 0), (13, 2), (13, 4)]),
    bus([(6, 0), (8, 0), (10, 0), (12, 0)]),
    # 橋を渡るバス
    bus([(6, 1), (8, 1), ((8, 1), (9, 1)), (9, 1), (11, 1)]),
    bus([(6, 3), (8, 3), ((8, 3), (9, 3)), (9, 3), (11, 3)]),
    bus([(6, 4), (8, 4), ((8, 4), (9, 4)), (9, 4), (11, 4)]),
]
BOATS = [
    ("隅田川ライン", line([(9, 2), (9, 3), (9, 4), (7, 4), (9, 6), (5, 6), (7, 7)])),
    ("臨海ライン", line([(13, 4), (12, 5), (9, 6)])),
]
HELI = line([(0, 3), (3, 3), (4, 4), (4, 0), (11, 2), (13, 4), (9, 6), (7, 7)])

# ---- 書き出し ----
edges = {}
def add(a, b, t, name):
    edges.setdefault((min(a, b), max(a, b)), {}).setdefault(t, set()).add(name)
for a, b in TAXI: add(a, b, "taxi", "タクシー")
for name, seq in TRAINS:
    for a, b in zip(seq, seq[1:]): add(a, b, "tube", name)
for r, seq in enumerate(BUSES):
    for a, b in zip(seq, seq[1:]): add(a, b, "bus", f"バス {r + 1}番")
for name, seq in BOATS:
    for a, b in zip(seq, seq[1:]): add(a, b, "boat", name)
assert connected(list(edges), set(range(N))), "not connected"
# 川：西岸と東岸の境目（交差点のあいだ）を通る階段状の線。描画では角を丸める
RIVER_PATH = [[round(pos(c, r)[0], 1), round(pos(c, r)[1], 1)] for c, r in
              [(4.5, -0.8), (4.5, 0.5), (8.5, 0.5), (8.5, 1.5), (9.5, 1.5), (9.5, 2.5), (8.5, 2.5), (8.5, 5.0)]]
board = {
    "W": W, "H": H, "cols": COLS, "rows": ROWS, "grid": GRID,
    "stations": ST, "taxi": [list(e) for e in TAXI],
    "tube": [[n, s] for n, s in TRAINS], "bus": BUSES, "boat": [[n, s] for n, s in BOATS],
    "heli": HELI, "islands": [NID[n] for n in nodes if cell(*n) == "I"],
    "bridges": list(BR_ID.values()), "river": RIVER_PATH,
}
json.dump(board, open(os.path.join(HERE, "board.json"), "w"), ensure_ascii=False)

def render(path, K=0.6):
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new("RGB", (int(W * K), int(H * K)), "#D9D6CC")
    dr = ImageDraw.Draw(im)
    f = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", int(30 * K))
    sc = lambda p: (p[0] * K, p[1] * K)
    # 海と川
    for r in range(ROWS):
        for c in range(COLS):
            x, y = pos(c, r)
            if cell(c, r) in "~I":
                dr.rectangle([(x - SX / 2 - 1) * K, (y - SY / 2 - 1) * K, (x + SX / 2 + 1) * K, (y + SY / 2 + 1) * K], fill="#8FC3DE")
            if cell(c, r) == ".":
                dr.rectangle([(x - SX / 2) * K, (y - SY / 2) * K, (x + SX / 2) * K, (y + SY / 2) * K], fill="#9CC58A")
    dr.line([sc(p) for p in RIVER_PATH], fill="#8FC3DE", width=int(90 * K), joint="curve")
    col = {"taxi": "#FFFFFF", "bus": "#16935B", "tube": "#D2362C", "boat": "#2F7FB0"}
    wid = {"taxi": 34, "bus": 9, "tube": 12, "boat": 8}
    for (a, b), ty in edges.items():   # 道路は灰色の縁取りの白い道
        if "taxi" in ty: dr.line([sc(ST[a][1:3]), sc(ST[b][1:3])], fill="#9A968C", width=int(46 * K))
    for t in ["taxi", "boat", "bus", "tube"]:
        for (a, b), ty in edges.items():
            if t not in ty: continue
            lst = [x for x in ["boat", "tube", "bus"] if x in ty]
            off = 0 if t == "taxi" else (lst.index(t) - (len(lst) - 1) / 2) * 14
            (x1, y1), (x2, y2) = ST[a][1:3], ST[b][1:3]
            L = math.hypot(x2 - x1, y2 - y1) or 1
            nx_, ny_ = -(y2 - y1) / L * off, (x2 - x1) / L * off
            dr.line([sc((x1 + nx_, y1 + ny_)), sc((x2 + nx_, y2 + ny_))], fill=col[t], width=int(wid[t] * K))
    tube_st = {i for _, s in TRAINS for i in s}
    for i, (name, x, y) in enumerate(ST):
        x, y = x * K, y * K
        R = 26 * K
        if i in HELI: dr.ellipse([x - R - 10, y - R - 10, x + R + 10, y + R + 10], outline="#7C3AED", width=4)
        if i in BR_ID.values(): dr.polygon([(x, y - R - 8), (x + R + 8, y), (x, y + R + 8), (x - R - 8, y)], fill="#CDB98C", outline="#3B2C1E")
        dr.ellipse([x - R * 1.3, y - R, x + R * 1.3, y + R], fill="#E0413A" if i in tube_st else "#FFFFFF", outline="#3B2C1E", width=2)
        dr.text((x, y + R + 2), name, fill="#1A140C", font=f, anchor="ma", stroke_width=3, stroke_fill="#FFFFFF")
    im.save(path)

if __name__ == "__main__":
    print("dropped:", dropped)
    print("empty nodes:", empty)
    print("stations:", N, "taxi:", len(TAXI), "edges:", len(edges))
    deg = neighbors(list(edges))
    print("degree<3:", [(ST[i][0], len(deg[i])) for i in range(N) if len(deg[i]) < 3])
    if len(sys.argv) > 1: render(sys.argv[1])
    for r in range(ROWS):
        print(" ".join(f"{at.get((c, r), '~'):>6}" for c in range(COLS)))
