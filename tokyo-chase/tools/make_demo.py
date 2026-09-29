# トーキョー・チェイス（デモ版）を作る：ロンドン・チェイスの HTML をもとに、盤面とルールを東京版に差し替える
#   python3 make_demo.py <london.html>   → tokyo-chase/index.html
# 盤面は board_sy.json（sy_build.py が作る）、駅名は names.py の仮想の地名
# ルール（シミュレーションで決めたもの）
#  - 乗り物：タクシー・バス・地下鉄。水上バスは怪盗Xだけが黒チケットで乗れる（刑事は乗れない）
#  - 刑事の切符は有限（タクシー12・バス10・地下鉄5・ヘリ1）。使った切符は怪盗Xの手持ちに加わる
#  - 21手、3手ごとに姿を現す（ロンドン版と同じ）
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from names import NAMES, RIVER_NAME

src = open(sys.argv[1], encoding="utf-8").read()
# 公開時に付く外枠（doctype〜body）は取り除き、中身だけにする
if src.lstrip().lower().startswith("<!doctype"):
    src = src[src.index("<body>") + len("<body>"):].lstrip("\n")
    src = src[:src.rindex("</body>")].rstrip() + "\n"
B = json.load(open(os.path.join(HERE, "board_sy.json"), encoding="utf-8"))
out = src

def sub(old, new, count=1):
    global out
    n = out.count(old)
    assert n >= 1, f"not found: {old[:80]}"
    if count == 1: assert n == 1, f"ambiguous ({n}): {old[:80]}"
    out = out.replace(old, new)

def rsub(pattern, new, flags=re.S):
    global out
    out2, n = re.subn(pattern, new, out, count=1, flags=flags)
    assert n == 1, f"pattern not found: {pattern[:80]}"
    out = out2

# ---------------- 題名・保存キー ----------------
sub("<title>ロンドン・チェイス</title>", "<title>トーキョー・チェイス</title>")
sub("london-chase-", "tokyo-chase-", count=0)
sub('aria-label="ロンドンの盤面。', 'aria-label="東京の盤面。')
sub("window.londonChaseBackgroundSVG", "window.tokyoChaseBackgroundSVG")

# タイトル画面・結果画面の背景（ロンドンの写真の代わりに夜の東京の色）
sub('''.screen.title { background: linear-gradient(rgba(10,13,20,.35), rgba(10,13,20,.55)), url("art/title/title-bg.webp") center / cover no-repeat, #141B29; }''',
    '''.screen.title { background: radial-gradient(90% 60% at 50% 100%, rgba(228,0,127,.28), transparent 70%), radial-gradient(120% 80% at 50% 0%, #25306A, #0B0E1F 72%), #0B0E1F; }''')
sub('''.rs-scene.escape { background-image: url("art/results/result-escape.webp"); }''', '''.rs-scene.escape { background: linear-gradient(#1B2150, #3A1D4E); }''')
sub('''.rs-scene.escape.meet { background-image: url("art/results/result-meet.webp"); }''', '''.rs-scene.escape.meet { background: linear-gradient(#2B1B50, #5A2A4E); }''')
sub('''.rs-scene.caught { background-image: url("art/results/result-caught.webp"); }''', '''.rs-scene.caught { background: linear-gradient(#10224A, #1F3E7A); }''')
sub('''<img class="logo-img" src="art/title/title-logo.webp" alt="LONDON CHASE"><h1 class="sub">ロンドン・チェイス</h1><p>霧の街に消えた怪盗Xを、刑事たちが追う</p></div>''',
    '''<div class="en">TOKYO CHASE</div><h1>トーキョー・チェイス</h1><p>夜の街に消えた怪盗Xを、刑事たちが追う<br><span class="pill gold">デモ版</span></p></div>''')
sub("怪盗Xは霧のロンドンへ消えた", "怪盗Xは夜の街へ消えた")

