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
  const ISLAND_SIZE = {json.dumps(B["islandSize"])};
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
'''  // 刑事の切符はヘリ以外は使い放題。怪盗Xはすべての切符が有限
  // 水上バスは怪盗Xだけが黒チケットで乗れる。刑事は乗れない
  const DET_TICKETS = { heli: 1 };
  const X_TICKETS = { taxi: 10, bus: 7, tube: 4, boat: 0 };
  const dHas = (d, type) => type === "boat" ? false : type === "heli" ? d.t.heli > 0 : true;''')
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
sub('''<span class="tk inf" title="タクシー・バス・地下鉄・水上バスは使い放題">切符∞</span>''',
    '''<span class="tk inf" title="タクシー・バス・地下鉄は使い放題">切符∞</span>''')
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
     '''        <li><b>切符</b>：刑事はタクシー・バス・地下鉄が使い放題（ヘリだけ${DET_TICKETS.heli}枚。水上バスには乗れません）。怪盗Xの切符（タクシー${X_TICKETS.taxi}・バス${X_TICKETS.bus}・地下鉄${X_TICKETS.tube}・黒チケット・2倍移動${X_DOUBLE}・ヘリ${X_HELI}）も有限。切符が尽きた乗り物には乗れません。動けなくなると怪盗Xの負け、刑事が全員動けなくなると怪盗Xの勝ち。</li>''')

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

# ---------------- 画面を広く使う：地図は画面いっぱい、最大に縮小しても横は半分くらい。横スクロールで追いかける ----------------
sub("""    V.s = Math.min(3, Math.max(V.fit * 0.85, V.s));
    const mw = W * V.s, mh = H * V.s, pad = 80;
    V.tx = mw + pad * 2 <= w ? (w - mw) / 2 : Math.min(pad, Math.max(w - mw - pad, V.tx));
    const top = hudTop();
    V.ty = mh + top + 40 <= h ? top + (h - top - mh) / 2 : Math.min(top + 20, Math.max(h - mh - 60, V.ty));""",
"""    V.s = Math.min(3, Math.max(V.fit, V.s));
    const mw = W * V.s, mh = H * V.s;
    // 地図の端が画面の内側に入らないようにする（上だけは画面上部の表示の下まで下げられる）
    // 四隅の表示の下に隠れた駅も引き出せるよう、端から少し余分にずらせる
    const padX = Math.min(w * 0.3, 220), padB = Math.min(h * 0.3, 190);
    V.tx = Math.min(padX, Math.max(w - mw - padX, V.tx));
    V.ty = Math.min(hudTop() + 10, Math.max(h - mh - padB, V.ty));""")
sub("""    V.fit = Math.min(w / W, (h - top - 20) / H);
    const s = V.fit * 1.02, tx = (w - W * s) / 2, ty = top + (h - top - H * s) / 2;
    animate ? animateView(s, tx, ty) : setView(s, tx, ty);""",
"""    V.fit = minScale();
    // いちばん引いた表示で、いま動く駒のあたりを真ん中に
    const G = A.G;
    let fx = W / 2, fy = H / 2;
    if (G && !G.over) {
      const pos = G.turn === "x" ? (xVisible() ? A.sec.pos : G.lastSeen ? G.lastSeen.pos : null) : G.det[G.turn].pos;
      if (pos !== null && pos !== undefined) [fx, fy] = P(pos);
    }
    const s = V.fit, tx = w / 2 - fx * s, ty = (top + h) / 2 - fy * s;
    animate ? animateView(s, tx, ty) : setView(s, tx, ty);""")
sub("""  function fitView(animate = true) {""", """  // いちばん引いたときの倍率：横は地図の半分くらいが見え、縦は画面いっぱい
  function minScale() {
    const { w, h } = vpSize();
    return Math.max(w / (W * 0.5), h / H);
  }
  function fitView(animate = true) {""")
sub("""window.addEventListener("resize", () => { const { w, h } = vpSize(); V.fit = Math.min(w / W, (h - hudTop() - 20) / H); clampView(); applyView(); });""",
    """window.addEventListener("resize", () => { V.fit = minScale(); clampView(); applyView(); });""")
sub("V.fit * 0.85", "V.fit", count=0)
# 駒が動いたら、画面の外へ出ないように追いかける
sub("""        apply(() => { landed = applyD(G, k, m.to, m.type, A.sec); });
        if (m.type === "heli") heliNote(k, from, landed);
        step();
      }, AI_DELAY);""", """        apply(() => { landed = applyD(G, k, m.to, m.type, A.sec); });
        if (m.type === "heli") heliNote(k, from, landed);
                step();
      }, AI_DELAY);""")
