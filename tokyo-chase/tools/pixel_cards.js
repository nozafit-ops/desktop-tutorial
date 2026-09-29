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