# ---------------- 盤面データ ----------------
st = [[NAMES[i], s[1], s[2]] for i, s in enumerate(B["stations"])]
boat_paths = {f"{min(a, b)}-{max(a, b)}": p for (a, b), p in zip(B["boatEdges"], B["boatPaths"])}
data = f'''const W = {B["W"]}, H = {B["H"]};
  // 仮想の東京（スコットランドヤード式）。tools/sy_build.py で生成、駅名は tools/names.py
  const STATIONS = {json.dumps(st, ensure_ascii=False)};
  const TAXI = {json.dumps(B["taxi"])};
  const TUBE = {json.dumps([["地下鉄", e] for e in B["subwayEdges"]], ensure_ascii=False)};
  const BUS = {json.dumps(B["busEdges"])};
  const BOATS = {json.dumps([["水上バス", e] for e in B["boatEdges"]], ensure_ascii=False)};
  const BOAT_PATH = new Map(Object.entries({json.dumps(boat_paths)}));
  const HELI = {json.dumps(B["heli"])};
  const RIVER = {json.dumps(B["river"])};
  const COAST = {json.dumps(B["coast"])};
  const RIVER_NAME = "{RIVER_NAME}";
  const BRIDGE_ST = {json.dumps(B["bridges"])};
  const ISLAND_LIST = {json.dumps(B["islands"])};
  '''
a = out.index("const W = 3000, H = 1900;"); b = out.index("const N = STATIONS.length;")
out = out[:a] + data + out[b:]
rsub(r"const ISLAND_ST = new Set\(STATIONS[\s\S]*?\}\)\);", "const ISLAND_ST = new Set(ISLAND_LIST);")
sub('for (let k = 0; k < BOAT.length - 1; k++) addEdge(BOAT[k], BOAT[k + 1], "boat", "テムズ水上バス");',
    'for (const [line, seq] of BOATS) for (let k = 0; k < seq.length - 1; k++) addEdge(seq[k], seq[k + 1], "boat", line);')

# ---------------- ルール ----------------
sub('tube:  { name: "地下鉄", en: "Underground", short: "地" },', 'tube:  { name: "地下鉄", en: "Subway", short: "地" },')
sub('boat:  { name: "水上バス", en: "River Bus", short: "船" },', 'boat:  { name: "水上バス", en: "Water Bus", short: "船" },')
sub('''  // 刑事の切符はヘリ以外は使い放題。怪盗Xはすべての切符が有限
  const DET_TICKETS = { heli: 1 };
  const X_TICKETS = { taxi: 10, bus: 7, tube: 4, boat: 2 };
  const dHas = (d, type) => type === "heli" ? d.t.heli > 0 : true;''',
'''  // 刑事の切符も有限。使った切符は怪盗Xの手持ちに加わる（スコットランドヤードのルール）
  // 水上バスは怪盗Xだけが黒チケットで乗れる。刑事は乗れない
  const DET_TICKETS = { taxi: 12, bus: 10, tube: 5, heli: 1 };
  const X_TICKETS = { taxi: 10, bus: 7, tube: 4, boat: 0 };
  const dHas = (d, type) => type === "boat" ? false : (d.t[type] ?? 0) > 0;''')
sub('''    if (type === "heli") d.t.heli--;
''', '''    if (type === "heli") d.t.heli--;
    else if (d.t[type] !== undefined) { d.t[type]--; if (G.xt && G.xt[type] !== undefined) G.xt[type]++; }
''')
# ロンドン版の不具合の修正：怪盗Xが「駅破壊」で自分の最後の逃げ道を壊さないようにする
sub('''      return [...Array(N).keys()].filter(i => i !== sec.pos && D[sec.pos][i] <= 2 && !occ.has(i) && !isRuin(G, i));''',
    '''      const exitsLeft = i => ADJ[sec.pos].some(e => e.to !== i && !occ.has(e.to) && !isRuin(G, e.to) && !isClosed(G.closedX, e.to, G));
      return [...Array(N).keys()].filter(i => i !== sec.pos && D[sec.pos][i] <= 2 && !occ.has(i) && !isRuin(G, i) && exitsLeft(i));''')
