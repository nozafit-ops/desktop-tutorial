# CPUの刑事に性格を持たせる（sim.js と make_demo.py の両方で使う）
#  - 追いかけ（chase）：怪盗Xがいそうな駅・最後に見た駅へまっすぐ詰める
#  - 先回り（cut）  ：怪盗Xが次に逃げそうな駅（ほかの刑事から遠い側）へ回り込む
#  - 待ち伏せ（ambush）：候補の多い一帯の中で、地下鉄駅など乗り換えの多い駅を押さえて待つ
# 候補が少なくなった終盤（先読み）は、性格に関係なく全員で追い詰める
#   python3 persona.py  → [old, new] の組を JSON で出す
import json, sys

def patches():
    return [
        ["  function aiD(G, k, steady = false) {",
         """  // CPUの刑事の性格（刑事モードでは刑事1＝あなた、仲間は刑事2から 先回り・待ち伏せ・追いかけ の順）
  const PERS_BY_K = ["chase", "cut", "ambush", "chase", "cut"];
  const PERS_NAME = { chase: "追いかけ", cut: "先回り", ambush: "待ち伏せ" };
  let HUB_ = null;
  const hubOf = i => (HUB_ ||= ADJ.map(a => new Set(a.map(e => e.to)).size + (a.some(e => e.type === "tube") ? 3 : 0) + (a.some(e => e.type === "bus") ? 1 : 0)))[i];
  function aiD(G, k, steady = false) {"""],
        ["""    const others = G.det.filter((_, j) => j !== k).map(o => o.pos);
    const scoreAt = to => {""",
         """    const others = G.det.filter((_, j) => j !== k).map(o => o.pos);
    const per = PERS_BY_K[k];
    // 先回り用：候補駅の隣で、ほかの刑事から遠い（＝怪盗Xが逃げ込みそうな）駅ほど重くする
    const AHEAD = new Map();
    if (per === "cut") for (const [p, w] of W) {
      const qs = [...new Set(ADJ[p].map(e => e.to))];
      const fl = qs.map(q => 1 + Math.min(4, 9, ...others.map(o => D[q][o])));
      const tot = fl.reduce((a, b) => a + b, 0) || 1;
      qs.forEach((q, i) => AHEAD.set(q, (AHEAD.get(q) || 0) + w * fl[i] / tot));
    }
    const scoreAt = to => {"""],
        ["""      return prob * AI_PROB - ed * 4 + spread + look + mateV;""",
         """      let extra = 0;
      if (per === "chase") extra = prob * AI_PROB * 0.8 - ed * 4 - (G.lastSeen ? Math.min(D[to][G.lastSeen.pos], 6) * 2 : 0) - spread * 0.5;
      else if (per === "cut") { let e2 = 0; for (const [q, w] of AHEAD) e2 += dd(to, q) * w; extra = ed * 2.5 - e2 * 5 - prob * AI_PROB * 0.4; }
      else if (per === "ambush") { let cov = 0; for (const [p, w] of W) if (D[to][p] <= 2) cov += w; extra = ed * 3 + cov * 26 + hubOf(to) * 1.6 + spread * 1.5; }
      if (G.possible.length <= 6) extra *= 0.3;   // 終盤は性格より全員で詰める
      return prob * AI_PROB - ed * 4 + spread + look + mateV + extra;"""],
    ]

if __name__ == "__main__":
    print(json.dumps(patches(), ensure_ascii=False))