sub("""    if (A.role === "pass" && !A.G.over && A.G.turn !== "x") A.cover = "d";
    step();""", """    if (A.role === "pass" && !A.G.over && A.G.turn !== "x") A.cover = "d";
    if (xVisible()) ensureVisible(landed);
    step();""")
sub("""    apply(() => { landed = applyD(A.G, k, to, type, A.sec); });
    if (type === "heli") heliNote(k, from, landed);
    step();""", """    apply(() => { landed = applyD(A.G, k, to, type, A.sec); });
    if (type === "heli") heliNote(k, from, landed);
        step();""")
sub('aria-label="全体を表示"', 'aria-label="いちばん引いて表示"')

# 駒へ移動するときは、いまの拡大率のまま（勝手に拡大しない）
sub("function centerOn(i, s = Math.max(V.s, 0.95)) {", "function centerOn(i, s = V.s) {")

# ---------------- プレイヤー視点に固定：画面は自分の駒を中心に動かない。見えるのは自分のまわりだけ ----------------
sub("""  // いちばん引いたときの倍率：""", """  // 画面は自分の駒（パス&プレイでは手番の人の駒）を中心に固定する。ドラッグや拡大縮小はしない
  const LOCK = false;   // true にすると画面を自分の駒に固定（いまはドラッグで自由にスクロール）
  let lockedOn = null;
  function viewAnchor() {
    const G = A.G;
    if (!G || !A.sec) return null;
    if (A.role === "x") return A.sec.pos;
    if (A.role === "d") return G.det[ME_DET].pos;
    if (A.cover === "x-open") return A.sec.pos;
    return G.det[typeof G.turn === "number" ? G.turn : 0].pos;
  }
  function lockView(animate = true) {
    const pos = viewAnchor();
    if (pos === null || pos === undefined) return;
    lockedOn = pos;
    const { w, h } = vpSize();
    const [x, y] = P(pos);
    const s = V.fit = minScale();
    const tx = w / 2 - x * s, ty = (hudTop() + h) / 2 - y * s;
    animate ? animateView(s, tx, ty, 520) : setView(s, tx, ty);
  }
  // いちばん引いたときの倍率：""")
sub("""  function fitView(animate = true) {
    const { w, h } = vpSize();""", """  function fitView(animate = true) {
    if (LOCK && A.G) return lockView(animate);
    const { w, h } = vpSize();""")
sub("""  function fitStations(list) {
""", """  function fitStations(list) {
    if (LOCK) return;
""")
sub("""  function ensureVisible(i) {
""", """  function ensureVisible(i) {
    if (LOCK) return;
""")
# 自分の番の始めは、駒が画面の端寄りなら真ん中へ（行き先の駅まで見えるように）
sub("""  function ensureVisible(i) {
""", """  function focusOwn(i) {
    const { w, h } = vpSize();
    const [, x, y] = STATIONS[i];
    const sx = x * V.s + V.tx, sy = y * V.s + V.ty, top = hudTop();
    if (sx < w * 0.28 || sx > w * 0.72 || sy < top + (h - top) * 0.22 || sy > h - (h - top) * 0.28) centerOn(i, V.s);
  }
  function ensureVisible(i) {
""")
sub("""  function focusTurn() {
    const G = A.G;
    if (!G) return;""", """  function focusTurn() {
    const G = A.G;
    if (!G) return;
    if (LOCK) return lockView();""")
sub("""      if (gesture.moved > 6) { mapEl.classList.add("dragging"); setView(V.s, gesture.tx + dx, gesture.ty + dy); }
    } else if (gesture.type === "pinch" && ptrs.size >= 2) {""", """      if (gesture.moved > 6 && !LOCK) { mapEl.classList.add("dragging"); setView(V.s, gesture.tx + dx, gesture.ty + dy); }
    } else if (gesture.type === "pinch" && ptrs.size >= 2 && !LOCK) {""")
sub("""  mapEl.addEventListener("wheel", e => {
    e.preventDefault();
""", """  mapEl.addEventListener("wheel", e => {
    e.preventDefault();
    if (LOCK) return;
""")
sub("""  mapEl.addEventListener("dblclick", e => {
""", """  mapEl.addEventListener("dblclick", e => {
    if (LOCK) return;
""")
sub("""window.addEventListener("resize", () => { V.fit = minScale(); clampView(); applyView(); });""",
    """window.addEventListener("resize", () => { V.fit = minScale(); clampView(); applyView(); if (LOCK && A.G && A.screen === "game") lockView(false); });""")