sub('''    const exits = o => new Set(ADJ[sec.pos].map(e => e.to).filter(t => t !== o && !isRuin(G, t))).size;''',
    '''    const exits = o => new Set(ADJ[sec.pos].map(e => e.to).filter(t => t !== o && !isRuin(G, t) && !G.det.some(d => d.pos === t) && !isClosed(G.closedX, t, G))).size;''')
sub('''        for (const [c, t] of aiUseCards(G, A.sec, "x")) useCardNow("x", c, t);
''', '''        for (const [c, t] of aiUseCards(G, A.sec, "x")) useCardNow("x", c, t);
        if (!xMoves(G, A.sec).length) { apply(() => finish(G, "d", "trapped")); continue; }
''')

# ---------------- 画面の表示 ----------------
sub('''aria-label="${dName(k)}：切符は使い放題・ヘリ${d.t.heli}">''',
    '''aria-label="${dName(k)}：タクシー${d.t.taxi}・バス${d.t.bus}・地下鉄${d.t.tube}・ヘリ${d.t.heli}">''')
sub('''<span class="tk inf" title="タクシー・バス・地下鉄・水上バスは使い放題">切符∞</span>''',
    '''${["taxi", "bus", "tube"].map(t => `<span class="tk ${t} ${d.t[t] ? "" : "zero"}" title="${TYPE[t].name}の残り">${TYPE[t].short}${d.t[t]}</span>`).join("")}''')
sub('''<span class="cnt">${t === "heli" ? d.t.heli : "∞"}</span>''', '''<span class="cnt">${d.t[t] ?? ""}</span>''')
sub('''${G.xt ? ["taxi", "bus", "tube", "boat"].map(t =>''', '''${G.xt ? ["taxi", "bus", "tube"].map(t =>''')
sub('''  .det { position: relative; }''', '''  .det { position: relative; }
  .det .tks { flex-wrap: wrap; justify-content: center; max-width: 92px; }''')

# 水上バスは川に沿った航路で描く
sub('''        el("line", { ...pts, class: `edge ${t} casing` }, g);
        el("line", { ...pts, class: `edge ${t}` }, g);''',
'''        if (t === "boat" && BOAT_PATH.has(key)) {
          const d = "M" + BOAT_PATH.get(key).map(p => p[0].toFixed(1) + "," + p[1].toFixed(1)).join(" L");
          el("path", { d, class: "edge boat casing", "stroke-linejoin": "round" }, g);
          el("path", { d, class: "edge boat", "stroke-linejoin": "round" }, g);
          return;
        }
        el("line", { ...pts, class: `edge ${t} casing` }, g);
        el("line", { ...pts, class: `edge ${t}` }, g);''')

# 遊び方
rsub(r'        <li>乗り物は4種類。.*?</li>\n', '''        <li>乗り物は3種類。<b>タクシー</b>（黄）は隣の駅へ。<b>バス</b>（緑）と <b>地下鉄</b>（赤）は遠くまで一気に進めます。駅マークの上半分の色が、その駅で使える乗り物です。</li>
        <li><b>水上バス</b>（青い破線）は${RIVER_NAME}と湾を結びます。乗れるのは <b>怪盗Xだけ</b>で、<b>黒チケット</b>を使います。刑事は乗れません。</li>
''')
sub('''島へは水上バスかヘリでしか行けません。''', '''2つの島（夢見島・空港島）へは水上バスかヘリでしか行けません。''')
sub('''        <li>川を渡る <b>橋</b> の上にも駅（ひし形の台座）があり、タクシーとバスは橋で一度止まります。</li>''',
    '''        <li>${RIVER_NAME}を渡る <b>橋</b> の上にも駅（ひし形の台座）があり、タクシーとバスは橋で一度止まります。橋は5か所だけです。</li>''')
