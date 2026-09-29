# 追加ルール（sim.js と make_demo.py の両方で使う）
#  - 相棒を確保したら、怪盗Xはそれから先ずっと居場所が見える（毎手「目撃」扱い）
#  - 刑事のカード「警察犬」：2手前・3手前にいた駅（足跡）がわかり、そこから今いそうな駅を絞り込む
#   python3 dog_mate.py [dogWeight=16]  → [old, new] の組を JSON で出す
import json, sys

def patches(dog_weight=16):
    return [
        # ---- 相棒確保で常に見える ----
        ["    let rev = REVEAL.includes(n) || inSight(G, to), vanished = false;",
         "    const mateOut = !!G.mate && !!G.mate.out;   // 相棒を確保されたら、もう隠れられない\n"
         "    let rev = REVEAL.includes(n) || inSight(G, to) || mateOut, vanished = false;"],
        ["    const known = type === \"pass\" || wit >= 0;",
         "    const known = type === \"pass\" || wit >= 0 || mateOut;"],
        ["    if (sec && inSight(G, sec.pos)) {",
         "    if (sec && (inSight(G, sec.pos) || (G.mate && G.mate.out))) {"],
        # ---- 警察犬 ----
        ["    reinforce: { side: \"d\", name: \"応援要請\",",
         "    dog:       { side: \"d\", name: \"警察犬\", desc: \"怪盗Xの足跡をかぎ分ける。2手前と3手前にいた駅がわかり、今いそうな駅を絞り込む。\" },\n"
         "    reinforce: { side: \"d\", name: \"応援要請\","],
        ["    d: [[\"bridge\", 22], [\"checkpoint\", 33], [\"dash\", 10], [\"heliban\", 18], [\"rcheck\", 17]],",
         f"    d: [[\"bridge\", 22], [\"checkpoint\", 33], [\"dash\", 10], [\"heliban\", 18], [\"rcheck\", 17], [\"dog\", {dog_weight}]],"],
        ["    else if (card === \"heliban\") G.heliBan = n + 5;",
         """    else if (card === "heliban") G.heliBan = n + 5;
    else if (card === "dog") {
      // 足跡：2手前・3手前の駅。2手前の駅から、その後の2手（見えた乗り物、見えなければ何でも）でたどれる駅に絞る
      const L = G.xLog.length;
      if (L >= 1) {
        const i0 = Math.max(0, L - 2), iOld = Math.max(0, L - 3);
        const trail = [...new Set([iOld, i0])].map(i => ({ n: i, pos: sec.path[i], dog: true }));
        let ps = [sec.path[i0]];
        for (let i = i0; i < L; i++) {
          const e = G.xLog[i], t = e.t === "pass" ? "pass" : e.t === "heli" ? "heli" : (e.k ? e.t : "black");
          if (t === "heli") { ps = HELI.slice(); continue; }
          if (t === "pass") continue;
          const nx = new Set();
          for (const s of ps) for (const ed of ADJ[s]) if (t === "black" || ed.type === t) nx.add(ed.to);
          ps = [...nx];
        }
        const cur = new Set(G.possible);
        let np = ps.filter(p => cur.has(p));
        if (!np.includes(sec.pos)) np = ps.includes(sec.pos) ? ps : G.possible;   // 念のため（本当の駅は必ず残す）
        G.possible = np.sort((a, b) => a - b);
        G.seen = [...(G.seen || []), ...trail].sort((a, b) => a.n - b.n);
        G.dogUsed = { n, trail: trail.map(t => t.pos) };
      }
    }"""],
        ["        if (c === \"reinforce\") use = use || G.det.every(d => d.t.heli === 0);",
         "        if (c === \"reinforce\") use = use || G.det.every(d => d.t.heli === 0);\n"
         "        if (c === \"dog\") use = use || (G.xLog.length >= 2 && G.possible.length >= 8);"],
    ]

if __name__ == "__main__":
    print(json.dumps(patches(int(sys.argv[1]) if len(sys.argv) > 1 else 16), ensure_ascii=False))
