// CPU どうしの対戦をたくさん回して、盤面の遊びやすさ（勝率・決着の手数など）を調べる
// ロンドン版の HTML から「CORE」（ルールとCPU。画面に依存しない部分）をそのまま取り出して使う
//   node sim.js <london.html> [games=400] [board=tokyo|london] [dets=4] [xTube=4] [xRail=3]
const fs = require("fs");
const path = require("path");

const [, , htmlPath, gamesArg = "400", which = "tokyo", detsArg = "4", xTubeArg = "", xRailArg = "3"] = process.argv;
const html = fs.readFileSync(htmlPath, "utf8");
let core = html.slice(html.indexOf("// CORE-START"), html.indexOf("// CORE-END"));

if (which === "sy") {
  // スコットランドヤード式の盤面（バス・地下鉄・水上バスは路線ではなく辺の集まり）
  const B = JSON.parse(fs.readFileSync(path.join(__dirname, "board_sy.json"), "utf8"));
  const a = core.indexOf("const W = ");
  const b = core.indexOf("const N = STATIONS.length;");
  const data = `
  const W = ${B.W}, H = ${B.H};
  const STATIONS = ${JSON.stringify(B.stations)};
  const TAXI = ${JSON.stringify(B.taxi)};
  const TUBE = ${JSON.stringify(B.subwayEdges.map(e => ["地下鉄", e]))};
  const BUS = ${JSON.stringify(B.busEdges)};
  const BOATS = ${JSON.stringify(B.boatEdges.map(e => ["水上バス", e]))};
  const BOAT = [];
  const HELI = ${JSON.stringify(B.heli)};
  const RIVER = [], ISLANDS = [];
  const BRIDGE_ST = ${JSON.stringify(B.bridges)};
  const BRIDGES = [];
  const ISLAND_LIST = ${JSON.stringify(B.islands)};
  `;
  core = core.slice(0, a) + data + core.slice(b);
  core = core.replace(/const ISLAND_ST = new Set\([\s\S]*?\}\)\);/, "const ISLAND_ST = new Set(ISLAND_LIST);");
  core = core.replace(
    'for (let k = 0; k < BOAT.length - 1; k++) addEdge(BOAT[k], BOAT[k + 1], "boat", "テムズ水上バス");',
    'for (const [line, seq] of BOATS) for (let k = 0; k < seq.length - 1; k++) addEdge(seq[k], seq[k + 1], "boat", line);');
  // スコットランドヤードのルール：水上バスは怪盗Xが黒チケットでだけ乗れる。刑事は乗れない
  core = core.replace('const dHas = (d, type) => type === "heli" ? d.t.heli > 0 : true;', 'const dHas = (d, type) => type === "heli" ? d.t.heli > 0 : type !== "boat";');
  core = core.replace(/tube: 4, boat: 2 \}/, "tube: 4, boat: 0 }");
} else if (which === "tokyo") {
  const B = JSON.parse(fs.readFileSync(path.join(__dirname, "board.json"), "utf8"));
  // 盤面データの部分（W,H から BRIDGES まで）を東京の盤面に差し替える
  const a = core.indexOf("const W = ");
  const b = core.indexOf("const N = STATIONS.length;");
  const data = `
  const W = ${B.W}, H = ${B.H};
  const STATIONS = ${JSON.stringify(B.stations)};
  const TAXI = ${JSON.stringify(B.taxi)};
  const TUBE = ${JSON.stringify(B.tube.map(([n, , s]) => [n, s]))};
  const RAIL = ${JSON.stringify((B.rail || []).map(([n, , s]) => [n, s]))};
  const BUS = ${JSON.stringify(B.bus)};
  const BOATS = ${JSON.stringify(B.boat)};
  const BOAT = [];
  const HELI = ${JSON.stringify(B.heli)};
  const RIVER = [], ISLANDS = [];
  const BRIDGE_ST = ${JSON.stringify(B.bridges)};
  const BRIDGES = [];
  const ISLAND_LIST = ${JSON.stringify(B.islands)};
  `;
  core = core.slice(0, a) + data + core.slice(b);
  // 島は座標の楕円ではなく、盤面データの一覧で決める
  core = core.replace(/const ISLAND_ST = new Set\([\s\S]*?\}\)\);/, "const ISLAND_ST = new Set(ISLAND_LIST);");
  // 水上バスは複数路線
  core = core.replace(
    'for (let k = 0; k < BOAT.length - 1; k++) addEdge(BOAT[k], BOAT[k + 1], "boat", "テムズ水上バス");',
    'for (const [line, seq] of BOATS) for (let k = 0; k < seq.length - 1; k++) addEdge(seq[k], seq[k + 1], "boat", line);' +
    'for (const [line, seq] of RAIL) for (let k = 0; k < seq.length - 1; k++) addEdge(seq[k], seq[k + 1], "rail", line);');
  // 鉄道（JR）を5つめの乗り物として足す（地下鉄とは別の切符）
  core = core.replace('tube:  { name: "地下鉄", en: "Underground", short: "地" },', 'tube:  { name: "地下鉄", en: "Subway", short: "地" },\n    rail:  { name: "鉄道", en: "Rail", short: "鉄" },');
  core = core.replace('const DET_TYPES = ["taxi", "bus", "tube", "boat", "heli"];', 'const DET_TYPES = ["taxi", "bus", "tube", "rail", "boat", "heli"];');
  core = core.replace('const MOVE_TYPES = ["taxi", "bus", "tube", "boat"];', 'const MOVE_TYPES = ["taxi", "bus", "tube", "rail", "boat"];');
  core = core.replace(/tube: 4, boat: 2 \}/, `tube: 4, rail: ${Number(xRailArg)}, boat: 2 }`);
}
// 刑事の切符を有限にする（スコットランドヤードのルール。使った切符は怪盗Xへ渡る）
if (process.env.DET_LIMIT) {
  const [t, b, u] = process.env.DET_LIMIT.split(",").map(Number);
  core = core.replace("const DET_TICKETS = { heli: 1 };", `const DET_TICKETS = { taxi: ${t}, bus: ${b}, tube: ${u}, heli: 1 };`);
  core = core.replace(/const dHas = \(d, type\) => [^;]*;/, 'const dHas = (d, type) => type === "boat" ? false : (d.t[type] ?? 0) > 0;');
  core = core.replace("    if (type === \"heli\") d.t.heli--;", "    if (type === \"heli\") d.t.heli--;\n    else if (d.t[type] !== undefined) { d.t[type]--; if (G.xt && G.xt[type] !== undefined) G.xt[type]++; }");
}
// 視界ルール：SIGHT=半径 のとき、怪盗Xは刑事の視界に入ったら見つかる（公開の手番はなし）
if (process.env.SIGHT) {
  const pairs = JSON.parse(require("child_process").execFileSync("python3", [path.join(__dirname, "sight_rule.py"), process.env.SIGHT, process.env.PARTIAL ?? "1"]).toString());
  for (const [a, b] of pairs) { if (!core.includes(a)) throw new Error("sight patch not found: " + a.slice(0, 60)); core = core.replace(a, b); }
}
// 公開のタイミング：スコットランドヤード式（24手、3・8・13・18・24手目）
if (process.env.SY_ROUNDS) {
  core = core.replace("const MAX_MOVES = 21;", "const MAX_MOVES = 24;");
  core = core.replace("const REVEAL = [3, 6, 9, 12, 15, 18, 21];", "const REVEAL = [3, 8, 13, 18, 24];");
}
// 手数を変える：MOVES=30 CARDS=5,12,20 CARD_LAST=28 XT=14,10,5 BLACK=5 DBL=4
if (process.env.MOVES) {
  core = core.replace("const MAX_MOVES = 21;", `const MAX_MOVES = ${Number(process.env.MOVES)};`);
  if (process.env.CARDS) core = core.replace("const CARD_TURNS = [5, 10, 17];", `const CARD_TURNS = [${process.env.CARDS}];`);
  if (process.env.CARD_LAST) core = core.replace("const CARD_LAST = 20;", `const CARD_LAST = ${Number(process.env.CARD_LAST)};`);
}
if (process.env.XT) { const [t, b, u] = process.env.XT.split(",").map(Number); core = core.replace(/const X_TICKETS = \{[^}]*\};/, `const X_TICKETS = { taxi: ${t}, bus: ${b}, tube: ${u}, boat: 0 };`); }
if (process.env.BLACK) core = core.replace("black: detCount,", `black: ${Number(process.env.BLACK)},`);
if (process.env.DBL) core = core.replace(/const X_DOUBLE = \d+;/, `const X_DOUBLE = ${Number(process.env.DBL)};`);
if (xTubeArg) core = core.replace(/tube: 4,/, `tube: ${Number(xTubeArg)},`);