# 自分の駒が動いたら（パス&プレイで手番が替わったら）画面をそこへ移す
sub("""  function render() {
""", """  function render() {
    if (LOCK && A.G && A.screen === "game" && viewAnchor() !== lockedOn) lockView();
""")
# ボタン：拡大・縮小・全体表示はなし。中心ボタンは「自分の駒へ」
sub("""      case "zoomIn": return zoomAt(1.5, w / 2, h / 2);
      case "zoomOut": return zoomAt(1 / 1.5, w / 2, h / 2);""", """      case "zoomIn": if (LOCK) return; return zoomAt(1.5, w / 2, h / 2);
      case "zoomOut": if (LOCK) return; return zoomAt(1 / 1.5, w / 2, h / 2);
      case "tapStation": return onStationTap(Number(b.dataset.pos));""")
sub("""      case "focusX": {""", """      case "focusX": if (LOCK) return;
      {""")
sub("""      case "focusD": return A.G && centerOn""", """      case "focusD": if (LOCK) return; return A.G && centerOn""")
sub("""      case "focusPos": return centerOn(Number(b.dataset.pos));""", """      case "focusPos": if (LOCK) { const p = Number(b.dataset.pos); toast(`${NO(p)} ${NAME(p)}`); return; } return centerOn(Number(b.dataset.pos));""")
sub('''aria-label="手番のコマへ移動"''', '''aria-label="自分の駒へ戻る"''')
sub("""  .side .iconbtn:active""", """  .edge-arrow.dest .dest-no { position: relative; display: grid; place-items: center; width: 34px; height: 34px; border-radius: 50%; background: #FFF6D8; color: #1A140C; font-weight: 900; font-size: 13px; border: 3px solid #3B2C1E; }
  .side .iconbtn:active""")
# 画面の外にある行き先（とカードの対象の駅）は、縁の矢印から選べる
sub("""    if (mateActive(G) && !G.over) t.push({ key: "m" + G.mate.pos, kind: "m", k: 0, pos: G.mate.pos });
    return t;""", """    if (mateActive(G) && !G.over) t.push({ key: "m" + G.mate.pos, kind: "m", k: 0, pos: G.mate.pos });
    if (LOCK && humanTurn()) {
      const moves = G.turn === "x" ? xMoves(G, A.sec) : detMoves(G, G.turn);
      for (const to of new Set(moves.filter(m => m.to >= 0).map(m => m.to))) t.push({ key: "go" + to, kind: "dest", k: 0, pos: to });
    }
    if (LOCK && A.pendingCard && A.pendingCard.stage === "target") for (const p of A.pendingCard.opts) t.push({ key: "go" + p, kind: "dest", k: 0, pos: p });
    return t;""")
sub("""    host.innerHTML = edgeTargets().map(t => {
      const color""", """    host.innerHTML = edgeTargets().map(t => {
      if (t.kind === "dest") return `<button class="edge-arrow dest" data-act="tapStation" data-pos="${t.pos}" data-key="${t.key}" aria-label="行き先 ${NO(t.pos)} ${NAME(t.pos)}" hidden>
        <svg class="dir" viewBox="-28 -28 56 56"><g class="rot"><circle r="22" fill="#E3B341" stroke="#3B2C1E" stroke-width="3"></circle><path d="M22,-10 L36,0 L22,10 Z" fill="#E3B341" stroke="#3B2C1E" stroke-width="2.5" stroke-linejoin="round"></path></g></svg>
        <span class="dest-no">${NO(t.pos)}</span></button>`;
      const color""")

# 背景画像は盤面の大きさに合わせる（ロンドン版は 3000×1900 の決め打ち）
sub('''<image id="bgimg" x="0" y="0" width="3000" height="1900" preserveAspectRatio="none"></image>''',
    f'''<image id="bgimg" x="0" y="0" width="{B["W"]}" height="{B["H"]}" preserveAspectRatio="none"></image>''')
# 固定の拡大率では駅名をいつも出す
sub("""  #map.z1 .stn-label:not(.hot) { display: none; }""", """  #map.z1 .stn-label:not(.hot) { display: inline; }""")

# 全体地図：ボタンで盤面全体を表示し、もう一度押すと自分の視点に戻る
sub("""    <button class="iconbtn" id="hintBtn" data-act="hint\"""", """    <button class="iconbtn" id="overviewBtn" data-act="overview" aria-pressed="false" aria-label="全体地図"><svg viewBox="0 0 24 24"><path d="M3 6l6-2 6 2 6-2v14l-6 2-6-2-6 2z"></path><path d="M9 4v14M15 6v14"></path></svg></button>
    <button class="iconbtn" id="hintBtn" data-act="hint\"""")
