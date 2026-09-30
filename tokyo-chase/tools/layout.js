  // ======================================================================
  // 画面を4つに分ける：左上＝自分の視点の地図（固定）、右上＝プレイヤー情報と履歴、
  // 左下＝手札と無線、右下＝全体図（ほかの駒の動き・カードの対象や遠い行き先もここで選べる）
  // ======================================================================
  (function setupLayout() {
    const app = $("app");
    app.classList.add("layout4");
    const pane = (id, cls) => { const d = document.createElement("div"); d.id = id; d.className = "pane " + cls; app.insertBefore(d, $("sheet")); return d; };
    const info = pane("paneInfo", "info"), cards = pane("paneCards", "cards"), mini = pane("paneMini", "mini");
    info.appendChild(document.querySelector(".hud.top"));
    const drawer = $("drawer");
    drawer.hidden = false;
    drawer.querySelector(".row").innerHTML = `<b>履歴</b><button class="btn ghost hint-btn" data-act="hint" aria-pressed="true" title="怪盗Xがいるかもしれない駅を表示">推理ヒント</button>`;
    info.appendChild(drawer);
    cards.appendChild($("handbar"));
    const talk = document.createElement("div");
    talk.id = "talkLog"; talk.className = "talklog";
    talk.innerHTML = `<div class="tl-h">無線・コメント</div><ul></ul>`;
    cards.appendChild(talk);
    mini.innerHTML = `<div class="mini-h">全体図<span>駅をタップ：遠い行き先・カードの対象を選ぶ</span></div>
      <svg id="mini" viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid meet" aria-label="全体図">
        <rect x="0" y="0" width="${W}" height="${H}" fill="#C6C6C1"></rect>
        <use href="#worldIn"></use>
        <g id="miniMarks"></g>
      </svg>`;
    // 全体図のタップ：いちばん近い駅を選ぶ（自分の番の行き先・カードの対象）
    $("mini").addEventListener("click", e => {
      const svg = $("mini"), pt = svg.createSVGPoint();
      pt.x = e.clientX; pt.y = e.clientY;
      const q = pt.matrixTransform(svg.getScreenCTM().inverse());
      let best = -1, bd = 110;
      STATIONS.forEach(([, x, y], i) => { const d = Math.hypot(x - q.x, y - q.y); if (d < bd) { bd = d; best = i; } });
      if (best >= 0) onStationTap(best);
    });
  })();

  // 全体図の上の印：各刑事の視界（画面の範囲）と、自分の視界
  function renderMini() {
    const g = $("miniMarks"), G = A.G;
    if (!g) return;
    g.replaceChildren();
    if (!G || G.over) return;
    const me = viewAnchor();
    G.det.forEach((d, k) => {
      const [x, y] = P(d.pos);
      el("rect", { x: x - VIEW_W / 2, y: y - VIEW_H / 2, width: VIEW_W, height: VIEW_H, class: "mini-view", stroke: DCOL[k] }, g);
    });
    if (me !== null && me !== undefined) {
      const [x, y] = P(me);
      el("rect", { x: x - VIEW_W / 2, y: y - VIEW_H / 2, width: VIEW_W, height: VIEW_H, class: "mini-me" }, g);
    }
  }

  // 自分の視点の地図：刑事の視界（VIEW_W×VIEW_H）の外側を暗くする
  function renderViewMask() {
    const g = $("viewMask"), G = A.G;
    if (!g) return;
    g.replaceChildren();
    const pos = G && !G.over ? viewAnchor() : null;
    if (pos === null || pos === undefined) return;
    const isDet = A.role === "d" || (A.role === "pass" && G.turn !== "x" && A.cover !== "x-open");
    if (!isDet) return;
    const [x, y] = P(pos), x0 = x - VIEW_W / 2, y0 = y - VIEW_H / 2, big = 6000;
    for (const [rx, ry, rw, rh] of [[x0 - big, y0 - big, big * 2 + VIEW_W, big], [x0 - big, y0 + VIEW_H, big * 2 + VIEW_W, big], [x0 - big, y0, big, VIEW_H], [x0 + VIEW_W, y0, big, VIEW_H]])
      el("rect", { x: rx, y: ry, width: rw, height: rh, class: "view-shade" }, g);
    el("rect", { x: x0, y: y0, width: VIEW_W, height: VIEW_H, class: "view-frame" }, g);
  }

  // 無線・コメントの一覧（吹き出しと同じ内容を残す）
  function renderTalkLog() {
    const ul = document.querySelector("#talkLog ul");
    if (!ul) return;
    ul.innerHTML = (A.radio || []).slice(0, 12).map(m => `<li>${portrait("d", m.k, "sm")}<span><b>${m.me ? "あなた" : dName(m.k)}</b>${esc(m.text)}</span></li>`).join("") || `<li class="empty">まだ無線はありません</li>`;
  }
