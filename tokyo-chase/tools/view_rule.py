# 新しいルール（sim.js と make_demo.py の両方で使う）
#  - 視界は「刑事を真ん中にした画面の範囲」（横 VIEW_W × 縦 VIEW_H の長方形）。円の視界の代わり
#    メインの地図はこの範囲をそのまま映すので、画面に怪盗Xが入った＝発見
#  - ヘリはヘリカードを引いたときだけ使える（怪盗X・刑事とも、最初のヘリ切符は0枚）
#     怪盗X：カード「ヘリ」＝ヘリ切符1枚。刑事：カード「ヘリ出動」＝刑事全員にヘリ切符1枚
#   python3 view_rule.py VIEW_W VIEW_H → [old, new] の組を JSON で出す
import json, sys

def patches(vw, vh):
    inrect = f"Math.abs(STATIONS[d.pos][1] - STATIONS[q][1]) <= {vw / 2} && Math.abs(STATIONS[d.pos][2] - STATIONS[q][2]) <= {vh / 2}"
    return [
        ["  const inSight = (G, p) => G.det.some(d => Math.hypot(STATIONS[d.pos][1] - STATIONS[p][1], STATIONS[d.pos][2] - STATIONS[p][2]) <= SIGHT);",
         f"  const VIEW_W = {vw}, VIEW_H = {vh};   // 刑事の視界＝画面の範囲（盤面の座標）\n"
         "  const inView = (d, q) => " + inrect + ";\n"
         "  const inSight = (G, p) => G.det.some(d => inView(d, p));"],
        ["    const wit = G.det.findIndex(d => { const r = q => Math.hypot(STATIONS[d.pos][1] - STATIONS[q][1], STATIONS[d.pos][2] - STATIONS[q][2]) <= SIGHT; return r(from) || r(to); });",
         "    const wit = G.det.findIndex(d => inView(d, from) || inView(d, to));"],
        # ---- ヘリはカードでだけ ----
        ["  const X_HELI = 1;", "  const X_HELI = 0;"],
        ["    trap:      { side: \"x\", name: \"罠\",",
         "    xheli:     { side: \"x\", name: \"ヘリ\", desc: \"ヘリの切符を1枚得る。ヘリポートの駅から、ほかのヘリポートのどこかへ飛べる。\" },\n"
         "    trap:      { side: \"x\", name: \"罠\","],
        ["    x: [[\"trap\", 34], [\"vanish\", 33], [\"destroy\", 33]],",
         "    x: [[\"trap\", 34], [\"vanish\", 33], [\"destroy\", 33], [\"xheli\", 24]],"],
        ["    else if (card === \"trap\") sec.trap = sec.pos;",
         "    else if (card === \"trap\") sec.trap = sec.pos;\n    else if (card === \"xheli\") G.heli += 1;"],
        ["        if (c === \"trap\") use = use || dmin <= 3;",
         "        if (c === \"xheli\") use = true;\n        if (c === \"trap\") use = use || dmin <= 3;"],
    ]

# 刑事側：最初のヘリ切符0枚、山札に「ヘリ出動」（応援要請の名前を変えたもの）
def det_patches(det_ticket_line):
    return [
        [det_ticket_line, det_ticket_line.replace("heli: 1", "heli: 0")],
        ["[\"dog\", 16]],", "[\"dog\", 16], [\"reinforce\", 22]],"],
        ["    reinforce: { side: \"d\", name: \"応援要請\", desc: \"刑事全員にヘリの切符が1枚ずつ追加される。\" },",
         "    reinforce: { side: \"d\", name: \"ヘリ出動\", desc: \"刑事全員にヘリの切符が1枚ずつ追加される。ヘリポートの駅から、ほかのヘリポートのどこかへ飛べる。\" },"],
    ]

if __name__ == "__main__":
    print(json.dumps(patches(float(sys.argv[1]), float(sys.argv[2])) + det_patches("const DET_TICKETS = { heli: 1 };"), ensure_ascii=False))