sub("""  function clampView() {
""", """  function clampView() {
    if (A.overview) return;   // 全体地図のあいだは自由な大きさ
""")
sub("""    if (LOCK && A.G && A.screen === "game" && viewAnchor() !== lockedOn) lockView();""",
    """    if (LOCK && A.G && A.screen === "game" && !A.overview && viewAnchor() !== lockedOn) lockView();
    const ob = $("overviewBtn");
    if (ob) ob.setAttribute("aria-pressed", String(!!A.overview));
    // 決着したら、隠した上部の表示を出して「結果」ボタンを押せるようにする
    if (A.G && A.G.over && document.body.classList.contains("hud-hidden")) { document.body.classList.remove("hud-hidden"); const pt = $("pullTab"); if (pt) pt.setAttribute("aria-expanded", "true"); }
    // 自由スクロールでも、自分の番になったら自分の駒が画面に入るようにする
    if (!LOCK && A.G && A.screen === "game" && !A.G.over) {
      const fk = humanTurn() ? String(A.G.turn) : null;
      if (fk !== A.focusKey) {
        A.focusKey = fk;
        // 直前の駒の追いかけ（同じ処理の中で動く）が終わってから、自分の駒へ寄せる
        if (fk !== null) setTimeout(() => { if (A.G && !A.overview && humanTurn() && String(A.G.turn) === fk) focusOwn(A.G.turn === "x" ? A.sec.pos : A.G.det[A.G.turn].pos); }, 0);
      }
    }""")
sub("""      case "hint": A.hints = !A.hints; render(); return;""", """      case "hint": A.hints = !A.hints; render(); return;
      case "overview": {
        if (!A.G) return;
        A.overview = !A.overview;
        if (A.overview) {
          // 盤面全体を、上の表示の下に収める
          const top = hudTop(), s = Math.min(w / W, (h - top - 16) / H);
          animateView(s, (w - W * s) / 2, top + (h - top - H * s) / 2, 420);
          toast("全体地図：もう一度押すと自分の視点に戻ります");
        } else lockView();
        render();
        return;
      }""")
# 全体地図のまま手番が進んだら、自分の視点に戻す
sub("""  function lockView(animate = true) {
""", """  function lockView(animate = true) {
    A.overview = false;
""")

# ---------------- 視界ルール：怪盗Xは刑事の視界（円）に入ったら見つかる ----------------
from sight_rule import patches as sight_patches
SIGHT = 350
for a_, b_ in sight_patches(SIGHT):
    sub(a_, b_)
# 刑事の視界を地図に描く（怪盗Xも刑事側も見える）
sub("""    if (!showX && A.hints && !G.over) for (const p of G.possible) {""", """    if (!G.over) for (const d of G.det) { const [x, y] = P(d.pos); el("circle", { cx: x, cy: y, r: SIGHT, class: "sight" }, gP); }
    if (!showX && A.hints && !G.over) for (const p of G.possible) {""")
sub("""  .poss { fill: var(--xrim); opacity: 0.28; }""", """  .poss { fill: var(--xrim); opacity: 0.28; }
  .sight { fill: rgba(80, 140, 255, 0.07); stroke: rgba(60, 110, 230, 0.55); stroke-width: 4; stroke-dasharray: 16 12; }""")
sub("""<small class="nx">${G.over ? "ゲーム終了" : nx ? `次の出現 ${nx}手目` : "出現なし"}</small>""",
    """<small class="nx">${G.over ? "ゲーム終了" : "刑事の視界に入ると見つかる"}</small>""")
rsub(r'        <li>怪盗Xの居場所は秘密。.*?</li>', """        <li>怪盗Xの居場所は秘密。ただし <b>刑事の視界</b>（刑事のまわりの青い点線の円）に入ると、その場で姿が見えて <b>発見</b> されます。怪盗Xが自分で視界に入っても、刑事が近づいて視界に入っても同じです。視界の中の駅には怪盗Xはいないので、候補から外れます。刑事にわかるのは、移動記録に残る <b>切符の種類</b> と、見つかった場所だけです。</li>""")
rsub(r'<span style="color:#E5484D;font-weight:900">赤い丸と赤い枠</span>のマスは怪盗Xが姿を現す手で、現れた駅の番号が入ります。', """駅の番号が入っているマスは、その手で怪盗Xが見つかった駅です。""")

# ---------------- 無線：見た刑事だけが乗り物を知り、仲間に無線で知らせる ----------------
# 乗り物がわからない手は「？」
sub("""    pass:  { name: "パス", en: "Pass", short: "休" },""", """    pass:  { name: "パス", en: "Pass", short: "休" },
    unk:   { name: "不明", en: "Unknown", short: "？" },""")