const api = new Function(core + `
  return { N, ADJ, D, newGame, xMoves, applyX, detMoves, applyD, skipD, finish, allStuck, aiX, aiD,
           aiUseCards, applyCard, drawCard, checkTrap, handOf, cardMove, CARD_TURNS, CARD_LAST, MAX_MOVES, REVEAL, X_TICKETS };
`)();

let selfTrap = 0, boatRides = 0, boatMaybe = 0;
// 画面の step() と同じ流れを、全員CPUで回す（刑事側のカードもCPUが使う＝怪盗Xモードと同じ）
function play(dets) {
  const { G, sec } = api.newGame(dets, true);
  let sizes = [];
  const gain = (side, card) => {
    if (card === "heliban") { G.helibanDrawn = true; api.applyCard(G, sec, card, null); return; }
    if (card === "rcheck") { api.applyCard(G, sec, card, null); return; }
    if (card !== "miss") api.handOf(G, side).push(card);
  };
  const expire = side => { if (api.cardMove(G, side) > api.CARD_LAST) api.handOf(G, side).length = 0; };
  let guard = 0;
  while (!G.over && guard++ < 2000) {
    if (G.turn === "x") {
      if (!api.xMoves(G, sec).length) { api.finish(G, "d", "trapped"); break; }
      if (!G.doubling) {
        const n = G.xLog.length + 1;
        G.drawn = G.drawn || { x: [], d: [] };
        if (api.CARD_TURNS.includes(n) && !G.drawn.x.includes(n)) { G.drawn.x.push(n); gain("x", api.drawCard("x")); }
        expire("x");
      }
      for (const [c, t] of api.aiUseCards(G, sec, "x")) api.applyCard(G, sec, c, t);
      // ロンドン版の不具合：CPUの怪盗Xが「駅破壊」で自分の最後の逃げ道を壊すことがある。ここでは袋のネズミとして扱う
      if (!api.xMoves(G, sec).length) { api.finish(G, "d", "trapped"); selfTrap++; break; }
      const m = api.aiX(G, sec);
      if (m.type === "black") { const ts = api.ADJ[sec.pos].filter(e => e.to === m.to).map(e => e.type); if (ts.length && ts.every(t => t === "boat")) boatRides++; else if (ts.includes("boat")) boatMaybe++; }
      api.applyX(G, sec, m.to, m.type, m.useDouble);
      sizes.push(G.possible.length);
    } else {
      const k = G.turn;
      if (k === 0) {
        const n = G.xLog.length;
        G.drawn = G.drawn || { x: [], d: [] };
        if (api.CARD_TURNS.includes(n) && !G.drawn.d.includes(n)) { G.drawn.d.push(n); gain("d", api.drawCard("d", G)); }
        expire("d");
      }
      if (G.stun && G.stun[k] > 0) { G.stun[k]--; api.skipD(G, k); continue; }
      if (api.allStuck(G)) { api.finish(G, "x", "stuck"); break; }
      if (!api.detMoves(G, k).length) { api.skipD(G, k); continue; }
      for (const [c, t] of api.aiUseCards(G, sec, "d")) api.applyCard(G, sec, c, t);
      const m = api.aiD(G, k);
      api.applyD(G, k, m.to, m.type, sec);
    }
    if (!G.over && G.det.some(d => d.pos === sec.pos)) api.finish(G, "d", "caught");
    if (!G.over) api.checkTrap(G, sec);
  }
  const used = {};
  for (const e of G.xLog) used[e.t] = (used[e.t] || 0) + 1;
  return { winner: G.winner, reason: G.reason, moves: G.xLog.length, avgPossible: sizes.reduce((a, b) => a + b, 0) / Math.max(1, sizes.length), used };
}

