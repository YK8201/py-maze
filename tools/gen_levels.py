"""氷の湖のステージ候補を自動生成するツール

    python tools/gen_levels.py --w 9 --h 9 --water 3 --thin 2 --min-par 8 --count 5

長方形の湖に岩・水・もろい氷をランダムに置き、スタートと町（ゴール）を岸に置く。
条件に合うものを出力する。

選ぶときの指標:
    par   : 最短手数
    dead  : 到達できる局面のうち、もうゴールできない（詰んだ）局面の割合。0 なら詰まない
    maze  : でたらめに動いたときにゴールまでにかかる平均手数 ÷ par。大きいほど迷いやすい
            （詰んだらスタートからやり直すものとして数える）
    falls : 水に落ちる手がある局面の割合。大きいほど「うっかり落ちる」危険が多い
"""

import argparse
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

from core import DIRS, EXIT, ICE, ROCK, START, THIN, WATER, Level, step  # noqa: E402


def analyze(level, limit=200_000):
    """局面のグラフを全部作り、(par, dead, falls, edges, start_key, fall_tiles, good) を返す。
    fall_tiles は実際に落ちうる水のマス、good はゴールにつながる局面の集合。
    解けないか大きすぎれば None"""
    s0 = level.initial_state()
    states = {s0.key(): s0}
    dist = {s0.key(): 0}
    edges = {}
    order = [s0]
    par = None
    risky = 0
    fall_tiles = set()
    i = 0
    while i < len(order):
        s = order[i]
        i += 1
        outs = []
        fall_here = False
        for d in DIRS:
            r = step(level, s, d)
            if r is None:
                continue
            ns, path, fell = r
            if fell:
                fall_here = True
                fall_tiles.add(path[-1])
                continue
            if ns.won:
                outs.append("WIN")
                if par is None or dist[s.key()] + 1 < par:
                    par = dist[s.key()] + 1
                continue
            k = ns.key()
            outs.append(k)
            if k not in states:
                states[k] = ns
                dist[k] = dist[s.key()] + 1
                order.append(ns)
                if len(states) > limit:
                    return None
        risky += fall_here
        edges[s.key()] = outs
    if par is None:
        return None
    # ゴールにつながる局面を、ゴールから逆向きに広げて求める
    good = set()
    changed = True
    while changed:
        changed = False
        for k, outs in edges.items():
            if k not in good and any(o == "WIN" or o in good for o in outs):
                good.add(k)
                changed = True
    dead = 1 - len(good) / len(edges)
    return par, dead, risky / len(edges), edges, s0.key(), fall_tiles, good


def wander(edges, start, rng, good=None, walkers=300, cap=3000):
    """でたらめに動くプレイヤーがゴールまでにかかる平均手数（cap で打ち切り）。
    good を渡すと、詰んだ局面に入ったらスタートからやり直す（ゲームが STUCK と教えるので）"""
    total = 0
    for _ in range(walkers):
        k = start
        n = 0
        while n < cap:
            if not edges[k]:  # どこにも動けない
                n = cap
                break
            o = rng.choice(edges[k])
            n += 1
            if o == "WIN":
                break
            k = o if good is None or o in good else start
        total += n
    return total / walkers


def to_rows(grid):
    return ["".join(r) for r in grid]


def shore_cell(rng, w, h, side):
    """岸（外周）のマスを1つ選ぶ。角は使わない"""
    if side == 0:
        return rng.randrange(1, w - 1), 0
    if side == 1:
        return rng.randrange(1, w - 1), h - 1
    if side == 2:
        return 0, rng.randrange(1, h - 1)
    return w - 1, rng.randrange(1, h - 1)


def generate(rng, w, h, rocks, n_water, n_thin):
    """w×h（外周の岸を含む）の湖を作る"""
    g = [[ROCK] * w for _ in range(h)]
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            g[y][x] = ROCK if rng.random() < rocks else ICE
    ice = [(x, y) for y in range(1, h - 1) for x in range(1, w - 1) if g[y][x] == ICE]
    if len(ice) < n_water + n_thin + 4:
        return None
    rng.shuffle(ice)
    for _ in range(n_water):
        x, y = ice.pop()
        g[y][x] = WATER
    for _ in range(n_thin):
        x, y = ice.pop()
        g[y][x] = THIN
    # スタートは下か左の岸、町は上か右の岸
    sx, sy = shore_cell(rng, w, h, rng.choice((1, 2)))
    ex, ey = shore_cell(rng, w, h, rng.choice((0, 3)))
    g[sy][sx] = START
    g[ey][ex] = EXIT
    return to_rows(g)


def special_tiles_matter(rows, res):
    """水・もろい氷のうち、解き方に効いているものの数を種類ごとに返す。
    水: 実際に落ちうる場所にある（うっかり落ちる危険になっている）
    もろい氷: ただの氷にすると、最短手数か詰む局面の割合が変わる"""
    par, dead, _, _, _, fall_tiles, _ = res
    count = {WATER: 0, THIN: 0}
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c == WATER and (x, y) in fall_tiles:
                count[WATER] += 1
            elif c == THIN:
                alt = [list(row) for row in rows]
                alt[y][x] = ICE
                b = analyze(Level(to_rows(alt)))
                if b is None or b[0] != par or abs(b[1] - dead) > 1e-9:
                    count[THIN] += 1
    return count


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--w", type=int, default=9, help="岸を含めた横幅")
    ap.add_argument("--h", type=int, default=9, help="岸を含めた高さ")
    ap.add_argument("--rocks", type=float, default=0.15, help="岩の割合")
    ap.add_argument("--water", type=int, default=2)
    ap.add_argument("--thin", type=int, default=0)
    ap.add_argument("--min-par", type=int, default=6)
    ap.add_argument("--max-par", type=int, default=99)
    ap.add_argument("--max-dead", type=float, default=0.0, help="0 なら詰む局面のないものだけ")
    ap.add_argument("--min-maze", type=float, default=0.0, help="迷いやすさの下限")
    ap.add_argument("--count", type=int, default=5)
    ap.add_argument("--tries", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=None)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    found = 0
    for _ in range(a.tries):
        rows = generate(rng, a.w, a.h, a.rocks, a.water, a.thin)
        if rows is None:
            continue
        res = analyze(Level(rows))
        if res is None:
            continue
        par, dead, falls, edges, start, _, good = res
        if not (a.min_par <= par <= a.max_par) or dead > a.max_dead:
            continue
        maze = wander(edges, start, rng, good) / par
        if maze < a.min_maze:
            continue
        matter = special_tiles_matter(rows, res)
        if (a.water and not matter[WATER]) or (a.thin and not matter[THIN]):
            continue
        found += 1
        print(f"# par={par} dead={dead:.2f} maze={maze:.1f} falls={falls:.2f}")
        for r in rows:
            print(f'    "{r}",')
        print()
        if found >= a.count:
            break


if __name__ == "__main__":
    main()