sub("""  .slot.heli { background: var(--heli); }""", """  .slot.heli { background: var(--heli); }
  .slot.unk { background: #4A4540; color: #D8CDBA; }""")
sub("""  function pushFeed(n, text, hot = false) {""", """  // 刑事側から見た乗り物（誰も見ていない手は「？」）
  const seenT = e => (e.k === 0 && !xVisible() && !(A.G && A.G.over)) ? "unk" : e.t;
  function pushFeed(n, text, hot = false) {""")
sub("""      if (e) cls.push(e.t);""", """      if (e) cls.push(seenT(e));""")
sub("""${e ? "：" + TYPE[e.t].name : ""}""", """${e ? "：" + TYPE[seenT(e)].name : ""}""")
sub("""<span class="n">${i + 1}</span>${e ? TYPE[e.t].short : ""}""", """<span class="n">${i + 1}</span>${e ? TYPE[seenT(e)].short : ""}""")
sub("""${G.xt ? ["taxi", "bus", "tube"].map(""", """${G.xt && (xVisible() || G.over) ? ["taxi", "bus", "tube"].map(""")
sub("""      let s = e.t === "pass" ? "怪盗Xはパス（その場にとどまった）" : `怪盗Xが ${TYPE[e.t].name} で移動`;""",
    """      let s = e.t === "pass" ? "怪盗Xはパス（その場にとどまった）" : seenT(e) === "unk" ? "怪盗Xが移動（誰にも見られていない）" : `怪盗Xが ${TYPE[e.t].name} で移動`;
      // 仲間の刑事からの無線（刑事側で遊んでいるときだけ）
      if (A.role !== "x" && e.t !== "pass") {
        const from = A.sec.path[i], to = A.sec.path[i + 1];
        if (e.k && e.w >= 0) {
          const how = e.t === "black" ? "乗り物は見えなかった" : `${TYPE[e.t].name}`;
          if (e.p !== null) radio(e.w, `${NO(to)} ${NAME(to)} で見つけた！ ${e.t === "black" ? "何かに乗って来た" : how + "で来た"}`, "見つけた！");
          else radio(e.w, `${NO(from)} ${NAME(from)} から ${e.t === "black" ? "何かに乗って消えた" : how + "で出ていった"}`, "逃げたぞ！");
        } else if (Math.random() < 0.35) {
          const k = G.det.map((_, j) => j).filter(j => A.role !== "d" || j !== ME_DET)[Math.floor(Math.random() * (G.det.length - (A.role === "d" ? 1 : 0)))];
          if (k !== undefined) radio(k, pick(["こっちの視界にはいない", "この辺りは異常なし", "見当たらない。別の方を探す"]), "");
        }
      }""")
sub("""        banner("発見！", `刑事が怪盗Xの居場所をつかんだ（${NAME(G.possible[0])}）`, "", 1);""",
    """        banner("発見！", `刑事が怪盗Xの居場所をつかんだ（${NAME(G.possible[0])}）`, "", 1);
        if (A.role !== "x") radio(nearestDet(G.possible), `${NO(G.possible[0])} ${NAME(G.possible[0])} にいる！`, "");""")
# 無線の欄
sub("""  <div class="panel drawer" id="drawer" hidden>""", """  <div class="panel radio" id="radio" hidden aria-live="polite"></div>
  <div class="panel drawer" id="drawer" hidden>""")
sub("""  .toast {""", """  .radio { position: absolute; z-index: 6; right: 10px; bottom: 10px; width: min(380px, calc(100% - 20px)); padding: 8px 10px; display: flex; flex-direction: column; gap: 5px; }
  .radio .rh { font-size: 11px; font-weight: 900; letter-spacing: .12em; color: var(--gold); }
  .radio .rm { display: flex; align-items: center; gap: 8px; font-size: 13px; line-height: 1.35; }
  .radio .rm .portrait { width: 28px; height: 28px; flex: none; }
  .radio .rm b { white-space: nowrap; }
  .radio .rm.old { opacity: .6; }
  @media (max-width: 640px) { .radio { right: 60px; left: 8px; width: auto; bottom: 120px; } .radio .rm.old { display: none; } }
  .toast {""")