// 盤面そのものの性質
function boardStats() {
  const deg = api.ADJ.map(a => new Set(a.map(e => e.to)).size);
  let far = 0, sum = 0, cnt = 0;
  for (let i = 0; i < api.N; i++) for (let j = 0; j < api.N; j++) if (i !== j && api.D[i][j] < Infinity) { sum += api.D[i][j]; cnt++; far = Math.max(far, api.D[i][j]); }
  const types = {};
  for (const a of api.ADJ) for (const t of new Set(a.map(e => e.type))) types[t] = (types[t] || 0) + 1;
  return { stations: api.N, avgNeighbors: +(deg.reduce((a, b) => a + b, 0) / api.N).toFixed(2), avgSteps: +(sum / cnt).toFixed(2), maxSteps: far, stationsWith: types };
}

const games = Number(gamesArg), dets = Number(detsArg);
const res = [];
for (let g = 0; g < games; g++) res.push(play(dets));
const pct = f => (100 * res.filter(f).length / games).toFixed(1) + "%";
const reasons = {};
for (const r of res) reasons[r.reason] = (reasons[r.reason] || 0) + 1;
const caught = res.filter(r => r.winner === "d");
const usedAvg = {};
for (const r of res) for (const [t, n] of Object.entries(r.used)) usedAvg[t] = (usedAvg[t] || 0) + n / games;
console.log(JSON.stringify({
  board: which, detectives: dets, games, xTickets: api.X_TICKETS, ...boardStats(),
  xWin: pct(r => r.winner === "x"), detWin: pct(r => r.winner === "d"), reasons, selfTrapByDestroyCard: selfTrap,
  avgCatchMove: caught.length ? +(caught.reduce((a, r) => a + r.moves, 0) / caught.length).toFixed(1) : null,
  avgCandidates: +(res.reduce((a, r) => a + r.avgPossible, 0) / games).toFixed(1),
  boatOnlyRidesPerGame: +(boatRides / games).toFixed(3), blackOnBoatOrOtherPerGame: +(boatMaybe / games).toFixed(3),
  xTicketsUsedPerGame: Object.fromEntries(Object.entries(usedAvg).map(([k, v]) => [k, +v.toFixed(2)])),
}, null, 1));
