# 怪盗Xの強いカード（sim.js と make_demo.py の両方で使う。view_rule.py のあとに当てる）
#  - 煙幕：刑事全員が1回休み
#  - 変装：これから3手のあいだ、刑事の視界に入っても見つからない
#   python3 strong_cards.py [重み=18] → [old, new] の組を JSON で出す
import json, sys

def patches(w=18):
    return [
        ["    xheli:     { side: \"x\", name: \"ヘリ\",",
         "    smoke:     { side: \"x\", name: \"煙幕\", desc: \"煙幕をはる。刑事全員が1回休みになる。\" },\n"
         "    disguise:  { side: \"x\", name: \"変装\", desc: \"これから3手のあいだ、刑事の視界に入っても見つからない。\" },\n"
         "    xheli:     { side: \"x\", name: \"ヘリ\","],
        ["[\"xheli\", 24]],", f"[\"xheli\", 24], [\"smoke\", {w}], [\"disguise\", {w}]],"],
        ["    else if (card === \"xheli\") G.heli += 1;",
         "    else if (card === \"xheli\") G.heli += 1;\n"
         "    else if (card === \"smoke\") { G.stun = { ...(G.stun || {}) }; G.det.forEach((_, k) => { G.stun[k] = Math.max(1, G.stun[k] || 0); }); }\n"
         "    else if (card === \"disguise\") G.disguise = n + 3;"],
        ["        if (c === \"xheli\") use = true;",
         "        if (c === \"xheli\") use = true;\n"
         "        if (c === \"smoke\") use = use || dmin <= 2;\n"
         "        if (c === \"disguise\") use = use || (dmin <= 3 && !(G.disguise > G.xLog.length));"],
        # 変装中は見つからない（自分の手・刑事の手とも）
        ["    if (rev && G.skipReveal > 0) { G.skipReveal--; rev = false; vanished = true; }   // 雲隠れ",
         "    if (rev && G.skipReveal > 0) { G.skipReveal--; rev = false; vanished = true; }   // 雲隠れ\n"
         "    if (rev && G.disguise >= n && !REVEAL.includes(n)) rev = false;   // 変装"],
        ["    if (sec && (inSight(G, sec.pos) || (G.mate && G.mate.out))) {",
         "    if (sec && (inSight(G, sec.pos) || (G.mate && G.mate.out)) && !(G.disguise > G.xLog.length)) {"],
    ]

if __name__ == "__main__":
    print(json.dumps(patches(int(sys.argv[1]) if len(sys.argv) > 1 else 18), ensure_ascii=False))
