// CPU どうしの対戦をたくさん回して、盤面の遊びやすさ（勝率・決着の手数など）を調べる
// ロンドン版の HTML から「CORE」（ルールとCPU。画面に依存しない部分）をそのまま取り出して使う
//   node sim.js <london.html> [games=400] [board=tokyo|london] [dets=4] [xTube=4]
const fs = require("fs");
const path = require("path");

const [, , htmlPath, gamesArg = "400", which = "tokyo", detsArg = "4", xTubeArg = ""] = process.argv;
const html = fs.readFileSync(htmlPath, "utf8");
let core = html.slice(html.indexOf("// CORE-START"), html.indexOf("// CORE-END"));

if (which === "tokyo") {
  const B = JSON.parse(fs.readFileSync(path.join(__dirname, "board.json"), "utf8"));
  // 盤面データの部分（W,H から BRIDGES まで）を東京の盤面に差し替える
  const a = core.indexOf("const W = ");
  const b = core.indexOf("const N = STATIONS.length;");
  const data = `
  const W = ${B.W}, H = ${B.H};
  const STATIONS = ${JSON.stringify(B.stations)};
  const TAXI = ${JSON.stringify(B.taxi)};
  const TUBE = ${JSON.stringify(B.tube.map(([n, , s]) => [n, s]))};
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
    'for (const [line, seq] of BOATS) for (let k = 0; k < seq.length - 1; k++) addEdge(seq[k], seq[k + 1], "boat", line);');
}
if (xTubeArg) core = core.replace(/tube: 4, boat: 2 \}/, `tube: ${Number(xTubeArg)}, boat: 2 }`);

const api = new Function(core + `
  return { N, ADJ, D, newGame, xMoves, applyX, detMoves, applyD, skipD, finish, allStuck, aiX, aiD,
           aiUseCards, applyCard, drawCard, checkTrap, handOf, cardMove, CARD_TURNS, CARD_LAST, MAX_MOVES, REVEAL, X_TICKETS };
`)();

let selfTrap = 0;
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
  board: which, detectives: dets, games, xTube: xTubeArg || api.X_TICKETS.tube, ...boardStats(),
  xWin: pct(r => r.winner === "x"), detWin: pct(r => r.winner === "d"), reasons, selfTrapByDestroyCard: selfTrap,
  avgCatchMove: caught.length ? +(caught.reduce((a, r) => a + r.moves, 0) / caught.length).toFixed(1) : null,
  avgCandidates: +(res.reduce((a, r) => a + r.avgPossible, 0) / games).toFixed(1),
  xTicketsUsedPerGame: Object.fromEntries(Object.entries(usedAvg).map(([k, v]) => [k, +v.toFixed(2)])),
}, null, 1));