rsub(r'        <li><b>切符</b>：刑事はタクシー・バス・地下鉄・水上バスが使い放題.*?</li>',
     '''        <li><b>切符</b>：刑事の切符は1人あたりタクシー${DET_TICKETS.taxi}・バス${DET_TICKETS.bus}・地下鉄${DET_TICKETS.tube}・ヘリ${DET_TICKETS.heli}枚。<b>刑事が使った切符は怪盗Xの手持ちに加わります</b>。怪盗Xの切符（タクシー${X_TICKETS.taxi}・バス${X_TICKETS.bus}・地下鉄${X_TICKETS.tube}・黒チケット・2倍移動${X_DOUBLE}・ヘリ${X_HELI}）も有限。切符が尽きた乗り物には乗れません。動けなくなると怪盗Xの負け、刑事が全員動けなくなると怪盗Xの勝ち。</li>''')

# ---------------- 背景（コードで描く簡単な地図） ----------------
a = out.index("  function backgroundSVG() {"); b = out.index("  async function renderBackground() {")
bg = r'''  function backgroundSVG() {
    // デモ版の背景：陸・大川・湾・島・橋だけの簡単な地図（絵は後で差し替える）
    let seed = 1964;
    const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
    const o = [];
    const pts = a => a.map(p => p[0].toFixed(1) + "," + p[1].toFixed(1)).join(" ");
    o.push(`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">`);
    o.push(`<defs>
      <pattern id="waves" width="46" height="20" patternUnits="userSpaceOnUse"><path d="M2,11 q9,-8 18,0 t18,0" fill="none" stroke="#7FA7B8" stroke-width="1.6" opacity="0.55"/></pattern>
      <pattern id="trees" width="26" height="22" patternUnits="userSpaceOnUse"><circle cx="7" cy="7" r="4.5" fill="#8FA87A"/><circle cx="19" cy="17" r="4" fill="#8FA87A"/></pattern>
      <radialGradient id="vig" cx="50%" cy="50%" r="72%"><stop offset="65%" stop-color="#2A2418" stop-opacity="0"/><stop offset="100%" stop-color="#2A2418" stop-opacity="0.35"/></radialGradient>
    </defs>`);
    o.push(`<rect width="${W}" height="${H}" fill="#E6DECB"/>`);
    // 街区（うすい格子）
    let d = "";
    for (let x = 0; x < W; x += 60) for (let y = 0; y < H; y += 60) {
      if (rnd() < 0.5) d += `M${x + 6},${y + 6}h${40 + rnd() * 10}v${40 + rnd() * 10}h${-40 - rnd() * 10}Z`;
    }
    o.push(`<path d="${d}" fill="#DDD3BC" opacity="0.7"/>`);
    // 公園（駅から離れた空き地）
    let parks = 0;
    for (let t = 0; t < 600 && parks < 10; t++) {
      const x = 160 + rnd() * (W - 320), y = 160 + rnd() * (H - 320);
      if (STATIONS.some(s => Math.hypot(s[1] - x, s[2] - y) < 130)) continue;
      if (RIVER.some(([rx, ry]) => Math.hypot(rx - x, ry - y) < 200)) continue;
      o.push(`<g transform="translate(${x.toFixed(0)} ${y.toFixed(0)}) rotate(${((rnd() - 0.5) * 40).toFixed(0)})"><ellipse rx="${(60 + rnd() * 40).toFixed(0)}" ry="${(36 + rnd() * 20).toFixed(0)}" fill="#BFCB9C" stroke="#7E8F55" stroke-width="2.5"/></g>`);
      parks++;
    }
    // 湾
    const last = COAST[COAST.length - 1], first = COAST[0];
    const bay = pts([...COAST, [W + 400, last[1]], [W + 400, H + 400], [first[0], H + 400]]);
    o.push(`<polygon points="${bay}" fill="#A9C9D6" stroke="#6E98AE" stroke-width="5"/><polygon points="${bay}" fill="url(#waves)"/>`);
    // 大川
    o.push(`<polyline points="${pts(RIVER)}" fill="none" stroke="#6E98AE" stroke-width="122" stroke-linejoin="round" stroke-linecap="round"/>`);
    o.push(`<polyline points="${pts(RIVER)}" fill="none" stroke="#A9C9D6" stroke-width="110" stroke-linejoin="round" stroke-linecap="round"/>`);
    o.push(`<polyline points="${pts(RIVER)}" fill="none" stroke="url(#waves)" stroke-width="100" stroke-linejoin="round"/>`);
    // 島
    for (const i of ISLAND_LIST) o.push(`<ellipse cx="${STATIONS[i][1]}" cy="${STATIONS[i][2]}" rx="120" ry="80" fill="#E3D9BD" stroke="#6E98AE" stroke-width="5"/><ellipse cx="${STATIONS[i][1]}" cy="${STATIONS[i][2]}" rx="92" ry="56" fill="url(#trees)" opacity="0.5"/>`);
    // 橋（両岸の駅を結ぶ向き）
    for (const bi of BRIDGE_ST) {
      const nb = TAXI.filter(e => e.includes(bi)).map(e => e[0] === bi ? e[1] : e[0]);
      if (nb.length < 2) continue;
      const [p, q] = [STATIONS[nb[0]], STATIONS[nb[1]]];
      const ang = Math.atan2(q[2] - p[2], q[1] - p[1]) * 180 / Math.PI;
      o.push(`<g transform="translate(${STATIONS[bi][1]} ${STATIONS[bi][2]}) rotate(${ang.toFixed(1)})"><rect x="-95" y="-16" width="190" height="32" rx="4" fill="#CFC3A2" stroke="#3B2C1E" stroke-width="3"/></g>`);
    }
    // 川と湾の名前
    const m = RIVER[Math.floor(RIVER.length * 0.55)];
    o.push(`<text x="${m[0] + 90}" y="${m[1]}" font-family="Zen Old Mincho, serif" font-size="44" font-weight="700" fill="#4E7890" opacity="0.8">${RIVER_NAME}</text>`);
    o.push(`<text x="${W - 700}" y="${H - 260}" font-family="Zen Old Mincho, serif" font-size="64" font-weight="700" letter-spacing="30" fill="#4E7890" opacity="0.6">東京湾</text>`);
    // 方位記号と表題
    o.push(`<g transform="translate(${W - 120} 150)"><circle r="64" fill="#F2EBD8" stroke="#3B2C1E" stroke-width="3"/><path d="M0,-72 L12,0 L0,72 L-12,0 Z M-72,0 L0,-12 L72,0 L0,12 Z" fill="#D9CDAE" stroke="#3B2C1E" stroke-width="2"/><path d="M0,-72 L12,0 L-12,0 Z" fill="#3B2C1E"/><text y="-80" font-family="Georgia, serif" font-size="26" fill="#3B2C1E" text-anchor="middle">N</text></g>`);
    o.push(`<rect width="${W}" height="${H}" fill="url(#vig)"/>`);
    o.push(`</svg>`);
    return o.join("");
  }

'''
out = out[:a] + bg + out[b:]
sub('''const ART = { map: "art/london-map.webp",''', '''const ART = { map: null,''')

# ---------------- 残っていないかの確認 ----------------
for word in ["テムズ", "ロンドン", "london-map", "霧の"]:
    assert word not in out, f"leftover: {word}"
dst = os.path.join(HERE, "..", "index.html")
open(dst, "w", encoding="utf-8").write(out)
print("wrote", os.path.normpath(dst), len(out), "bytes")