sub("""  function render() {
""", """  // 無線：仲間の刑事からの報告（画面右下に最新3件）
  function radio(k, text, bubble) {
    const G = A.G;
    if (!G || !G.det[k]) return;
    const me = A.role === "d" && k === ME_DET;
    A.radio = [{ k, text, me }, ...(A.radio || [])].slice(0, 12);
    pushFeed(G.xLog.length, `無線｜${me ? "あなた" : dName(k)}：${text}`, true);
    if (bubble) say(k, bubble, "hot", 2200);
  }
  function renderRadio() {
    const el_ = $("radio");
    const on = A.G && A.screen === "game" && A.role !== "x" && (A.radio || []).length;
    el_.hidden = !on;
    if (!on) return;
    el_.innerHTML = `<div class="rh">無線</div>` + A.radio.slice(0, 3).map((m, i) =>
      `<div class="rm ${i ? "old" : ""}">${portrait("d", m.k, "sm")}<span><b>${m.me ? "あなた" : dName(m.k)}</b>：${esc(m.text)}</span></div>`).join("");
  }
  function render() {
    renderRadio();
""")
sub("""    Object.assign(A, { role, G, sec, feed: [], sel: null, useDouble: false, screen: "game", busy: false });""",
    """    Object.assign(A, { role, G, sec, feed: [], radio: [], sel: null, useDouble: false, screen: "game", busy: false });""")
rsub(r'(        <li>怪盗Xの居場所は秘密。.*?</li>)', r"""\1
        <li><b>無線</b>：怪盗Xが乗った乗り物は、<b>乗った駅か降りた駅が刑事の視界に入っていたときだけ</b>わかります。誰も見ていない移動は移動記録に「？」と残ります。仲間の刑事は見たことを無線で知らせてくれます（右下の「無線」欄とログ）。無線の報告をつなぎ合わせて、怪盗Xの居場所を突き止めましょう。怪盗Xの切符の残り枚数も刑事には見えません。</li>""")

# 不具合の修正：決着の0.9秒後に結果画面へ切り替えるタイマーが、次のゲームを始めた後に動くと、画面が「結果」のまま止まって操作できなくなる
sub("""    setTimeout(() => { A.screen = "result"; renderScreen(); }, 900);""",
    """    const endedG = G;
    setTimeout(() => { if (A.G === endedG && A.screen === "game") { A.screen = "result"; renderScreen(); } }, 900);""")
# 候補が空のときに「発見」と扱わない（空の候補の場所を描こうとして止まる不具合の予防）
sub("""    if (n <= 1) return { level: "found",""", """    if (n === 1) return { level: "found",""")

# ---------------- 会話は駒の吹き出しで：長いセリフは折り返す。画面の外の仲間は縁の矢印に吹き出しを出す ----------------
sub("""        const w = s.text.length * 26 + 30;
        tk.querySelector(".tb").setAttribute("d", `M${-w / 2},-54 h${w} a10,10 0 0 1 10,10 v30 a10,10 0 0 1 -10,10 h${-w / 2 + 14} l-14,14 l-4,-14 h${-w / 2 + 4} a10,10 0 0 1 -10,-10 v-30 a10,10 0 0 1 10,-10 Z`);
        tk.querySelector("text").textContent = s.text;""",
"""        const lines = wrapTalk(s.text);
        const w = Math.max(...lines.map(l => l.length)) * 26 + 30, hgt = lines.length * 32 + 18;
        tk.querySelector(".tb").setAttribute("d", `M${-w / 2},${-4 - hgt} h${w} a10,10 0 0 1 10,10 v${hgt - 20} a10,10 0 0 1 -10,10 h${-w / 2 + 14} l-14,14 l-4,-14 h${-w / 2 + 4} a10,10 0 0 1 -10,-10 v${-(hgt - 20)} a10,10 0 0 1 10,-10 Z`);
        const tx = tk.querySelector("text");
        tx.textContent = "";
        tx.setAttribute("y", String(-4 - hgt + 34));
        lines.forEach((l, i) => { const ts = el("tspan", { x: 0, dy: i ? 32 : 0 }, tx); ts.textContent = l; });""")
sub("""  function say(k, text, kind = "", ms = 2400) {
    if (k < 0 || !A.G || !A.G.det[k]) return;
    SPEECH.set(k, { text, kind, until: Date.now() + ms });
    updateTalk();
    setTimeout(updateTalk, ms + 40);
  }""", """  // 吹き出しのセリフを、句読点や空白の近くで1行12文字くらいに折り返す
  function wrapTalk(text) {
    const out = [];
    let rest = text;
    while (rest.length > 13) {
      let cut = -1;
      for (let i = 12; i >= 6; i--) if ("、。！？ ）".includes(rest[i - 1])) { cut = i; break; }
      if (cut < 0) cut = 12;
      out.push(rest.slice(0, cut).trim()); rest = rest.slice(cut).trim();
    }
    if (rest) out.push(rest);
    return out.slice(0, 3);
  }
  function say(k, text, kind = "", ms = 2400) {
    if (k < 0 || !A.G || !A.G.det[k]) return;
    SPEECH.set(k, { text, kind, until: Date.now() + ms });
    updateTalk();
    renderEdge();
    setTimeout(() => { updateTalk(); renderEdge(); }, ms + 40);
  }""")
