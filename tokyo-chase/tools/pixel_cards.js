  // ======================================================================
  // 切符カード（ドット絵）：クリーム色の台紙に赤い枠。上に走る人と枚数、真ん中に乗り物の絵、下に「○○ TICKETS」
  // 絵は小さなキャンバスに四角を並べて描き、拡大表示でドットを見せる（画像ファイルは使わない）
  // ======================================================================
  const PXC = { W: 48, H: 32 };
  const pxCache = new Map();
  const CARD_INFO = {
    taxi:  { no: "01", en: "TAXI",      ja: "タクシー", mark: "タ" },
    bus:   { no: "02", en: "BUS",       ja: "バス",     mark: "バ" },
    tube:  { no: "03", en: "SUBWAY",    ja: "地下鉄",   mark: "地" },
    boat:  { no: "04", en: "WATER BUS", ja: "水上バス（黒チケット・乗り物は隠れる）", mark: "船" },
    black: { no: "05", en: "BLACK",     ja: "黒チケット（乗り物を隠す）", mark: "黒" },
    heli:  { no: "06", en: "HELI",      ja: "ヘリ（ほかのヘリポートのどこかへ着陸）", mark: "H" },
  };
  function pxScene(kind) {
    if (pxCache.has(kind)) return pxCache.get(kind);
    const c = document.createElement("canvas");
    c.width = PXC.W; c.height = PXC.H;
    const g = c.getContext("2d");
    const r = (x, y, w, h, col) => { g.fillStyle = col; g.fillRect(x, y, w, h); };
    // 枠線つきの四角（1ドット外側に濃い色）
    const box = (x, y, w, h, col, ol = "#2A2230") => { r(x - 1, y - 1, w + 2, h + 2, ol); r(x, y, w, h, col); };
    const town = (base, win, y0) => {
      for (const [x, w, h] of [[0, 7, 9], [8, 5, 12], [14, 8, 7], [23, 6, 11], [30, 9, 8], [40, 8, 13]]) {
        r(x, y0 - h, w, h, base);
        for (let yy = y0 - h + 2; yy < y0 - 1; yy += 3) for (let xx = x + 1; xx < x + w - 1; xx += 2) r(xx, yy, 1, 1, win);
      }
    };
    if (kind === "taxi") {
      r(0, 0, 48, 32, "#A9CBE3"); town("#8FA3B5", "#D6E4EE", 21);
      r(0, 20, 48, 2, "#B9B4A8"); r(0, 22, 48, 10, "#55585C");
      for (let x = 1; x < 48; x += 7) r(x, 28, 4, 1, "#E9E9E4");
      box(9, 17, 28, 6, "#F2B51D"); box(15, 12, 15, 5, "#F2B51D");
      r(16, 13, 6, 4, "#BFE3F5"); r(23, 13, 6, 4, "#BFE3F5"); r(22, 13, 1, 4, "#F2B51D");
      box(20, 9, 5, 2, "#FFF3C4");
      for (let x = 9; x < 37; x += 2) r(x, 20, 1, 1, "#2A2230");
      r(36, 18, 1, 2, "#FFFBE0"); r(9, 18, 1, 2, "#E5484D");
      for (const x of [12, 28]) { box(x, 22, 5, 4, "#1E1E1E"); r(x + 1, 23, 3, 2, "#9A9A9A"); }
    } else if (kind === "bus") {
      r(0, 0, 48, 32, "#BFD8EA"); town("#A6B8C8", "#E4EEF5", 21);
      r(0, 20, 48, 2, "#B9B4A8"); r(0, 22, 48, 10, "#55585C");
      for (let x = 3; x < 48; x += 7) r(x, 28, 4, 1, "#E9E9E4");
      r(42, 6, 1, 17, "#6B6B6B"); box(39, 2, 7, 6, "#E8912D"); r(40, 4, 5, 1, "#FFF3C4"); r(40, 6, 3, 1, "#FFF3C4");
      box(3, 8, 33, 14, "#16935B");
      r(5, 10, 29, 5, "#CFEFF7");
      for (let x = 10; x < 34; x += 6) r(x, 10, 1, 5, "#0E6B3A");
      r(30, 10, 4, 11, "#0E6B3A"); r(31, 11, 2, 9, "#8FD1B0");
      r(3, 17, 33, 1, "#FBF7EA"); r(3, 20, 33, 2, "#0E6B3A");
      r(35, 18, 1, 2, "#FFE680");
      for (const x of [7, 25]) { box(x, 21, 5, 4, "#1E1E1E"); r(x + 1, 22, 3, 2, "#9A9A9A"); }
    } else if (kind === "tube") {
      r(0, 0, 48, 32, "#4A1C2C");
      for (const [i, col] of [[0, "#5E2438"], [4, "#6E2A42"], [8, "#7F334E"]]) { r(i, i, 48 - 2 * i, 1, col); r(i, i, 1, 32 - i, col); r(47 - i, i, 1, 32 - i, col); }
      for (let k = 0; k < 30; k++) r(18 + k, Math.floor(k / 3), 2, 1, k % 2 ? "#F2A03D" : "#F7C06A");
      for (let y = 22; y < 32; y++) r(0, y, 11 + Math.round((y - 22) * 1.3), 1, "#C98AA6");
      r(0, 22, 11, 1, "#E8B4CB");
      box(15, 6, 20, 24, "#C9A7B8", "#2A1620");
      r(16, 6, 18, 1, "#DBC0CD"); r(19, 7, 12, 2, "#2A1620"); r(21, 7, 8, 1, "#F4E9EF");
      r(17, 11, 7, 8, "#E86F3A"); r(26, 11, 7, 8, "#E86F3A"); r(24, 11, 2, 12, "#A98596");
      r(18, 12, 2, 3, "#F7A57E"); r(27, 12, 2, 3, "#F7A57E");
      r(18, 23, 2, 2, "#FFF6D0"); r(30, 23, 2, 2, "#FFF6D0");
      r(15, 27, 20, 2, "#2A1620"); r(4, 26, 1, 3, "#2A1620"); r(7, 25, 1, 4, "#2A1620");
    } else if (kind === "boat") {
      r(0, 0, 48, 32, "#BCD9EE"); town("#9BB0C2", "#E0EAF2", 15);
      r(0, 15, 48, 17, "#3F7FB8");
      for (let y = 18; y < 32; y += 3) for (let x = (y * 5) % 9; x < 48; x += 9) r(x, y, 3, 1, "#7FB0E6");
      box(11, 11, 22, 6, "#E8EEF4"); r(10, 10, 24, 1, "#2F7FB0");
      for (let x = 13; x < 31; x += 4) r(x, 13, 3, 2, "#2F4E79");
      box(5, 17, 34, 5, "#F4F4F0");
      r(5, 20, 34, 1, "#2F7FB0"); r(38, 16, 3, 1, "#F4F4F0"); r(39, 15, 3, 1, "#F4F4F0");
      r(19, 6, 1, 4, "#6B6B6B"); r(20, 6, 4, 2, "#E5484D");
      for (let x = 4; x < 42; x += 3) r(x, 23, 2, 1, "#DCEBF7");
    } else if (kind === "black") {
      r(0, 0, 48, 32, "#1C1830");
      for (const [x, y] of [[4, 3], [11, 7], [20, 2], [27, 9], [44, 12], [2, 13], [15, 14]]) r(x, y, 1, 1, "#E4DCC2");
      box(36, 3, 6, 6, "#F2E3A1", "#1C1830"); r(38, 4, 3, 3, "#E4D08A");
      town("#0C0A14", "#3A3450", 32);
      r(19, 8, 4, 4, "#000"); r(18, 12, 6, 7, "#000"); r(24, 13, 4, 2, "#000"); r(15, 14, 3, 2, "#000");
      r(18, 19, 3, 5, "#000"); r(22, 19, 3, 3, "#000"); r(24, 21, 3, 2, "#000"); r(16, 23, 3, 2, "#000");
      r(19, 9, 4, 1, "#C3242F");
      const q = ["0111", "1001", "0001", "0010", "0100", "0000", "0100"];
      q.forEach((row, y) => [...row].forEach((v, x) => { if (v === "1") r(33 + x * 2, 12 + y * 2, 2, 2, "#E3B341"); }));
    } else if (kind.startsWith("c_")) {
      pxHandScene(kind.slice(2), r, box, town);
    } else {   // heli
      r(0, 0, 48, 32, "#CFE3F5");
      for (const [x, y, w] of [[3, 4, 9], [30, 3, 12], [36, 6, 7]]) r(x, y, w, 2, "#F4F8FC");
      r(6, 25, 36, 5, "#6B6B6B"); r(7, 26, 34, 3, "#7E7E7E");
      r(21, 26, 1, 3, "#F2C230"); r(25, 26, 1, 3, "#F2C230"); r(22, 27, 3, 1, "#F2C230");
      r(5, 6, 36, 1, "#2A2230"); r(21, 7, 2, 3, "#2A2230");
      box(14, 10, 16, 9, "#7C3AED"); r(24, 11, 5, 5, "#CDEBFA"); r(25, 12, 2, 2, "#F4FBFF");
      r(2, 12, 13, 3, "#7C3AED"); r(1, 12, 1, 3, "#2A2230"); r(0, 9, 2, 9, "#4B2391");
      r(16, 19, 2, 3, "#2A2230"); r(26, 19, 2, 3, "#2A2230"); r(13, 21, 18, 1, "#2A2230");
      r(15, 12, 8, 1, "#9C6BF2");
    }
    const url = c.toDataURL("image/png");
    pxCache.set(kind, url);
    return url;
  }
  // 手札カード（特殊カード）の絵
  function pxHandScene(c, r, box, town) {
    const miniHeli = (x, y, col = "#7C3AED") => {
      r(x, y, 12, 1, "#2A2230"); r(x + 5, y + 1, 1, 1, "#2A2230");
      r(x + 3, y + 2, 7, 4, col); r(x + 7, y + 3, 2, 2, "#CDEBFA"); r(x - 2, y + 3, 5, 1, col);
      r(x + 3, y + 7, 7, 1, "#2A2230");
    };
    const runner = (x, y, col) => {
      r(x + 3, y, 3, 3, col); r(x + 2, y + 3, 4, 5, col); r(x + 6, y + 4, 3, 1, col); r(x, y + 4, 2, 1, col);
      r(x + 2, y + 8, 2, 4, col); r(x + 4, y + 8, 3, 2, col); r(x + 6, y + 10, 2, 2, col); r(x, y + 11, 2, 1, col);
    };
    if (c === "bridge") {
      r(0, 0, 48, 32, "#BCD9EE"); r(0, 20, 48, 12, "#3F7FB8");
      for (let x = 2; x < 48; x += 8) r(x, 26, 3, 1, "#7FB0E6");
      box(0, 15, 48, 4, "#9A9A96"); for (const x of [8, 38]) r(x, 19, 3, 9, "#6E6E6A");
      for (let x = 0; x < 48; x += 4) r(x, 13, 1, 2, "#6E6E6A"); r(0, 13, 48, 1, "#6E6E6A");
      for (let x = 14; x < 34; x += 4) { r(x, 8, 2, 3, "#E5484D"); r(x + 2, 8, 2, 3, "#FBF7EA"); }
      r(14, 7, 20, 1, "#2A2230"); r(14, 11, 20, 1, "#2A2230"); r(15, 12, 1, 3, "#2A2230"); r(32, 12, 1, 3, "#2A2230");
      r(22, 2, 4, 4, "#E5484D"); r(23, 3, 2, 2, "#FBF7EA");
    } else if (c === "checkpoint" || c === "rcheck") {
      r(0, 0, 48, 32, c === "rcheck" ? "#D9D2C0" : "#A9CBE3");
      if (c === "rcheck") { for (let x = 0; x < 48; x += 8) r(x, 0, 1, 20, "#B9B09A"); for (let y = 3; y < 20; y += 6) r(0, y, 48, 1, "#B9B09A"); }
      else town("#8FA3B5", "#D6E4EE", 20);
      r(0, 20, 48, 12, "#55585C"); for (let x = 1; x < 48; x += 7) r(x, 28, 4, 1, "#E9E9E4");
      for (const x of [9, 33]) r(x, 15, 2, 10, "#2A2230");
      for (let x = 6; x < 38; x += 4) { r(x, 13, 2, 3, "#E5484D"); r(x + 2, 13, 2, 3, "#FBF7EA"); }
      r(6, 12, 32, 1, "#2A2230"); r(6, 16, 32, 1, "#2A2230");
      for (const x of [2, 40]) { r(x + 2, 18, 2, 2, "#F28C28"); r(x + 1, 20, 4, 2, "#F28C28"); r(x + 2, 20, 2, 1, "#FBF7EA"); r(x, 22, 6, 1, "#2A2230"); }
      r(21, 8, 3, 3, "#2F7FE0"); r(24, 8, 3, 3, "#E5484D"); r(20, 11, 8, 1, "#2A2230");
      if (c === "rcheck") { const q = ["0110", "1001", "0010", "0100", "0000", "0100"]; q.forEach((row, y) => [...row].forEach((v, x) => { if (v === "1") r(38 + x * 2, 1 + y * 2, 2, 2, "#C3242F"); })); }
    } else if (c === "dash") {
      r(0, 0, 48, 32, "#CFE3F5");
      for (const [y, x, w] of [[6, 2, 14], [11, 0, 18], [16, 4, 12], [21, 1, 16], [26, 6, 10]]) r(x, y, w, 1, "#FFFFFF");
      r(0, 28, 48, 4, "#9A9A96");
      runner(22, 9, "#2F5FB8"); r(25, 9, 3, 1, "#1C3570"); r(24, 8, 5, 1, "#1C3570");
      for (const x of [34, 38]) { r(x, 12, 3, 2, "#E3B341"); r(x + 1, 11, 1, 4, "#E3B341"); }
    } else if (c === "heliban") {
      r(0, 0, 48, 32, "#CFE3F5"); r(6, 25, 36, 5, "#6B6B6B");
      r(21, 26, 1, 3, "#F2C230"); r(25, 26, 1, 3, "#F2C230"); r(22, 27, 3, 1, "#F2C230");
      miniHeli(18, 12);
      for (let a = 0; a < 64; a++) { const t = a / 64 * Math.PI * 2; r(Math.round(24 + Math.cos(t) * 12), Math.round(16 + Math.sin(t) * 12), 2, 2, "#E5484D"); }
      for (let k = -8; k <= 8; k++) r(24 + k, 16 + k, 2, 2, "#E5484D");
    } else if (c === "reinforce") {
      r(0, 0, 48, 32, "#CFE3F5");
      for (const [x, y, w] of [[3, 3, 9], [32, 4, 12]]) r(x, y, w, 2, "#F4F8FC");
      miniHeli(5, 8); miniHeli(20, 16); miniHeli(33, 8);
      r(0, 28, 48, 4, "#9A9A96");
      for (const [x, y] of [[16, 5], [30, 22], [44, 18]]) { r(x, y, 3, 1, "#2F5FB8"); r(x + 1, y - 1, 1, 3, "#2F5FB8"); }
    } else if (c === "trap") {
      r(0, 0, 48, 32, "#6B8F4E"); for (let y = 2; y < 32; y += 4) for (let x = (y * 3) % 7; x < 48; x += 7) r(x, y, 1, 2, "#86A866");
      box(10, 18, 28, 6, "#8A8A86"); r(22, 20, 4, 2, "#5A5A56");
      for (let x = 10; x < 38; x += 4) { r(x, 15, 2, 3, "#C9C9C4"); r(x + 1, 13, 1, 2, "#E9E9E4"); }
      r(10, 24, 28, 1, "#4A4A46"); r(36, 22, 8, 1, "#6E6E6A"); r(43, 20, 2, 5, "#6E6E6A");
    } else if (c === "vanish") {
      r(0, 0, 48, 32, "#2A2440");
      for (const [x, y] of [[3, 3], [40, 5], [30, 2], [8, 10]]) r(x, y, 1, 1, "#E4DCC2");
      runner(20, 12, "#4A4460");
      for (const [x, y, w, h] of [[8, 16, 12, 7], [16, 12, 14, 9], [26, 15, 14, 8], [12, 21, 26, 6], [34, 20, 8, 5]]) { r(x, y, w, h, "#D8D4E4"); r(x + 1, y, w - 2, 1, "#F4F2F8"); }
      for (const [x, y] of [[6, 12], [40, 13], [22, 8], [44, 24]]) r(x, y, 2, 2, "#B9B4CC");
    } else if (c === "destroy") {
      r(0, 0, 48, 32, "#3A2A2A"); r(0, 26, 48, 6, "#55585C");
      for (let a = 0; a < 12; a++) { const t = a / 12 * Math.PI * 2; for (let d = 4; d < 14; d++) r(Math.round(24 + Math.cos(t) * d), Math.round(15 + Math.sin(t) * d * 0.8), 2, 2, d < 9 ? "#F7C948" : "#E86F3A"); }
      r(18, 11, 12, 8, "#FFF3C4");
      box(14, 20, 20, 5, "#FBF7EA"); r(24, 20, 1, 5, "#2A2230"); r(23, 22, 1, 1, "#2A2230"); r(25, 21, 1, 1, "#2A2230");
      for (const [x, y] of [[6, 8], [40, 6], [8, 22], [41, 21], [34, 3]]) r(x, y, 2, 2, "#9A8A7A");
    } else if (c === "dog") {
      r(0, 0, 48, 32, "#D9D2C0"); r(0, 22, 48, 10, "#B9B09A");
      for (const [x, y] of [[30, 25], [35, 27], [40, 24], [45, 26]]) { r(x, y, 2, 2, "#6E5A40"); r(x - 1, y - 2, 1, 1, "#6E5A40"); r(x + 2, y - 2, 1, 1, "#6E5A40"); }
      box(8, 12, 16, 7, "#A0703C", "#3A2A1A");           // 胴
      box(22, 13, 7, 6, "#A0703C", "#3A2A1A");          // 頭（下向きにかいでいる）
      r(28, 17, 2, 2, "#2A2230"); r(23, 12, 2, 3, "#6E4A28");   // 鼻・耳
      r(25, 14, 1, 1, "#2A2230");
      r(9, 19, 2, 4, "#3A2A1A"); r(20, 19, 2, 4, "#3A2A1A"); r(13, 19, 2, 4, "#3A2A1A");
      r(5, 10, 3, 2, "#A0703C"); r(4, 9, 2, 1, "#A0703C");       // しっぽ
      r(17, 11, 5, 1, "#2F5FB8"); r(18, 12, 3, 1, "#E3B341");     // 首輪（警察）
      r(33, 5, 8, 6, "#FBF7EA"); r(34, 6, 2, 1, "#2A2230"); r(37, 6, 3, 1, "#2A2230"); r(34, 8, 6, 1, "#2A2230"); r(35, 11, 1, 1, "#FBF7EA");
    } else {   // miss
      r(0, 0, 48, 32, "#8A8680");
      const q = ["0111", "1001", "0001", "0010", "0100", "0000", "0100"];
      q.forEach((row, y) => [...row].forEach((v, x) => { if (v === "1") r(20 + x * 2, 8 + y * 2, 2, 2, "#D8D4CC"); }));
    }
  }
  function pxHandArt(c) { return pxScene("c_" + c); }
  // 走る人の小さなシルエット（カード左上）
  function pxRunner() {
    if (pxCache.has("runner")) return pxCache.get("runner");
    const rows = ["....11......", "...111......", "....1.......", "..11111.....", ".1.111.1....", "1..111..1...", "...111......", "...1.11.....", "..1...11....", ".1.....1....", "1......1...."];
    const c = document.createElement("canvas");
    c.width = 12; c.height = rows.length;
    const g = c.getContext("2d");
    g.fillStyle = "#9FB3C2";
    rows.forEach((row, y) => [...row].forEach((v, x) => { if (v === "1") g.fillRect(x, y, 1, 1); }));
    const url = c.toDataURL("image/png");
    pxCache.set("runner", url);
    return url;
  }
  // 切符カードのボタン。art は絵の種類（黒チケットで水上バスに乗るときは "boat"）、type は実際に使う切符
  function pxCard(art, cnt, type) {
    const info = CARD_INFO[art] || CARD_INFO.taxi;
    return `<button class="ticket pxcard ${type}" data-act="ticket" data-type="${type}" aria-label="${info.ja} 残り${cnt}">
      <span class="pc-top"><img class="pc-run" src="${pxRunner()}" alt=""><span class="pc-no">${info.no}</span><span class="pc-cnt">${cnt}</span><span class="pc-type ${art}">${info.mark}</span></span>
      <img class="pc-art" src="${pxScene(art)}" alt="">
      <span class="pc-bot"><span class="pc-chase">CHASE</span><span class="pc-title">${info.en}<br>TICKETS</span></span>
      <span class="pc-ja">${info.ja}</span>
    </button>`;
  }
  // 盤面に置く警察犬の駒（背景なしのドット絵。右向きで地面をかいでいる）
  function pxDogSprite() {
    if (pxCache.has("dogsprite")) return pxCache.get("dogsprite");
    const c = document.createElement("canvas");
    c.width = 28; c.height = 19;
    const g = c.getContext("2d");
    const r = (x, y, w, h, col) => { g.fillStyle = col; g.fillRect(x, y, w, h); };
    const O = "#2A1A0E", B = "#A0703C", Dk = "#6E4A28";
    r(4, 5, 16, 8, O); r(5, 6, 14, 6, B);                 // 胴
    r(18, 7, 9, 7, O); r(19, 8, 7, 5, B);                  // 頭（下向き）
    r(25, 11, 3, 3, O);                                     // 鼻
    r(19, 6, 3, 4, Dk); r(22, 9, 1, 1, O);                  // 耳・目
    r(6, 12, 3, 6, O); r(15, 12, 3, 6, O); r(10, 12, 2, 5, O); r(7, 13, 1, 4, B); r(16, 13, 1, 4, B);
    r(1, 2, 4, 2, O); r(0, 1, 2, 2, O); r(2, 3, 3, 1, B);   // しっぽ
    r(15, 5, 4, 2, "#2F5FB8"); r(16, 7, 2, 1, "#E3B341");  // 首輪（警察）
    r(7, 7, 6, 1, "#C08850");                               // 背中の光
    const url = c.toDataURL("image/png");
    pxCache.set("dogsprite", url);
    return url;
  }
