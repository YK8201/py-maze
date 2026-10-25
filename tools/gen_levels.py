"""ステージ候補を自動生成するツール

    python tools/gen_levels.py --w 9 --h 11 --dots 4 --mud 1 --min-par 8 --count 5

ランダムな壁から作り、ソルバーで最短手数(par)を求めて条件に合うものを出力する。
一度も通れないマスは壁で埋めるので、通路だけの見た目になる。
"""

import argparse
import os
import random
import sys
from collections import deque

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

from core import CRUMBLE, DIRS, DOT, EXIT, FLOOR, MUD, START, WALL, Level, step  # noqa: E402
from solver import solve  # noqa: E402


def explore(level):
    """ドットとゴールを無視して到達できる (状態集合, 通過マス集合) を返す"""
    s0 = level.initial_state()
    s0.dots = 1  # ゴールを開かせない
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
    return seen, cells


def dead_end_ratio(level):
    """到達可能な状態のうち、もうクリアできない状態の割合（考えどころの目安）"""
    s0 = level.initial_state()
    edges = {}
    order = [s0]
    states = {s0.key(): s0}
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
            outs.append(ns.key())
            if ns.key() not in states and not ns.won:
                states[ns.key()] = ns
                order.append(ns)
            elif ns.won:
                outs[-1] = "WIN"
        edges[s.key()] = outs
    good = set()
    changed = True
    while changed:
        changed = False
        for k, outs in edges.items():
            if k in good:
                continue
            if any(o == "WIN" or o in good for o in outs):
                good.add(k)
                changed = True
    return 1 - len(good) / max(1, len(edges))


def to_rows(grid):
    return ["".join(r) for r in grid]


def trim(rows):
    """外周の壁を1マスだけ残して切り詰める"""
    ys = [y for y, r in enumerate(rows) if r.strip(WALL)]
    xs = [x for x in range(len(rows[0])) if any(r[x] != WALL for r in rows)]
    return [r[min(xs) - 1 : max(xs) + 2] for r in rows[min(ys) - 1 : max(ys) + 2]]


def generate(rng, w, h, density, n_dots, n_mud, n_crumble):
    g = [[WALL] * w for _ in range(h)]
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            g[y][x] = WALL if rng.random() < density else FLOOR
    floors = [(x, y) for y in range(h) for x in range(w) if g[y][x] == FLOOR]
    if len(floors) < 10:
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
    # 仮のゴールを置いて通れるマスを調べる
    ex, ey = floors[0]
    g[ey][ex] = EXIT
    _, cells = explore(Level(to_rows(g)))
    g[ey][ex] = FLOOR
    cand = [p for p in cells if g[p[1]][p[0]] == FLOOR]
    if len(cand) < n_dots + 1:
        return None
    rng.shuffle(cand)
    ex, ey = cand.pop()
    g[ey][ex] = EXIT
    for _ in range(n_dots):
        x, y = cand.pop()
        g[y][x] = DOT
    # 通れないマスは壁にする
    _, cells = explore(Level(to_rows(g)))
    for y in range(h):
        for x in range(w):
            if (x, y) not in cells and g[y][x] != WALL:
                if g[y][x] in (DOT, EXIT, START):
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
                m = solve(Level(to_rows(alt)))
                if m is not None and len(m) == par:
                    return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--w", type=int, default=9)
    ap.add_argument("--h", type=int, default=9)
    ap.add_argument("--density", type=float, default=0.3)
    ap.add_argument("--dots", type=int, default=3)
    ap.add_argument("--mud", type=int, default=0)
    ap.add_argument("--crumble", type=int, default=0)
    ap.add_argument("--min-par", type=int, default=6)
    ap.add_argument("--max-par", type=int, default=99)
    ap.add_argument("--min-dead", type=float, default=0.0)
    ap.add_argument("--count", type=int, default=5)
    ap.add_argument("--tries", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=None)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    found = 0
    for _ in range(a.tries):
        rows = generate(rng, a.w, a.h, a.density, a.dots, a.mud, a.crumble)
        if rows is None:
            continue
        lv = Level(rows)
        moves = solve(lv, limit=300_000)
        if moves is None or not (a.min_par <= len(moves) <= a.max_par):
            continue
        dead = dead_end_ratio(lv)
        if dead < a.min_dead:
            continue
        if not special_tiles_matter(rows, len(moves)):
            continue
        found += 1
        print(f"# par={len(moves)} dead={dead:.2f}")
        for r in rows:
            print(f'    "{r}",')
        print()
        if found >= a.count:
            break


if __name__ == "__main__":
    main()
