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

# ---------------- 画面を広く使う：地図は画面いっぱい、最大に縮小しても横は半分くらい。横スクロールで追いかける ----------------
sub("""    V.s = Math.min(3, Math.max(V.fit * 0.85, V.s));
    const mw = W * V.s, mh = H * V.s, pad = 80;
    V.tx = mw + pad * 2 <= w ? (w - mw) / 2 : Math.min(pad, Math.max(w - mw - pad, V.tx));
    const top = hudTop();
    V.ty = mh + top + 40 <= h ? top + (h - top - mh) / 2 : Math.min(top + 20, Math.max(h - mh - 60, V.ty));""",
"""    V.s = Math.min(3, Math.max(V.fit, V.s));
    const mw = W * V.s, mh = H * V.s;
    // 地図の端が画面の内側に入らないようにする（上だけは画面上部の表示の下まで下げられる）
    V.tx = Math.min(0, Math.max(w - mw, V.tx));
    V.ty = Math.min(hudTop() * 0.7, Math.max(h - mh, V.ty));""")
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
        ensureVisible(landed);
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
    ensureVisible(landed);
    step();""")
sub('aria-label="全体を表示"', 'aria-label="いちばん引いて表示"')

# 駒へ移動するときは、いまの拡大率のまま（勝手に拡大しない）
sub("function centerOn(i, s = Math.max(V.s, 0.95)) {", "function centerOn(i, s = V.s) {")

# ---------------- プレイヤー視点に固定：画面は自分の駒を中心に動かない。見えるのは自分のまわりだけ ----------------
sub("""  // いちばん引いたときの倍率：""", """  // 画面は自分の駒（パス&プレイでは手番の人の駒）を中心に固定する。ドラッグや拡大縮小はしない
  const LOCK = true;
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
sub("""  .side .iconbtn:active""", """  .side [data-act="zoomIn"], .side [data-act="zoomOut"], .side [data-act="fit"] { display: none; }
  .edge-arrow.dest .dest-no { position: relative; display: grid; place-items: center; width: 34px; height: 34px; border-radius: 50%; background: #FFF6D8; color: #1A140C; font-weight: 900; font-size: 13px; border: 3px solid #3B2C1E; }
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
    if (ob) ob.setAttribute("aria-pressed", String(!!A.overview));""")
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
sub("""  .side [data-act="zoomIn"], .side [data-act="zoomOut"], .side [data-act="fit"] { display: none; }""",
    """  .side [data-act="zoomIn"], .side [data-act="zoomOut"], .side [data-act="fit"] { display: none; }
  #map.z0 .stn-label:not(.hot) { display: none; }""")

# ---------------- 視界ルール：怪盗Xは刑事の視界（円）に入ったら見つかる ----------------
from sight_rule import patches as sight_patches
SIGHT = 410
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

# ---------------- 残っていないかの確認 ----------------
for word in ["テムズ", "ロンドン", "london-map", "霧の"]:
    assert word not in out, f"leftover: {word}"
dst = os.path.join(HERE, "..", "index.html")
open(dst, "w", encoding="utf-8").write(out)
print("wrote", os.path.normpath(dst), len(out), "bytes")
