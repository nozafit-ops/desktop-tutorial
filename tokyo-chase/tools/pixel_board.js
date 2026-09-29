  // ======================================================================
  // ドット絵風の盤面：灰色の街に、斜め見下ろしのビル・木・公園・水面をコードで描く
  // 道路・バス・地下鉄は、縦横と45度の線でつなぎ、角を丸める（地下鉄の路線図風）
  // ======================================================================
  const PX = 3;   // 背景の1ドットが盤面の何単位か（大きいほどドットが粗い）

  // 駅 a→b を、縦横の直線と45度の斜めで結ぶ折れ線（端は縦横、真ん中が斜め）
  function octPts(a, b, off = 0) {
    const [x1, y1] = P(a), [x2, y2] = P(b);
    const dx = x2 - x1, dy = y2 - y1, ax = Math.abs(dx), ay = Math.abs(dy);
    const sx = Math.sign(dx) || 1, sy = Math.sign(dy) || 1;
    let pts;
    if (ax >= ay) { const run = (ax - ay) / 2; pts = [[x1, y1], [x1 + sx * run, y1], [x2 - sx * run, y2], [x2, y2]]; }
    else { const run = (ay - ax) / 2; pts = [[x1, y1], [x1, y1 + sy * run], [x2, y2 - sy * run], [x2, y2]]; }
    if (off) {
      const L = Math.hypot(dx, dy) || 1, nx = -dy / L * off, ny = dx / L * off;
      pts = pts.map(([x, y]) => [x + nx, y + ny]);
    }
    return pts.filter((p, i) => i === 0 || Math.hypot(p[0] - pts[i - 1][0], p[1] - pts[i - 1][1]) > 0.5);
  }
  // 折れ線の角を丸めた SVG の path
  function roundPath(pts, r = 34) {
    let d = `M${pts[0][0].toFixed(1)},${pts[0][1].toFixed(1)}`;
    for (let i = 1; i < pts.length - 1; i++) {
      const [px, py] = pts[i - 1], [cx, cy] = pts[i], [nx, ny] = pts[i + 1];
      const l1 = Math.hypot(cx - px, cy - py), l2 = Math.hypot(nx - cx, ny - cy);
      const k = Math.min(r, l1 / 2, l2 / 2);
      const ax = cx - (cx - px) / l1 * k, ay = cy - (cy - py) / l1 * k;
      const bx = cx + (nx - cx) / l2 * k, by = cy + (ny - cy) / l2 * k;
      d += ` L${ax.toFixed(1)},${ay.toFixed(1)} Q${cx.toFixed(1)},${cy.toFixed(1)} ${bx.toFixed(1)},${by.toFixed(1)}`;
    }
    const e = pts[pts.length - 1];
    return d + ` L${e[0].toFixed(1)},${e[1].toFixed(1)}`;
  }

  async function renderBackground() {
    const img = $("bgimg");
    const cw = Math.ceil(W / PX), ch = Math.ceil(H / PX);
    const c = document.createElement("canvas");
    c.width = cw; c.height = ch;
    const g = c.getContext("2d");
    g.imageSmoothingEnabled = false;
    let seed = 20260929;
    const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
    const px = v => Math.round(v / PX);
    // 地面と歩道のタイル
    g.fillStyle = "#C6C6C1"; g.fillRect(0, 0, cw, ch);
    for (let y = 0; y < ch; y += 6) for (let x = (y / 6) % 2 * 3; x < cw; x += 6) { g.fillStyle = "#CDCDC8"; g.fillRect(x, y, 3, 3); }
    // 水：湾と大川
    const bay = new Path2D();
    const last = COAST[COAST.length - 1];
    [...COAST, [W + 400, last[1]], [W + 400, H + 400], [COAST[0][0], H + 400]].forEach(([x, y], i) => i ? bay.lineTo(px(x), px(y)) : bay.moveTo(px(x), px(y)));
    bay.closePath();
    const river = new Path2D();
    RIVER.forEach(([x, y], i) => i ? river.lineTo(px(x), px(y)) : river.moveTo(px(x), px(y)));
    g.lineJoin = "round"; g.lineCap = "round";
    g.fillStyle = "#E4DCC2"; g.strokeStyle = "#E4DCC2"; g.lineWidth = px(122); g.stroke(river);
    g.save(); g.translate(0, -2); g.fill(bay); g.restore();
    g.fillStyle = "#4E86C8"; g.strokeStyle = "#4E86C8"; g.lineWidth = px(108); g.stroke(river); g.fill(bay);
    g.lineWidth = px(108);
    const wet = (x, y) => g.isPointInPath(bay, x, y) || g.isPointInStroke(river, x, y);
    for (let y = 2; y < ch; y += 5) for (let x = (y * 7) % 11; x < cw; x += 11) {
      if (wet(x, y) && wet(x + 4, y)) { g.fillStyle = rnd() < 0.5 ? "#7FB0E6" : "#6A9FDA"; g.fillRect(x, y, 3, 1); }
    }
    // 島
    for (const i of ISLAND_LIST) {
      const [x, y] = P(i);
      g.fillStyle = "#E4DCC2"; g.beginPath(); g.ellipse(px(x), px(y), px(124), px(84), 0, 0, Math.PI * 2); g.fill();
      g.fillStyle = "#7DBB5E"; g.beginPath(); g.ellipse(px(x), px(y) - 2, px(100), px(62), 0, 0, Math.PI * 2); g.fill();
    }
    // 道・線路の通り道（ビルを置かない）
    const segs = [];
    for (const key of edgeTypes.keys()) {
      const [a, b] = key.split("-").map(Number);
      const pts = octPts(a, b).map(([x, y]) => [x / PX, y / PX]);
      for (let k = 0; k < pts.length - 1; k++) segs.push([pts[k], pts[k + 1]]);
    }
    const segD = (x, y, a, b) => {
      const vx = b[0] - a[0], vy = b[1] - a[1], L = vx * vx + vy * vy || 1;
      const t = Math.max(0, Math.min(1, ((x - a[0]) * vx + (y - a[1]) * vy) / L));
      return Math.hypot(x - a[0] - vx * t, y - a[1] - vy * t);
    };
    const nearRoad = (x, y, d) => segs.some(([a, b]) => segD(x, y, a, b) < d);
    const nearSt = (x, y, d) => STATIONS.some(s => Math.hypot(s[1] / PX - x, s[2] / PX - y) < d);
    // 公園（木の多い緑地）
    const parks = [];
    for (let t = 0; t < 800 && parks.length < 9; t++) {
      const x = 30 + rnd() * (cw - 60), y = 30 + rnd() * (ch - 60), rw = 16 + rnd() * 14, rh = 10 + rnd() * 8;
      if (wet(x, y) || nearRoad(x, y, Math.max(rw, rh) + 4) || nearSt(x, y, Math.max(rw, rh) + 16)) continue;
      parks.push([x, y, rw, rh]);
      g.fillStyle = "#5E9E4A"; g.fillRect(Math.round(x - rw - 1), Math.round(y - rh - 1), Math.round(rw * 2 + 2), Math.round(rh * 2 + 2));
      g.fillStyle = "#79B862"; g.fillRect(Math.round(x - rw), Math.round(y - rh), Math.round(rw * 2), Math.round(rh * 2));
      if (rnd() < 0.5) { g.fillStyle = "#4E86C8"; g.fillRect(Math.round(x - rw / 2), Math.round(y - rh / 3), Math.round(rw * 0.8), Math.round(rh * 0.6)); }
    }
    const inPark = (x, y) => parks.some(([cx, cy, rw, rh]) => Math.abs(x - cx) < rw + 2 && Math.abs(y - cy) < rh + 2);
    // 木
    const tree = (x, y) => {
      g.fillStyle = "#6B4A2E"; g.fillRect(x, y + 2, 1, 2);
      g.fillStyle = "#2F6B34"; g.fillRect(x - 2, y - 2, 5, 4); g.fillRect(x - 1, y - 3, 3, 6);
      g.fillStyle = "#4F9A4A"; g.fillRect(x - 1, y - 2, 3, 3);
      g.fillStyle = "#79C466"; g.fillRect(x - 1, y - 2, 1, 1);
    };
    // 斜め見下ろしのビル（正面・右の側面・屋根）
    const PAL = [
      ["#E9E9E4", "#C3C3BE", "#9C9C97", "#8FB4D8"],   // 白いビル・青い窓
      ["#BFD4EA", "#8FB2D6", "#6B8FB8", "#E6F2FF"],   // ガラス張り
      ["#D9CDB4", "#B9AB8E", "#948768", "#6E6252"],   // ベージュ
      ["#C8C8C4", "#A2A29D", "#7E7E79", "#5B5B57"],   // 灰色
      ["#D99A7A", "#B87658", "#935A40", "#F2D2A8"],   // レンガ
    ];
    const building = (x, y) => {
      const p = PAL[Math.floor(rnd() * PAL.length)];
      const w = 5 + Math.floor(rnd() * 6), d = 3 + Math.floor(rnd() * 3), h = 4 + Math.floor(rnd() * (rnd() < 0.2 ? 20 : 9));
      const bx = Math.round(x - w / 2), by = Math.round(y);
      g.fillStyle = "rgba(0,0,0,0.18)"; g.fillRect(bx + 1, by, w + d, 2);                       // 影
      g.fillStyle = p[1]; g.fillRect(bx, by - h, w, h);                                           // 正面
      for (let k = 0; k < d; k++) { g.fillStyle = p[2]; g.fillRect(bx + w + k, by - h - k - 1, 1, h + 1); }   // 側面
      for (let k = 0; k < d; k++) { g.fillStyle = p[0]; g.fillRect(bx + k + 1, by - h - k - 1, w, 1); }       // 屋根
      g.fillStyle = p[3];
      for (let wy = by - h + 2; wy < by - 1; wy += 2) for (let wx = bx + 1; wx < bx + w - 1; wx += 2) if (rnd() < 0.8) g.fillRect(wx, wy, 1, 1);
    };
    // 街区にビルと木を並べる（下の段から描くと重なりが自然）
    const spots = [];
    for (let y = 8; y < ch - 2; y += 8) for (let x = 6; x < cw - 4; x += 9) {
      const jx = x + (rnd() - 0.5) * 4, jy = y + (rnd() - 0.5) * 3;
      if (wet(jx, jy) || wet(jx + 8, jy - 8) || inPark(jx, jy) || nearRoad(jx, jy, 10) || nearRoad(jx + 4, jy - 8, 10) || nearSt(jx, jy, 20)) continue;
      spots.push([jx, jy]);
    }
    spots.sort((p, q) => p[1] - q[1]);
    for (const [x, y] of spots) { const r = rnd(); if (r < 0.62) building(x, y); else if (r < 0.85) tree(Math.round(x), Math.round(y)); }
    for (const [cx, cy, rw, rh] of parks) for (let k = 0; k < rw * rh / 18; k++) tree(Math.round(cx + (rnd() - 0.5) * rw * 1.7), Math.round(cy + (rnd() - 0.5) * rh * 1.6));
    img.setAttribute("href", c.toDataURL("image/png"));
  }

  function buildBoard() {
    const gE = $("gEdges"), gS = $("gStations"), gL = $("gLabels");
    const layers = { taxi: el("g", {}, gE), bus: el("g", {}, gE), tube: el("g", {}, gE), boat: el("g", {}, gE) };
    for (const [key, types] of edgeTypes) {
      const [a, b] = key.split("-").map(Number);
      const g_ = t => { const g = el("g", {}, layers[t]); el("title", {}, g).textContent = types.get(t).join("・"); return g; };
      if (types.has("taxi")) {
        const d = roundPath(octPts(a, b)), g = g_("taxi");
        el("path", { d, class: "rd rd-out" }, g); el("path", { d, class: "rd rd-in" }, g);
      }
      const rails = ["bus", "tube"].filter(t => types.has(t));
      rails.forEach((t, k) => {
        const off = types.has("taxi") ? (k === 0 ? 11 : -11) : (rails.length > 1 ? (k === 0 ? 8 : -8) : 0);
        const d = roundPath(octPts(a, b, off)), g = g_(t);
        el("path", { d, class: `ln ${t}-ln` }, g); el("path", { d, class: `ln ${t}-dash` }, g);
      });
      if (types.has("boat")) {
        const pts = BOAT_PATH.has(key) ? BOAT_PATH.get(key) : [P(a), P(b)];
        const d = "M" + pts.map(p => p[0].toFixed(1) + "," + p[1].toFixed(1)).join(" L"), g = g_("boat");
        el("path", { d, class: "edge boat casing", "stroke-linejoin": "round" }, g);
        el("path", { d, class: "edge boat", "stroke-linejoin": "round" }, g);
      }
    }
    // 駅：白い楕円の台。地下鉄の駅は赤。バス停は緑の札、水上バスの桟橋は青の札
    STATIONS.forEach(([name, x, y], i) => {
      const g = el("g", {}, gS);
      const has = t => ADJ[i].some(e => e.type === t);
      if (HELI_SET.has(i)) {
        el("circle", { cx: x, cy: y, r: 44, class: "helipad" }, g);
        el("text", { x: x + 36, y: y - 28, class: "heli-h" }, g).textContent = "H";
      }
      if (BRIDGE_ST.includes(i)) el("rect", { x: x - 30, y: y - 30, width: 60, height: 60, rx: 6, class: "bridge-pt", transform: `rotate(45 ${x} ${y})` }, g);
      el("ellipse", { cx: x, cy: y + 7, rx: 30, ry: 19, class: "st-shadow" }, g);
      el("ellipse", { cx: x, cy: y + 3, rx: 29, ry: 19, class: "st-side" + (has("tube") ? " sub" : "") }, g);
      el("ellipse", { cx: x, cy: y, rx: 29, ry: 18, class: "st-top" + (has("tube") ? " sub" : "") }, g);
      el("ellipse", { cx: x - 8, cy: y - 7, rx: 10, ry: 4, class: "st-hi" }, g);
      const tags = [has("bus") && "bus", has("boat") && "boat"].filter(Boolean);
      tags.forEach((t, k) => el("rect", { x: x + 20 + k * 11, y: y - 24, width: 9, height: 9, class: "st-tag " + t }, g));
      el("text", { x, y: y + 6, class: "stn-num" + (has("tube") ? " on-sub" : "") }, g).textContent = NO(i);
      el("text", { x, y: y + 48, class: "stn-label", id: "lbl" + i }, gL).textContent = name;
    });
  }

