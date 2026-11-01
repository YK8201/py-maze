"""ステージ候補を自動生成するツール

    python tools/gen_levels.py --w 9 --h 9 --mud 1 --min-par 8 --count 5

ランダムな壁から作り、条件に合うものを出力する。床にはすべてドットが置かれる。
一度も通れないマスは壁で埋めるので、通路だけの見た目になる。

選ぶときの指標:
    par   : 最短手数
    dead  : 到達できる局面のうち、もうクリアできない（詰んだ）局面の割合。0 なら詰まない
    maze  : でたらめに動いたときにクリアまでにかかる平均手数 ÷ par。大きいほど迷いやすい
"""

import argparse
import os
import random
import sys
from collections import deque

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

from core import CRUMBLE, DIRS, EXIT, FLOOR, MUD, START, WALL, Level, step  # noqa: E402


def explore(level):
    """ゴールを開かせずに動き回り、通過できるマスの集合を返す"""
    s0 = level.initial_state()
    s0.dots = 1 << len(level.dots)  # どのドットとも関係ないビットを残してゴールを閉じたままにする
    seen = {s0.key()}
    cells = {s0.pos}
    q = deque([s0])
    while q:
        s = q.popleft()
        for d in DIRS:
            r = step(level, s, d)
            if r is None:
                continue
            ns, path, _ = r
            cells.update(path)
            if ns.key() not in seen:
                seen.add(ns.key())
                q.append(ns)
    return cells


def analyze(level, limit=200_000):
    """局面のグラフを全部作り、(par, dead, edges, start_key) を返す。大きすぎれば None"""
    s0 = level.initial_state()
    states = {s0.key(): s0}
    edges = {}
    order = [s0]
    dist = {s0.key(): 0}
    par = None
    i = 0
    while i < len(order):
        s = order[i]
        i += 1
        outs = []
        for d in DIRS:
            r = step(level, s, d)
            if r is None:
                continue
            ns = r[0]
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
        edges[s.key()] = outs
    if par is None:
        return None
    # クリアにつながる局面を、クリアから逆向きに広げて求める
    good = set()
    changed = True
    while changed:
        changed = False
        for k, outs in edges.items():
            if k not in good and any(o == "WIN" or o in good for o in outs):
                good.add(k)
                changed = True
    dead = 1 - len(good) / len(edges)
    return par, dead, edges, s0.key()


def wander(edges, start, rng, walkers=300, cap=3000):
    """でたらめに動くプレイヤーがクリアまでにかかる平均手数（cap で打ち切り）"""
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
            k = o
        total += n
    return total / walkers


def to_rows(grid):
    return ["".join(r) for r in grid]


def trim(rows):
    """外周の壁を1マスだけ残して切り詰める"""
    ys = [y for y, r in enumerate(rows) if r.strip(WALL)]
    xs = [x for x in range(len(rows[0])) if any(r[x] != WALL for r in rows)]
    return [r[min(xs) - 1 : max(xs) + 2] for r in rows[min(ys) - 1 : max(ys) + 2]]


def generate(rng, w, h, density, n_mud, n_crumble):
    g = [[WALL] * w for _ in range(h)]
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            g[y][x] = WALL if rng.random() < density else FLOOR
    floors = [(x, y) for y in range(h) for x in range(w) if g[y][x] == FLOOR]
    if len(floors) < 8 + n_mud + n_crumble:
        return None
    rng.shuffle(floors)
    sx, sy = floors.pop()
    g[sy][sx] = START
    for _ in range(n_mud):
        x, y = floors.pop()
        g[y][x] = MUD
    for _ in range(n_crumble):
        x, y = floors.pop()
        g[y][x] = CRUMBLE
    # 仮のゴールを置いて通れるマスを調べ、その中からゴールを選び直す
    ex, ey = floors[0]
    g[ey][ex] = EXIT
    cells = explore(Level(to_rows(g)))
    g[ey][ex] = FLOOR
    cand = [p for p in cells if g[p[1]][p[0]] == FLOOR]
    if not cand:
        return None
    ex, ey = rng.choice(cand)
    g[ey][ex] = EXIT
    # 通れないマスは壁にする
    cells = explore(Level(to_rows(g)))
    for y in range(h):
        for x in range(w):
            if (x, y) not in cells and g[y][x] != WALL:
                if g[y][x] in (EXIT, START):
                    return None
                g[y][x] = WALL
    return trim(to_rows(g))


def special_tiles_matter(rows, par):
    """ぬかるみ・崩れる床をただの床にすると手数が変わる（=意味がある）か"""
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c in (MUD, CRUMBLE):
                alt = [list(row) for row in rows]
                alt[y][x] = FLOOR
                a = analyze(Level(to_rows(alt)))
                if a is not None and a[0] == par:
                    return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--w", type=int, default=9)
    ap.add_argument("--h", type=int, default=9)
    ap.add_argument("--density", type=float, default=0.35)
    ap.add_argument("--mud", type=int, default=0)
    ap.add_argument("--crumble", type=int, default=0)
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
        rows = generate(rng, a.w, a.h, a.density, a.mud, a.crumble)
        if rows is None:
            continue
        res = analyze(Level(rows))
        if res is None:
            continue
        par, dead, edges, start = res
        if not (a.min_par <= par <= a.max_par) or dead > a.max_dead:
            continue
        maze = wander(edges, start, rng) / par
        if maze < a.min_maze:
            continue
        if not special_tiles_matter(rows, par):
            continue
        found += 1
        print(f"# par={par} dead={dead:.2f} maze={maze:.1f}")
        for r in rows:
            print(f'    "{r}",')
        print()
        if found >= a.count:
            break


if __name__ == "__main__":
    main()
