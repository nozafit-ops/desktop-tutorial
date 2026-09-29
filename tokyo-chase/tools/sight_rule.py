# 「視界」ルール：怪盗Xは決まった手数で姿を現すのではなく、刑事の視界（半径 SIGHT の円）に入ったら姿が見えて発見される
#  - 刑事の視界の中の駅には、怪盗Xはいない（いれば見えている）ので、候補から外れる
#  - 雲隠れのカードは「次に見つかるのを1回だけなかったことにする」
# ロンドン版の CORE（ルールとCPU）への差し替えを [元の文字列, 新しい文字列] の組で持つ。
# シミュレーター（sim.js）とデモ版（make_demo.py）の両方がこの一覧を使うので、ルールは必ず同じになる
import json, os, sys

def patches(sight, partial=True):
    """partial=True：怪盗Xの乗り物は、乗った駅か降りた駅が誰かの視界に入っていたときだけ刑事にわかる"""
    return _sight(sight) + (_partial() if partial else [])

def _partial():
    return [
        ("    sec.pos = to;\n", "    const from = sec.pos;\n    sec.pos = to;\n"),
        # k=1：乗り物が刑事に見られた（w=見た刑事の番号）。k=0：誰も見ていない（刑事には「？」）
        ("    G.xLog.push({ t: type, p: rev ? to : null, d: useDouble ? 1 : (G.doubling ? 2 : 0), v: vanished ? 1 : 0 });",
         "    const wit = G.det.findIndex(d => { const r = q => Math.hypot(STATIONS[d.pos][1] - STATIONS[q][1], STATIONS[d.pos][2] - STATIONS[q][2]) <= SIGHT; return r(from) || r(to); });\n"
         "    const known = type === \"pass\" || wit >= 0;\n"
         "    G.xLog.push({ t: type, p: rev ? to : null, d: useDouble ? 1 : (G.doubling ? 2 : 0), v: vanished ? 1 : 0, k: known ? 1 : 0, w: wit });"),
        ("    G.possible = rev ? [to] : nextPossible(G, type);",
         "    G.possible = rev ? [to] : nextPossible(G, known ? type : \"black\");"),
        # CPUの刑事の推理も、見られていない手は乗り物がわからないものとして扱う
        ("      const t = G.xLog[i].t, nx = new Map();",
         "      const t = G.xLog[i].k === 0 ? \"black\" : G.xLog[i].t, nx = new Map();"),
    ]

def _sight(sight):
    return [
        # 公開の手番はなくす
        ("const REVEAL = [3, 6, 9, 12, 15, 18, 21];",
         f"const REVEAL = [];\n  const SIGHT = {sight};   // 刑事の視界の半径（盤面の座標）\n"
         "  const inSight = (G, p) => G.det.some(d => Math.hypot(STATIONS[d.pos][1] - STATIONS[p][1], STATIONS[d.pos][2] - STATIONS[p][2]) <= SIGHT);"),
        # 候補の駅：刑事の視界の中は除く
        ("    if (type === \"heli\") return HELI.filter(h => !occ.has(h) && !isClosed(G.closedX, h, G));",
         "    if (type === \"heli\") return HELI.filter(h => !occ.has(h) && !isClosed(G.closedX, h, G) && !inSight(G, h));"),
        ("    if (type === \"pass\") return G.possible.filter(p => !occ.has(p));",
         "    if (type === \"pass\") return G.possible.filter(p => !occ.has(p) && !inSight(G, p));"),
        ("      if ((type === \"black\" || e.type === type) && !occ.has(e.to) && !isClosed(G.closedX, e.to, G)) nx.add(e.to);",
         "      if ((type === \"black\" || e.type === type) && !occ.has(e.to) && !isClosed(G.closedX, e.to, G) && !inSight(G, e.to)) nx.add(e.to);"),
        # 怪盗Xが動いた先が視界の中なら見つかる
        ("    let rev = REVEAL.includes(n), vanished = false;",
         "    let rev = REVEAL.includes(n) || inSight(G, to), vanished = false;"),
        # 刑事が動いて、怪盗Xが視界に入ったら見つかる。入らなければ視界の中の駅は候補から外れる
        ("    G.possible = G.possible.filter(p => p !== to);",
         "    if (sec && inSight(G, sec.pos)) {\n"
         "      if (G.skipReveal > 0) { G.skipReveal--; G.possible = G.possible.filter(p => p !== to); }\n"
         "      else { G.possible = [sec.pos]; G.lastSeen = { pos: sec.pos, n: G.xLog.length }; }\n"
         "    } else {\n"
         "      const left = G.possible.filter(p => p !== to && !inSight(G, p));\n"
         "      G.possible = left.length ? left : G.possible.filter(p => p !== to);\n"
         "    }"),
        # 雲隠れ：次に見つかるのを1回だけ防ぐ。CPUは刑事が近いときに使う
        ("        if (c === \"vanish\") use = use || (REVEAL.includes(G.xLog.length + 1) && !(G.skipReveal > 0));",
         "        if (c === \"vanish\") use = use || (dmin <= 3 && !(G.skipReveal > 0));"),
        ("    vanish:    { side: \"x\", name: \"雲隠れ\", desc: \"次の目撃情報を1回だけ無効にする。\" },",
         "    vanish:    { side: \"x\", name: \"雲隠れ\", desc: \"次に刑事の視界に入っても、1回だけ見つからない。\" },"),
        # CPUの怪盗Xは刑事の視界に入る駅を避ける
        ("    if (dmin <= 1) s -= 40;",
         "    if (dmin <= 1) s -= 40;\n    if (inSight(G, to)) s -= 25;"),
    ]

if __name__ == "__main__":
    json.dump(patches(float(sys.argv[1]), (sys.argv[2] if len(sys.argv) > 2 else "1") == "1"), sys.stdout, ensure_ascii=False)
