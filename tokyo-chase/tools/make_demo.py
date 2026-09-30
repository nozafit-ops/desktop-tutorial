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
  const MONO = {json.dumps(B.get("monoEdges", []))};
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
  const X_TICKETS = { taxi: 22, bus: 15, tube: 7, boat: 5, mono: 6 };
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
  const AUTO_CAM = false;   // true にすると駒の動きに合わせて画面が自動で動く（いまは自分でドラッグしたときだけ動く）
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
    if (LOCK || !AUTO_CAM) return;
""")
# 自分の番の始めは、駒が画面の端寄りなら真ん中へ（行き先の駅まで見えるように）
sub("""  function ensureVisible(i) {
""", """  function focusOwn(i) {
    if (!AUTO_CAM) return;
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
out = out[:a_] + open(os.path.join(HERE, "pixel_board.js"), encoding="utf-8").read() + open(os.path.join(HERE, "pixel_cards.js"), encoding="utf-8").read() + open(os.path.join(HERE, "layout.js"), encoding="utf-8").read() + out[b_:]
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

# ---------------- 「2倍移動」は「2回移動」と呼ぶ ----------------
sub("2倍移動", "2回移動", count=0)
sub('"dbl">2×</span>', '"dbl">2回</span>')
sub('">2×${G.dbl}', '">2回×${G.dbl}')
sub("「2×」", "「2回」", count=0)

# ---------------- 30手：手数・カードの手・怪盗Xの切符を増やす（sim.js MOVES=30 で調整） ----------------
sub("const MAX_MOVES = 21;", "const MAX_MOVES = 30;")
sub("const CARD_TURNS = [5, 10, 17];", "const CARD_TURNS = [5, 12, 20];")
sub("const CARD_LAST = 20;   // 手札のカードは20手目まで好きな時に使える", "const CARD_LAST = 28;   // 手札のカードは28手目まで好きな時に使える")
sub("const X_DOUBLE = 4;", "const X_DOUBLE = 5;")
sub("black: detCount,", "black: X_BLACK,")
sub("const X_DOUBLE = 5;", "const X_DOUBLE = 5;\n  const X_BLACK = 10;    // 黒チケットの枚数（水上バスにもこれで乗る）")
sub("<b>黒チケット</b>（乗り物を隠す。刑事の人数と同じ枚数）", "<b>黒チケット</b> ${X_BLACK}枚（乗り物を隠す。水上バスにもこれで乗る）")
# 水上バスで行ける駅では、黒チケットの札に「水上バス」と出す
sub("""<span class="ja">${TYPE[t].name}${t === "black" ? "（乗り物を隠す）" : ""}</span>""",
    """<span class="ja">${t === "black" && ADJ[A.sec.pos].some(e => e.to === to && e.type === "boat") ? "水上バス（黒チケット・乗り物は隠れる）" : TYPE[t].name + (t === "black" ? "（乗り物を隠す）" : "")}</span>""")

# ---------------- 切符をドット絵のカードに（tools/pixel_cards.js の pxCard） ----------------
sub("""tickets = `<button class="ticket heli" data-act="ticket" data-type="heli"><span class="en">Helicopter</span><span class="ja">ほかのヘリポートのどこかへ着陸（ランダム）</span><span class="cnt">${cnt}</span></button>`;""",
    """tickets = pxCard("heli", cnt, "heli");""")
sub("""`<button class="ticket ${t}" data-act="ticket" data-type="${t}"><span class="en">${TYPE[t].en}</span><span class="ja">${t === "black" && ADJ[A.sec.pos].some(e => e.to === to && e.type === "boat") ? "水上バス（黒チケット・乗り物は隠れる）" : TYPE[t].name + (t === "black" ? "（乗り物を隠す）" : "")}</span><span class="cnt">${t === "black" ? G.black : G.xt && G.xt[t] !== undefined ? G.xt[t] : ""}</span></button>`).join("");""",
    """pxCard(t === "black" && ADJ[A.sec.pos].some(e => e.to === to && e.type === "boat") ? "boat" : t, t === "black" ? G.black : G.xt && G.xt[t] !== undefined ? G.xt[t] : "", t)).join("");""")
sub("""`<button class="ticket ${t}" data-act="ticket" data-type="${t}"><span class="en">${TYPE[t].en}</span><span class="ja">${TYPE[t].name}</span><span class="cnt">${t === "heli" ? d.t.heli : "∞"}</span></button>`).join("");""",
    """pxCard(t, t === "heli" ? d.t.heli : "∞", t)).join("");""")
sub("""  .tickets { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; }""",
    """  .tickets { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; }
  .tickets:has(.pxcard) { grid-template-columns: repeat(auto-fit, minmax(104px, 150px)); justify-content: center; }
  .tickets .ticket.pxcard { background: #FBF7EA; color: #4F6475; border: 3px solid #C2464F; border-radius: 12px; padding: 6px 7px 7px; gap: 5px; justify-content: flex-start;
    box-shadow: inset 0 0 0 2px #FBF7EA, inset 0 0 0 3px rgba(194,70,79,.35), 0 4px 0 rgba(0,0,0,.35); font-family: "DotGothic16", sans-serif; }
  .ticket.pxcard::before, .ticket.pxcard::after { display: none; }
  .pxcard .pc-top { display: flex; align-items: center; gap: 3px; height: 28px; }
  .pxcard .pc-run { width: 24px; height: 22px; image-rendering: pixelated; }
  .pxcard .pc-no { align-self: flex-start; font-size: 9px; color: #9FB3C2; }
  .pxcard .pc-cnt { margin-left: auto; font-size: 25px; line-height: 1; color: #FFFFFF; text-shadow: 1px 0 0 #7E2A63, -1px 0 0 #7E2A63, 0 1px 0 #7E2A63, 0 -1px 0 #7E2A63, 2px 2px 0 #7E2A63, 3px 3px 0 #7E2A63; }
  .pxcard .pc-type { width: 26px; height: 26px; display: grid; place-items: center; border: 2px solid #7E2A63; border-radius: 3px; color: #fff; font-size: 14px; }
  .pxcard .pc-type.taxi { background: var(--taxi); color: #1A140C; } .pxcard .pc-type.bus { background: var(--bus); } .pxcard .pc-type.tube { background: var(--tube); }
  .pxcard .pc-type.boat { background: var(--ferry); } .pxcard .pc-type.black { background: #1C1830; } .pxcard .pc-type.heli { background: var(--heli); }
  .pxcard .pc-art { width: 100%; aspect-ratio: 3 / 2; image-rendering: pixelated; border-radius: 2px; display: block; }
  .pxcard .pc-bot { display: flex; align-items: stretch; gap: 4px; }
  .pxcard .pc-chase { writing-mode: vertical-rl; transform: rotate(180deg); font-size: 8px; letter-spacing: .05em; background: #4F6475; color: #FBF7EA; padding: 2px 1px; text-align: center; }
  .pxcard .pc-title { font-size: 15px; line-height: 1.05; color: #4F6475; letter-spacing: .02em; }
  .pxcard .pc-ja { font-family: "Zen Kaku Gothic New", sans-serif; font-size: 11px; font-weight: 700; color: #8A5A4A; line-height: 1.3; }
  .ticket.pxcard:active:not(:disabled) { transform: translateY(2px); }""")

# ---------------- 手札カードもドット絵に（tools/pixel_cards.js の pxHandArt） ----------------
sub("""<img src="art/cards/${c}.webp" alt=""><span>${CARD[c].name}</span></button>`""", """<img src="${pxHandArt(c)}" alt=""><span>${CARD[c].name}</span></button>`""")
sub("""<span class="hb-heli"><img src="art/icons/heli.webp" alt=""><b>×${left}</b></span>""", """<span class="hb-heli"><img src="${pxScene("heli")}" alt=""><b>×${left}</b></span>""")
sub("""<img class="gc-art" src="art/cards/${pc.card}.webp" alt="">""", """<img class="gc-art" src="${pxHandArt(pc.card)}" alt="">""")
sub("""`<button class="ticket hand-card ${side}" ${usable ? `data-act="useCard" data-i="${i}"` : "disabled"}><img class="hc-art" src="art/cards/${c}.webp" alt=""><span class="en">${CARD[c].name}</span><span class="ja">${CARD[c].desc}</span></button>`""",
    """`<button class="ticket pxcard hand-card ${side}" ${usable ? `data-act="useCard" data-i="${i}"` : "disabled"}>
          <span class="pc-top"><img class="pc-run" src="${pxRunner()}" alt=""><span class="pc-no">${side === "x" ? "THIEF CARD" : "POLICE CARD"}</span></span>
          <img class="pc-art" src="${pxHandArt(c)}" alt="">
          <span class="pc-bot"><span class="pc-chase">CHASE</span><span class="pc-title">${CARD[c].name}</span></span>
          <span class="pc-ja">${CARD[c].desc}</span></button>`""")
sub("""  .ticket.pxcard:active:not(:disabled) { transform: translateY(2px); }""", """  .ticket.pxcard:active:not(:disabled) { transform: translateY(2px); }
  .tickets .ticket.pxcard.hand-card { background: #FBF7EA; color: #4F6475; min-height: 0; }
  .tickets .ticket.pxcard.hand-card.d { border-color: #2F5FB8; box-shadow: inset 0 0 0 2px #FBF7EA, inset 0 0 0 3px rgba(47,95,184,.35), 0 4px 0 rgba(0,0,0,.35); }
  .pxcard.hand-card .pc-title { font-family: "DotGothic16", sans-serif; font-size: 17px; align-self: center; }
  .pxcard.hand-card .pc-no { align-self: center; font-size: 10px; letter-spacing: .05em; }
  .pxcard.hand-card .pc-ja { font-weight: 500; font-size: 11px; color: #5A4A40; }
  .gc-art, .hb-card img, .hb-card.heli .hb-heli img { image-rendering: pixelated; }
  .gcard.gcard.d, .gcard.gcard.x, .gcard.gcard.miss { background: #FBF7EA; border: 4px solid #2F5FB8; box-shadow: inset 0 0 0 3px #FBF7EA, inset 0 0 0 4px rgba(47,95,184,.35), 0 10px 30px rgba(0,0,0,.5); }
  .gcard.gcard.x { border-color: #C2464F; box-shadow: inset 0 0 0 3px #FBF7EA, inset 0 0 0 4px rgba(194,70,79,.35), 0 10px 30px rgba(0,0,0,.5); }
  .gcard.gcard.miss { border-color: #8A8680; }
  .gcard .gc-kind { font-family: "DotGothic16", sans-serif; color: #9FB3C2; letter-spacing: .15em; }
  .gcard .gc-art { border: 2px solid #4F6475; border-radius: 3px; }
  .gcard .gc-name { font-family: "DotGothic16", sans-serif; font-weight: 400; color: #4F6475; }
  .gcard .gc-desc { color: #5A4A40; }""")

# ---------------- CPUの刑事の性格：追いかけ・先回り・待ち伏せ（tools/persona.py） ----------------
from persona import patches as persona_patches
for a_, b_ in persona_patches():
    sub(a_, b_)
# 上の刑事一覧：CPUの刑事には性格の札を出す（「切符∞」の代わり）
sub("""<span class="tks"><span class="tk inf" title="タクシー・バス・地下鉄は使い放題">切符∞</span>""",
    """<span class="tks">${A.role !== "pass" && !(A.role === "d" && k === ME_DET) && PERS_BY_K[k] ? `<span class="tk pers ${PERS_BY_K[k]}" title="この刑事の性格">${PERS_NAME[PERS_BY_K[k]]}</span>` : `<span class="tk inf" title="タクシー・バス・地下鉄は使い放題">切符∞</span>`}""")
sub("""  .tk.inf { background: #E8E0CC; color: #1A140C; padding: 0 5px; }""", """  .tk.inf { background: #E8E0CC; color: #1A140C; padding: 0 5px; }
  .tk.pers { padding: 0 5px; color: #fff; font-size: 10px; }
  .tk.pers.chase { background: #C2464F; } .tk.pers.cut { background: #2F7FB0; } .tk.pers.ambush { background: #5E7A3A; }""")
# 無線のひとことも性格ごとに
sub("""radio(k, pick(["こっちの視界にはいない", "この辺りは異常なし", "見当たらない。別の方を探す"]), "");""",
    """radio(k, pick(Math.random() < 0.5 ? ["こっちの視界にはいない", "この辺りは異常なし", "見当たらない。別の方を探す"] : ({ chase: ["足取りを追う！", "逃がさないぞ", "最後に見た方へ急ぐ"], cut: ["逃げ道の先へ回り込む", "この先で待ち構える", "向こう側をふさぐ"], ambush: ["乗り換え駅で張り込む", "ここを押さえておく", "動かず待つのが一番だ"] }[PERS_BY_K[k]] || ["見当たらない"])), "");""")
sub("""        <li><b>仲間への指示</b>：""", """        <li><b>刑事の性格</b>：CPUの刑事にはそれぞれ性格があります。<b>追いかけ</b>は怪盗Xがいそうな駅・最後に見た駅へまっすぐ詰め、<b>先回り</b>は怪盗Xが逃げそうな先へ回り込み、<b>待ち伏せ</b>は地下鉄駅など乗り換えの多い駅を押さえて待ちます。候補が絞れてくると全員で包囲します。</li>
        <li><b>仲間への指示</b>：""")

# ---------------- 怪盗Xの移動記録（行動履歴バー）を最上段に ----------------
sub("""    <div class="toprow first">
      <button class="panel iconbtn" data-act="menu" aria-label="メニュー">
        <svg viewBox="0 0 24 24"><path d="M4 7h16M4 12h16M4 17h16"></path></svg>
      </button>
      <button class="panel xcard" id="xcard" data-act="focusX"></button>
      <div class="panel dets" id="dets"></div>
    </div>
    <div class="toprow second">
      <div class="panel prompt" id="prompt"></div>
      <div class="panel xlog" id="xlog" aria-label="怪盗Xの移動記録"></div>
    </div>""", """    <div class="toprow second">
      <div class="panel xlog" id="xlog" aria-label="怪盗Xの移動記録"></div>
    </div>
    <div class="toprow first">
      <button class="panel iconbtn" data-act="menu" aria-label="メニュー">
        <svg viewBox="0 0 24 24"><path d="M4 7h16M4 12h16M4 17h16"></path></svg>
      </button>
      <button class="panel xcard" id="xcard" data-act="focusX"></button>
      <div class="panel prompt" id="prompt"></div>
      <div class="panel dets" id="dets"></div>
    </div>""")
sub("""  .toprow.second .xlog { flex: 1; min-width: 0; }""", """  .toprow.second .xlog { flex: 1; min-width: 0; }
  .toprow.first .dets { margin-left: auto; }
  .toprow.first .prompt { max-width: none; }
  .tk { white-space: nowrap; }
  @media (max-width: 760px) { .toprow.first .prompt { flex: none; max-width: 40%; } .toprow.first .prompt .portrait { display: none; } .toprow.first .xcard { min-width: 0; } .xcard .nx { display: none; } }
  @media (max-height: 520px) and (orientation: landscape) { .side { top: auto; bottom: 8px; transform: none; gap: 2px; padding: 4px; } }""")

# ---------------- 相棒確保で常に見える・警察犬カード（tools/dog_mate.py） ----------------
from dog_mate import patches as dogmate_patches
for a_, b_ in dogmate_patches():
    sub(a_, b_)
# 相棒は刑事から5駅以上離れて現れ、毎手1駅ずつ怪盗Xへ近づく（sim.js MATEDIST=5 MATEEVERY=1 で調整）
sub("occ.every(o => D[p][o] >= 3));", "occ.every(o => D[p][o] >= 5));")
sub("const MATE_EVERY = 3;   // 相棒は何手ごとに1駅動くか", "const MATE_EVERY = 1;   // 相棒は何手ごとに1駅動くか")
sub("""        banner("相棒確保！", "怪盗Xはもう相棒と合流できない", "blue", 2);""",
    """        banner("相棒確保！", "怪盗Xはもう隠れられない。これから居場所が常に見える", "blue", 2);""")
sub("""        pushFeed(G.xLog.length, `${dName(k)} が ${NAME(G.mate.pos)} で相棒を確保！ もう合流はできない`, true);""",
    """        pushFeed(G.xLog.length, `${dName(k)} が ${NAME(G.mate.pos)} で相棒を確保！ もう合流はできず、怪盗Xの居場所は常に見える`, true);""")
sub("""      else if (card === "heliban") detail = `すべてのヘリポートを閉鎖（${G.heliBan - G.xLog.length}手）`;""",
    """      else if (card === "heliban") detail = `すべてのヘリポートを閉鎖（${G.heliBan - G.xLog.length}手）`;
      else if (card === "dog") {
        if (G.dogUsed && G.dogUsed.n === G.xLog.length) {
          detail = `足跡を発見：${G.dogUsed.trail.map(p => `${NO(p)} ${NAME(p)}`).join(" → ")}。いそうな駅は${G.possible.length}駅`;
          banner("警察犬！", `足跡をたどった。いそうな駅は${G.possible.length}駅`, "blue", 2);
          say(nearestDet(G.dogUsed.trail), "ワン！ 足跡があった", "hot", 2600);
        } else detail = "まだ足跡がない";
      }""")
sub("""<li><b>カード</b>：5・10・17手目に""", """<li><b>カード</b>：${CARD_TURNS.join("・")}手目に""")
sub("""刑事側は「橋封鎖」「検問」「ダッシュ」「ヘリ封鎖」「ランダム検問」。""", """刑事側は「橋封鎖」「検問」「ダッシュ」「ヘリ封鎖」「ランダム検問」「警察犬」。警察犬は怪盗Xの2手前・3手前の駅（足跡）を見つけ、いそうな駅を絞り込みます。""")
sub("""刑事が相棒の駅に入ると相棒を確保でき、もう合流はできません。</li>""", """刑事が相棒の駅に入ると相棒を確保でき、もう合流はできません。<b>相棒を確保すると、それから先は怪盗Xの居場所が常に見えます。</b></li>""")

# ---------------- 警察犬の駒を地図に置く ----------------
sub("""      el("text", { x, y: y - 48, class: "lastseen-label" }, gM).textContent = `X? ${G.lastSeen.n}手目`;
    }""", """      el("text", { x, y: y - 48, class: "lastseen-label" }, gM).textContent = `X? ${G.lastSeen.n}手目`;
    }
    if (G.dog && !G.dog.gone && !G.over) {
      const [x, y] = P(G.dog.pos), left = Math.max(0, G.dog.until - G.xLog.length);
      el("ellipse", { cx: x + 60, cy: y + 20, rx: 50, ry: 11, fill: "rgba(0,0,0,0.28)" }, gM);
      el("image", { href: pxDogSprite(), x: x + 2, y: y - 60, width: 120, height: 81, class: "dog-piece" }, gM);
      el("text", { x: x + 62, y: y - 68, class: "mark-label dog" }, gM).textContent = left ? `警察犬 追跡あと${left}手` : "警察犬 追跡終了";
    }""")
sub("""  .mark-label.block { stroke: #C0271F; }""", """  .mark-label.block { stroke: #C0271F; }
  .mark-label.dog { stroke: #6E4A28; }
  .dog-piece { image-rendering: pixelated; pointer-events: none; }""")

# ---------------- 視界＝画面の長方形・ヘリはカードでだけ（tools/view_rule.py） ----------------
from view_rule import patches as view_patches, det_patches
VIEW_W, VIEW_H = 1050, 650   # 左上の地図に映る範囲そのもの。sim.js VIEW=1050,650 XT=22,15,7 BLACK=10（怪盗Xの勝率 刑事4人42%・5人22%）
for a_, b_ in view_patches(VIEW_W, VIEW_H) + det_patches("const DET_TICKETS = { heli: 1 };"):
    sub(a_, b_)

# ---------------- 4分割の画面（tools/layout.js） ----------------
sub("""    <g id="world">
""", """    <g id="world">
      <g id="worldIn">
""")
sub("""      <g id="gTalk"></g>
    </g>
  </svg>""", """      <g id="gTalk"></g>
      </g>
      <g id="viewMask"></g>
    </g>
  </svg>""")
sub("  const LOCK = false;", "  const LOCK = true;")
sub("    return Math.max(w / (W * 0.5), h / H);", "    return Math.min(w / VIEW_W, h / VIEW_H);   // 刑事の視界（画面の範囲）がちょうど入る倍率")
sub("""    const t = document.querySelector(".hud.top");
    return t ? t.getBoundingClientRect().bottom - mapEl.getBoundingClientRect().top : 100;""", """    return 0;   // 上の表示は地図の外（右上）にある""")
sub("""    if (A.overview) return;   // 全体地図のあいだは自由な大きさ
""", """    if (A.overview) return;   // 全体地図のあいだは自由な大きさ
    if (LOCK) return;         // 自分の駒をいつも真ん中に（端でもずらさない）
""")
sub("""    if (!G.over) for (const d of G.det) { const [x, y] = P(d.pos); el("circle", { cx: x, cy: y, r: SIGHT, class: "sight" }, gP); }
""", "")
sub("""    if (LOCK && A.G && A.screen === "game" && !A.overview && viewAnchor() !== lockedOn) lockView();""",
    """    if (LOCK && A.G && A.screen === "game" && !A.overview && viewAnchor() !== lockedOn) lockView();
    renderMini(); renderViewMask(); renderTalkLog();""")
sub("""    const covered = !$("drawer").hidden || !$("sheet").hidden || !$("screen").hidden;""", """    const covered = !$("sheet").hidden || !$("screen").hidden;""")
sub("""  #app { position: relative; height: 100%; overflow: hidden; }""", """  #app { position: relative; height: 100%; overflow: hidden; }
  /* 4分割の画面 */
  #app.layout4 { display: grid; gap: 6px; padding: 6px; background: #17130E;
    grid-template-columns: minmax(0, 1fr) clamp(290px, 31vw, 470px); grid-template-rows: minmax(0, 1fr) clamp(150px, 29vh, 270px);
    grid-template-areas: "map info" "cards mini"; }
  #app.layout4 #map { position: relative; inset: auto; grid-area: map; width: 100%; height: 100%; border-radius: 10px; cursor: default; }
  .pane { position: relative; z-index: 1; min-width: 0; min-height: 0; overflow: hidden; background: var(--hud-solid); border: 1px solid var(--rule); border-radius: 10px; }
  .pane.info { grid-area: info; display: flex; flex-direction: column; gap: 6px; padding: 6px; }
  .pane.cards { grid-area: cards; display: flex; gap: 8px; padding: 6px; }
  .pane.mini { grid-area: mini; display: flex; flex-direction: column; }
  #paneInfo .hud.top { position: static; transform: none; pointer-events: auto; flex: none; }
  #paneInfo .toprow.second, #paneInfo .pulltab, .hud.side, #overviewBtn { display: none !important; }
  #paneInfo .toprow.first { flex-wrap: wrap; }
  #paneInfo .toprow.first .xcard { flex: 1 1 0; min-width: 0; }
  #paneInfo .toprow.first .prompt { flex: 1 1 100%; max-width: none; order: 3; }
  #paneInfo .toprow.first .dets { flex: 1 1 100%; margin-left: 0; order: 4; }
  #paneInfo .drawer { position: static; width: auto; max-height: none; flex: 1; min-height: 0; padding: 6px 8px; box-shadow: none; }
  #paneInfo .drawer .row { display: flex; justify-content: space-between; align-items: center; }
  .hint-btn { min-height: 30px; padding: 0 10px; font-size: 12px; flex: none; }
  .hint-btn[aria-pressed="false"] { opacity: .55; }
  #paneCards .handbar { position: static; max-width: none; flex: 0 1 auto; min-width: 0; zoom: 1; }
  #paneCards .handbar[hidden] { display: none; }
  .talklog { flex: 1 1 0; min-width: 0; display: flex; flex-direction: column; background: #FFF6D8; color: #3A2C1E; border-radius: 8px; padding: 6px 8px; }
  .talklog .tl-h { font-weight: 900; font-size: 12px; color: #8A6A2A; }
  .talklog ul { list-style: none; margin: 4px 0 0; padding: 0; overflow-y: auto; display: flex; flex-direction: column; gap: 4px; font-size: 12px; }
  .talklog li { display: flex; gap: 6px; align-items: center; }
  .talklog li .portrait { width: 24px; height: 24px; flex: none; }
  .talklog li b { margin-right: 4px; }
  .talklog li.empty { color: #9A8A70; }
  .mini-h { font-size: 12px; font-weight: 900; padding: 4px 8px 0; display: flex; gap: 8px; align-items: baseline; }
  .mini-h span { font-weight: 400; font-size: 10px; color: var(--muted); overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
  #mini { flex: 1; min-height: 0; width: 100%; display: block; cursor: pointer; }
  #mini use { --lbl: hidden; }
  .stn-label, #gTalk { visibility: var(--lbl, visible); }
  .mini-view { fill: none; stroke-width: 8; opacity: .55; }
  .mini-me { fill: rgba(255, 230, 120, .15); stroke: #F2C230; stroke-width: 16; }
  .view-shade { fill: rgba(20, 16, 30, .38); pointer-events: none; }
  .view-frame { fill: none; stroke: #F2C230; stroke-width: 4; stroke-dasharray: 16 10; pointer-events: none; }
  .heli-sprite { image-rendering: pixelated; }
  @media (max-width: 760px) and (orientation: portrait) {
    #app.layout4 { grid-template-columns: 1fr 1fr; grid-template-rows: minmax(0, 46fr) minmax(0, 24fr) minmax(0, 30fr);
      grid-template-areas: "map map" "mini info" "cards info"; gap: 4px; padding: 4px; }
    .pane.cards { flex-direction: column; }
    #paneInfo .dets { zoom: .8; }
  }
  @media (max-height: 520px) and (orientation: landscape) {
    #app.layout4 { grid-template-rows: minmax(0, 1fr) 118px; grid-template-columns: minmax(0, 1fr) clamp(240px, 30vw, 360px); }
    #paneInfo .hud.top, #paneCards .handbar { zoom: .7; }
  }""")

# ルール説明（視界・ヘリ・操作）
sub("""<li><b>ヘリポート</b>（H）からはヘリで飛べます。""", """<li><b>ヘリポート</b>（ヘリの絵の駅）からはヘリで飛べます。ただしヘリの切符は最初は0枚で、<b>ヘリのカードを引いたときだけ</b>使えます（怪盗Xは「ヘリ」、刑事は「ヘリ出動」）。""")
sub("""ただし <b>刑事の視界</b>（刑事のまわりの青い点線の円）に入ると、""", """ただし <b>刑事の視界</b>（刑事を真ん中にした画面の範囲。左上の地図に映る四角）に入ると、""")
sub("""        <li><b>移動記録の見方</b>：""", """        <li style="display:none"><b>移動記録の見方</b>：""")
sub("""        <li>操作：ドラッグで移動、ピンチ・ホイール・ダブルタップで拡大。光る駅をタップすると切符を選べます。ヘリは画面上部の手番表示にある「ヘリ」ボタンから。</li>""",
    """        <li>画面：<b>左上</b>は自分の駒を真ん中にした地図（動かしたり拡大はできません）。<b>右上</b>はプレイヤー情報と履歴、<b>左下</b>は手札と無線、<b>右下</b>は全体図です。自分の番に光る駅をタップすると切符を選べます。左上の地図に映らない遠い行き先や、橋封鎖などカードの対象は全体図の駅をタップして選べます。</li>""")

# 画面の端の矢印：地図の四辺の内側に置く（上の表示・右のボタン列はもう地図に重ならない）
sub("""    const top = (topEl ? topEl.getBoundingClientRect().bottom - r.top : 100) + 36;""", """    const top = 36;""")
sub("""    const sideR = sideEl ? sideEl.getBoundingClientRect() : null;""", """    const sideR = null;""")
sub("""  .hint-btn { min-height: 30px; padding: 0 10px; font-size: 12px; flex: none; }""", """  .hint-btn { min-height: 30px !important; padding: 0 10px !important; font-size: 12px !important; flex: 0 0 auto !important; width: auto !important; }
  .mini-h { white-space: nowrap; }
  #app.layout4 #edge { grid-area: map; position: relative; inset: auto; }""")

# ---------------- 画面の調整：少し引いた視点・全体図の拡大ボタン・大きな手札カード ----------------
sub("    return Math.min(w / VIEW_W, h / VIEW_H);   // 刑事の視界（画面の範囲）がちょうど入る倍率",
    "    return w / VIEW_W;   // 地図の枠は視界と同じ縦横比にしてあるので、映っている範囲＝視界")
# 手札：大きなカードを横に並べる（カード名と説明つき）
sub("""title="${esc(CARD[c].desc)}"><img src="${pxHandArt(c)}" alt=""><span>${CARD[c].name}</span></button>`""",
    """title="${esc(CARD[c].desc)}"><img src="${pxHandArt(c)}" alt=""><span>${CARD[c].name}</span><small>${esc(CARD[c].desc)}</small></button>`""")
sub("""      <span>${why}</span></button>`;""", """      <span>ヘリ</span><small>${why}${left ? "（ヘリの絵の駅から、ほかのヘリポートのどこかへ）" : "（ヘリのカードを引くと使える）"}</small></button>`;""")
sub("""  .heli-sprite { image-rendering: pixelated; }""", """  .heli-sprite { image-rendering: pixelated; }
  /* 左下：手札を大きなカードで並べ、無線は右端に小さく */
  #paneCards .handbar { flex: 1 1 auto; display: flex; flex-direction: column; padding: 6px 8px; overflow: hidden; }
  #paneCards .hb-cards { flex: 1; min-height: 0; gap: 10px; align-items: stretch; overflow-x: auto; overflow-y: hidden; }
  #paneCards .hb-card { width: auto; height: 100%; aspect-ratio: 5 / 7; padding: 6px; gap: 4px; justify-content: flex-start; background: #FBF7EA; color: #4F6475;
    border: 3px solid #2F5FB8; border-radius: 10px; box-shadow: inset 0 0 0 2px #FBF7EA, inset 0 0 0 3px rgba(47,95,184,.35), 0 3px 0 rgba(0,0,0,.35); }
  #paneCards .hb-card.x { border-color: #C2464F; }
  #paneCards .hb-card.heli { border-color: #7C3AED; }
  #paneCards .hb-card img { width: 100%; image-rendering: pixelated; border: 2px solid #4F6475; border-radius: 3px; }
  #paneCards .hb-card.heli .hb-heli { background: #CFE3F5; border: 2px solid #4F6475; border-radius: 3px; position: relative; }
  #paneCards .hb-card.heli .hb-heli img { width: 100%; border: 0; }
  #paneCards .hb-card.heli .hb-heli b { position: absolute; right: 4px; bottom: 2px; font-size: 16px; color: #fff; text-shadow: 1px 1px 0 #3B2C6E, -1px -1px 0 #3B2C6E; }
  #paneCards .hb-card span { font-family: "DotGothic16", sans-serif; font-weight: 400; font-size: clamp(12px, 1.6vh, 17px); color: #4F6475; white-space: normal; }
  #paneCards .hb-card small { font-size: clamp(9px, 1.25vh, 12px); line-height: 1.35; color: #5A4A40; text-align: left; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 5; -webkit-box-orient: vertical; }
  #paneCards .hb-card.heli.off { opacity: .75; }
  #paneCards .talklog { flex: 0 0 clamp(150px, 22%, 250px); }
  #paneCards .talklog ul { font-size: 11px; }
  #paneCards .hb-empty { align-self: center; }
  /* 全体図の拡大：右下から左上へ約2倍に広げる */
  .mini-zoom { margin-left: auto; flex: none; font: inherit; font-size: 11px; font-weight: 900; padding: 2px 10px; border-radius: 999px; border: 1px solid var(--rule); background: #E3B341; color: #1A140C; cursor: pointer; }
  .mini-h { align-items: center; }
  #app.mini-big #paneMini { grid-area: auto; position: absolute; right: 6px; bottom: 6px; z-index: 19 !important; box-shadow: 0 10px 40px rgba(0,0,0,.6);
    width: min(calc(2 * clamp(290px, 31vw, 470px)), calc(100% - 12px)); height: min(calc(2 * clamp(150px, 29vh, 270px)), calc(100% - 12px)); }
  @media (max-width: 760px) and (orientation: portrait) {
    #app.mini-big #paneMini { width: calc(100% - 8px); height: 55%; right: 4px; bottom: 4px; }
    #paneCards .hb-card { height: auto; width: 88px; aspect-ratio: auto; }
    #paneCards .talklog { flex: 1 1 auto; }
  }
  @media (max-height: 520px) and (orientation: landscape) { #app.mini-big #paneMini { height: calc(100% - 12px); } }""")

# ---------------- 映っている範囲＝索敵範囲：地図の枠を視界と同じ縦横比に。右の人物は全身図 ----------------
sub("""  function renderViewMask() {
    const g = $("viewMask"), G = A.G;
    if (!g) return;
    g.replaceChildren();""", """  function renderViewMask() {
    const g = $("viewMask"), G = A.G;
    if (!g) return;
    g.replaceChildren();
    return;   // 地図に映っている範囲すべてが視界なので、枠や影は描かない""")
sub("""  (function setupLayout() {
    const app = $("app");""", """  (function setupLayout() {
    const app = $("app");
    // 地図のマス目（grid の map 領域）の大きさを測り、その中に視界と同じ縦横比の地図を置く
    const cell = document.createElement("div");
    cell.id = "mapCell";
    app.insertBefore(cell, app.firstChild);
    const fit = () => {
      const r = cell.getBoundingClientRect(), k = Math.min(r.width / VIEW_W, r.height / VIEW_H);
      mapEl.style.width = Math.floor(VIEW_W * k) + "px";
      mapEl.style.height = Math.floor(VIEW_H * k) + "px";
    };
    fit();
    new ResizeObserver(() => { fit(); window.dispatchEvent(new Event("resize")); }).observe(cell);""")
sub("""  #app.layout4 #map { position: relative; inset: auto; grid-area: map; width: 100%; height: 100%; border-radius: 10px; cursor: default; }""",
    """  #app.layout4 #map { position: relative; inset: auto; grid-area: map; justify-self: center; align-self: center; border-radius: 10px; cursor: default; }
  #mapCell { grid-area: map; min-width: 0; min-height: 0; }""")
sub("""  #app.layout4 #edge { grid-area: map; position: relative; inset: auto; }""", """  #app.layout4 #edge { grid-area: map; position: relative; inset: auto; justify-self: center; align-self: center; width: var(--mw); height: var(--mh); }""")
sub("""      mapEl.style.height = Math.floor(VIEW_H * k) + "px";""", """      mapEl.style.height = Math.floor(VIEW_H * k) + "px";
      app.style.setProperty("--mw", mapEl.style.width); app.style.setProperty("--mh", mapEl.style.height);""")
# 右の人物：顔アイコンの代わりに全身図を大きく
sub("""        ${portrait("d", k, "sm")}${A.role === "d" && k === ME_DET ?""", """        <img class="det-full" src="${detChar(k).img}" alt="">${A.role === "d" && k === ME_DET ?""")
sub("""    $("xcard").innerHTML = `${portrait("x")}<span class="who">""", """    $("xcard").innerHTML = `<img class="x-full" src="${thief().img}" alt="">${G.mate ? `<span class="mate-full"><img src="${mateChar().img}" alt=""><small>相棒${G.mate.out ? "（確保）" : ""}</small></span>` : ""}<span class="who">""")
sub("""  .det .tks { flex-wrap: wrap; justify-content: center; max-width: 92px; }""", """  .det .tks { flex-wrap: wrap; justify-content: center; max-width: 92px; }
  .det-full { height: clamp(70px, 13vh, 130px); width: auto; aspect-ratio: 3 / 5; object-fit: contain; object-position: bottom; filter: drop-shadow(0 3px 3px rgba(0,0,0,.5)); }
  .x-full { height: clamp(80px, 15vh, 140px); width: auto; aspect-ratio: 3 / 5; object-fit: contain; object-position: bottom; flex: none; filter: drop-shadow(0 3px 3px rgba(0,0,0,.5)); }
  .mate-full { display: flex; flex-direction: column; align-items: center; flex: none; font-size: 10px; color: var(--muted); }
  .mate-full img { height: clamp(50px, 9vh, 90px); width: auto; aspect-ratio: 3 / 5; object-fit: contain; object-position: bottom; }
  #paneInfo .dets { justify-content: space-around; }
  #paneInfo .det { flex: 1 1 0; }
  @media (max-width: 760px) and (orientation: portrait) {
    #app.layout4 { grid-template-rows: auto minmax(0, 40fr) minmax(0, 60fr); }
    #mapCell { aspect-ratio: 1050 / 650; width: 100%; }
    .x-full { height: 64px; } .mate-full { display: none; } .det-full { height: 64px; }
  }""")

# ---------------- 怪盗Xの強いカード（tools/strong_cards.py）と、カードの知らせ ----------------
from strong_cards import patches as strong_patches
for a_, b_ in strong_patches(24):
    sub(a_, b_)
sub("""    const mine = A.role === "x" || (A.role === "pass" && A.cover === "x-open");""", """    const mine = A.role === "x" || (A.role === "pass" && A.cover === "x-open");
    if (card === "smoke") {
      toast("煙幕！ 刑事全員が1回休み");
      banner("煙幕！", "刑事全員が1回休み", "gray", 2);
      pushFeed(G.xLog.length, "怪盗Xのカード「煙幕」：刑事全員が1回休み", true);
      G.det.forEach((_, k) => say(k, "ゴホッ、前が見えない！", "sad", 2600));
      return;
    }""")
sub("""card === "vanish" ? "：次の目撃情報を消す" : "：何も起こらなかった"}`""",
    """card === "vanish" ? "：次の目撃情報を消す" : card === "disguise" ? "：3手のあいだ見つからない" : card === "xheli" ? "：ヘリの切符を1枚得た" : "：何も起こらなかった"}`""")
sub("""<li><b>カード</b>：${CARD_TURNS.join("・")}手目に""", """<li><b>カード</b>：（怪盗Xは「罠」「雲隠れ」「駅破壊」「ヘリ」「煙幕」「変装」）${CARD_TURNS.join("・")}手目に""")

# ---------------- 全体図を大きく・拡大時は無線をよける・全体図で行き先を光らせて選びやすく ----------------
sub("""  .heli-sprite { image-rendering: pixelated; }""", """  .heli-sprite { image-rendering: pixelated; }
  @media (min-width: 761px) and (min-height: 521px) {
    #app.layout4 { --colR: clamp(330px, 36vw, 580px); --rowB: clamp(170px, 32vh, 330px);
      grid-template-columns: minmax(0, 1fr) var(--colR); grid-template-rows: minmax(0, 1fr) var(--rowB); }
    #app.mini-big #paneMini { width: min(calc(2 * var(--colR)), calc(100% - 12px)) !important; height: min(calc(2 * var(--rowB)), calc(100% - 12px)) !important; }
    #paneCards { transition: padding-right .3s ease; }
    #app.mini-big #paneCards { padding-right: calc(min(2 * var(--colR), 100vw - 24px) - var(--colR) + 6px); }
  }
  .mini-dest { fill: rgba(242, 194, 48, .35); stroke: #F2C230; stroke-width: 14; }
  .mini-dest.tgt { fill: rgba(229, 72, 77, .3); stroke: #E5484D; }""")

# ---------------- 水上バスの切符：怪盗Xは水上バス専用の切符5枚でも乗れる（黒チケットでも乗れる） ----------------
sub("""${G.xt && (xVisible() || G.over) ? ["taxi", "bus", "tube"].map(t =>""", """${G.xt && (xVisible() || G.over) ? ["taxi", "bus", "tube", "boat"].map(t =>""")
sub("""地下鉄${X_TICKETS.tube}・黒チケット・""", """地下鉄${X_TICKETS.tube}・水上バス${X_TICKETS.boat}・黒チケット・""")
sub("""乗れるのは <b>怪盗Xだけ</b>で、<b>黒チケット</b>を使います。""", """乗れるのは <b>怪盗Xだけ</b>で、<b>水上バスの切符</b>（${X_TICKETS.boat}枚）か<b>黒チケット</b>を使います（黒チケットなら乗り物は隠れます）。桟橋のある駅では、行き先を選ぶと「WATER BUS」のカードが出ます。""")

# ---------------- モノレール・怪盗Xのヘリはいつでも（tools/mono_rule.py） ----------------
from mono_rule import patches as mono_patches
for a_, b_ in mono_patches(6, 99):
    sub(a_, b_)
sub("""["taxi", "bus", "tube", "boat"].map(t => `<span class="tk ${t}""", """["taxi", "bus", "tube", "mono", "boat"].map(t => `<span class="tk ${t}""")
sub("""<span class="tk heli ${G.heli ? "" : "zero"}">H${G.heli}</span>""", """<span class="tk heli ${G.heli ? "" : "zero"}">H${G.heli >= 50 ? "∞" : G.heli}</span>""")
sub("""<b>×${left}</b></span>""", """<b>×${left >= 50 ? "∞" : left}</b></span>""")
sub("""  .tk.boat { background: var(--ferry); color: #fff; }""", """  .tk.boat { background: var(--ferry); color: #fff; }
  .tk.mono, .pxcard .pc-type.mono { background: #E08A2E; color: #fff; }
  .wedge.mono { fill: #E08A2E; }
  .mono-ln { stroke: #E08A2E; }
  .mono-dash { stroke: #FFF1DC; stroke-width: 5; stroke-dasharray: 3 9; }""")
sub("""地下鉄${X_TICKETS.tube}・水上バス${X_TICKETS.boat}・黒チケット・""", """地下鉄${X_TICKETS.tube}・モノレール${X_TICKETS.mono}・水上バス${X_TICKETS.boat}・黒チケット・""")
sub("""（ヘリだけ${DET_TICKETS.heli}枚。水上バスには乗れません）""", """（ヘリはカード「ヘリ出動」でだけ。水上バスには乗れません）""")
sub("""        <li><b>水上バス</b>（青い破線）""", """        <li><b>モノレール</b>（オレンジの線）は湾岸を走る高架の路線です。広野から夢見島・潮月町を通って岬町まで、夢見島から空港島へも行けます。刑事は使い放題、怪盗Xは切符${X_TICKETS.mono}枚。</li>
        <li><b>水上バス</b>（青い破線）""")
sub("""ただしヘリの切符は最初は0枚で、<b>ヘリのカードを引いたときだけ</b>使えます（怪盗Xは「ヘリ」、刑事は「ヘリ出動」）。""", """<b>怪盗Xはいつでも</b>ヘリで飛べます。刑事はカード「ヘリ出動」を引いたときだけ使えます。""")
sub("""（怪盗Xは「罠」「雲隠れ」「駅破壊」「ヘリ」「煙幕」「変装」）""", """（怪盗Xは「罠」「雲隠れ」「駅破壊」「煙幕」「変装」）""")

# ---------------- 残っていないかの確認 ----------------
for word in ["テムズ", "ロンドン", "london-map", "霧の"]:
    assert word not in out, f"leftover: {word}"
dst = os.path.join(HERE, "..", "index.html")
open(dst, "w", encoding="utf-8").write(out)
print("wrote", os.path.normpath(dst), len(out), "bytes")