# 無線の報告は、話した刑事の吹き出しに全文を出す
sub("""    if (bubble) say(k, bubble, "hot", 2200);""", """    say(k, text, bubble ? "hot" : "", 4800);""")
# 画面の外にいる仲間の矢印にもセリフを出す
sub("""        ${portrait(t.kind, t.k)}${dist}</button>`;""", """        ${portrait(t.kind, t.k)}${dist}${t.kind === "d" && SPEECH.has(t.k) && SPEECH.get(t.k).until > Date.now() ? `<span class="ea-say">${esc(SPEECH.get(t.k).text)}</span>` : ""}</button>`;""")
sub("""  .edge-arrow .ea-d.hot {""", """  .edge-arrow .ea-say { position: absolute; bottom: calc(100% + 6px); left: 50%; transform: translateX(-50%); width: max-content; max-width: 190px;
    padding: 5px 9px; border-radius: 10px; background: #FBF5E4; color: #1A140C; border: 2px solid #3B2C1E; font-size: 12px; font-weight: 700; line-height: 1.35; text-align: left; white-space: normal; box-shadow: 0 4px 10px rgba(0,0,0,.35); }
  .edge-arrow .ea-d.hot {""")
# 右下の無線欄はやめ、吹き出しとログにする
sub("""    const on = A.G && A.screen === "game" && A.role !== "x" && (A.radio || []).length;""", """    const on = false;   // 会話は駒の吹き出しで見せる（全部はログに残る）""")

# 縁の矢印の吹き出しが画面の外にはみ出さないように、端では内側へ寄せる
sub("""      b.style.transform = `translate(${ax.toFixed(1)}px, ${ay.toFixed(1)}px)`;""", """      b.style.transform = `translate(${ax.toFixed(1)}px, ${ay.toFixed(1)}px)`;
      const say_ = b.querySelector(".ea-say");
      if (say_) {
        say_.style.left = ax < 120 ? "0" : ax > r.width - 120 ? "auto" : "50%";
        say_.style.right = ax > r.width - 120 ? "0" : "auto";
        say_.style.transform = ax < 120 || ax > r.width - 120 ? "none" : "translateX(-50%)";
        if (ay < top + 60) { say_.style.bottom = "auto"; say_.style.top = "calc(100% + 16px)"; }
      }""")

# ---------------- ドット絵風の盤面（tools/pixel_board.js）：背景と道・線路・駅の描き方を差し替える ----------------
a_ = out.index("  async function renderBackground() {"); b_ = out.index("  // 駒（ボードゲームのポーン）")
out = out[:a_] + open(os.path.join(HERE, "pixel_board.js"), encoding="utf-8").read() + out[b_:]
sub("""family=Zen+Old+Mincho:wght@700;900&display=swap">""", """family=Zen+Old+Mincho:wght@700;900&family=DotGothic16&display=swap">""")
sub("""  .stn-num { font-family: "Zen Kaku Gothic New", sans-serif; font-weight: 900; font-size: 15px; fill: var(--map-ink);""",
    """  .stn-num { font-family: "DotGothic16", "Zen Kaku Gothic New", sans-serif; font-weight: 400; font-size: 16px; fill: #1C1C1C;""")
sub("""    font-family: "Zen Kaku Gothic New", sans-serif; font-weight: 900; font-size: 17px; fill: var(--map-ink);
    paint-order: stroke; stroke: var(--paper); stroke-width: 6px; stroke-linejoin: round;""",
    """    font-family: "DotGothic16", "Zen Kaku Gothic New", sans-serif; font-weight: 400; font-size: 21px; fill: #141414;
    paint-order: stroke; stroke: #F4F4F0; stroke-width: 6px; stroke-linejoin: miter;""")
