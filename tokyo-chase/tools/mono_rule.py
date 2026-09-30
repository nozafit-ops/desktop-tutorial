# モノレールと、怪盗Xのヘリ（sim.js と make_demo.py の両方で使う。view_rule.py・strong_cards.py のあとに当てる）
#  - モノレール（mono）：新しい乗り物。刑事は使い放題、怪盗Xは切符 MONO_X 枚
#  - 怪盗Xはヘリをいつでも使える（切符 X_HELI_N 枚。カード「ヘリ」は山札から外す）
#   python3 mono_rule.py MONO_X X_HELI_N → [old, new] の組を JSON で出す
import json, sys

def patches(mono_x=6, heli_n=99):
    return [
        ["    heli:  { name: \"ヘリ\", en: \"Helicopter\", short: \"H\" },",
         "    mono:  { name: \"モノレール\", en: \"Monorail\", short: \"モ\" },\n"
         "    heli:  { name: \"ヘリ\", en: \"Helicopter\", short: \"H\" },"],
        ["  const DET_TYPES = [\"taxi\", \"bus\", \"tube\", \"boat\", \"heli\"];",
         "  const DET_TYPES = [\"taxi\", \"bus\", \"tube\", \"mono\", \"boat\", \"heli\"];"],
        ["  const MOVE_TYPES = [\"taxi\", \"bus\", \"tube\", \"boat\"];",
         "  const MOVE_TYPES = [\"taxi\", \"bus\", \"tube\", \"mono\", \"boat\"];"],
        ["  for (const [line, seq] of BOATS) for (let k = 0; k < seq.length - 1; k++) addEdge(seq[k], seq[k + 1], \"boat\", line);",
         "  for (const [line, seq] of BOATS) for (let k = 0; k < seq.length - 1; k++) addEdge(seq[k], seq[k + 1], \"boat\", line);\n"
         "  for (const [a, b] of MONO) addEdge(a, b, \"mono\", \"モノレール\");"],
        ["  const X_HELI = 0;", f"  const X_HELI = {heli_n};   // 怪盗Xはヘリをいつでも使える"],
        [", [\"xheli\", 24]", ""],
    ]

def x_tickets(line, mono_x):
    """X_TICKETS の行に mono を足す"""
    return line.replace(" };", f", mono: {mono_x} }};")

if __name__ == "__main__":
    print(json.dumps(patches(int(sys.argv[1]), int(sys.argv[2])), ensure_ascii=False))