sub("""  #map { position: absolute; inset: 0; width: 100%; height: 100%; display: block; touch-action: none; background: #2A2016; cursor: grab; }""",
    """  #map { position: absolute; inset: 0; width: 100%; height: 100%; display: block; touch-action: none; background: #B9B9B4; cursor: grab; }
  #bgimg { image-rendering: pixelated; image-rendering: crisp-edges; }
  .ln { fill: none; stroke-linecap: round; stroke-linejoin: round; }
  .gap { stroke: #C6C6C1; }
  .taxi-ln { stroke: #D9A11A; }
  .bus-ln { stroke: var(--bus); }
  .bus-dash { stroke: #DDF3E4; stroke-width: 2.5; stroke-dasharray: 10 10; }
  .tube-ln { stroke: var(--tube); }
  .tube-dash { stroke: #F6D2D0; stroke-width: 4; stroke-dasharray: 12 8; }
  .deck { fill: #C6C6C1; stroke: none; }
  .deck-rail { fill: none; stroke: #4A4A46; stroke-width: 5; stroke-linecap: square; }
  .hport { fill: #2E2E2E; stroke: #FFFFFF; stroke-width: 4; }
  .hport-ring { fill: none; stroke: #F2C230; stroke-width: 3; }
  .hport-h { font-family: "DotGothic16", sans-serif; font-size: 20px; fill: #FFFFFF; text-anchor: middle; pointer-events: none; }
  .st-shadow { fill: rgba(0, 0, 0, 0.28); }
  .st-side { fill: #9A9A96; stroke: #2E2E2E; stroke-width: 2.5; }
  .st-side.sub { fill: #6E1520; }
  .st-top { fill: #FAFAF7; stroke: #2E2E2E; stroke-width: 2.5; }
  .st-top.sub { fill: #C3242F; }
  .st-hi { fill: rgba(255, 255, 255, 0.7); }
  .st-tag { stroke: #1C1C1C; stroke-width: 1.5; }
  .st-tag.bus { fill: #1F8A4C; }
  .st-tag.boat { fill: #2F7FB0; }
  .stn-num.on-sub { fill: #FFFFFF; }""")

# ---------------- 2倍移動をはっきり知らせる：バナー・刑事の吹き出し・記録欄の強調 ----------------
sub("""      if (e.d === 1) s = "怪盗Xが2倍移動！ " + s;""", """      if (e.d === 1) {
        s = "怪盗Xが2倍移動！ " + s;
        banner("2倍移動！", A.role === "x" ? "続けてもう1駅動けます" : "怪盗Xが続けてもう1駅動く", "", 2);
        if (A.role !== "x") say(Math.floor(Math.random() * G.det.length), "2回続けて動くぞ！", "", 3200);
      }""")
sub("""      if (CARD_TURNS.includes(i + 1)) cls.push("cardturn");
      if (!G.over && i === G.xLog.length) cls.push("now");""", """      if (CARD_TURNS.includes(i + 1)) cls.push("cardturn");
      if (e && e.d) cls.push("dx");
      if (!G.over && i === G.xLog.length) cls.push("now");""")
sub("""  .slot .dbl { position: absolute; bottom: 2px; right: 3px; font-size: 8px; }""",
    """  .slot .dbl { position: absolute; top: 2px; right: 2px; font-size: 10px; font-weight: 900; line-height: 1; padding: 2px 3px; border-radius: 5px; background: #E8C872; color: #1A140C; box-shadow: 0 1px 0 rgba(0,0,0,.4); }
  .slot.dx { box-shadow: inset 0 0 0 3px #E8C872; }""")

# 同じ重さのお知らせが重なったら、上書きせず順番に出す（2倍移動と目撃が同時のときなど）
sub("""    if (Date.now() < bannerUntil && pri < bannerPri) return;""", """    if (Date.now() < bannerUntil && pri < bannerPri) return;
    if (Date.now() < bannerUntil && pri === bannerPri) { setTimeout(() => banner(title, sub, color, pri), bannerUntil - Date.now() + 80); return; }""")

# ---------------- 横向きの携帯：上・右・左下の表示を小さくして地図を広く ----------------
sub("""  @media (prefers-reduced-motion: reduce) { .top { transition: none; } }""", """  @media (prefers-reduced-motion: reduce) { .top { transition: none; } }
  @media (max-height: 520px) and (orientation: landscape) { .hud.top, .hud.side, .handbar { zoom: 0.62; } }
  /* 携帯：画面の端の駒アイコンを小さく・半透明にして、下の駅を見やすく */
  @media (max-width: 760px), (max-height: 520px) { .edge-arrow { opacity: 0.82; } .edge-arrow:active { opacity: 1; } .edge-arrow svg.dir { transform: scale(0.72); } .edge-arrow .portrait, .edge-arrow .portrait img { width: 27px !important; height: 27px !important; } .edge-arrow .ea-d { font-size: 9px; bottom: -6px; padding: 0 4px; } }
  @media (max-width: 760px) { .hud.side, .handbar { zoom: 0.8; } }""")

# ---------------- 残っていないかの確認 ----------------
for word in ["テムズ", "ロンドン", "london-map", "霧の"]:
    assert word not in out, f"leftover: {word}"
dst = os.path.join(HERE, "..", "index.html")
open(dst, "w", encoding="utf-8").write(out)
print("wrote", os.path.normpath(dst), len(out), "bytes")
