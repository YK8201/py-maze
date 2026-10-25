"""幅優先探索で最短手数を求める。python solver.py で全ステージを検証する。"""

from collections import deque

from core import DIRS, Level, step


def solve(level, limit=2_000_000):
    """最短手順（方向のリスト）を返す。解けなければ None。"""
    start = level.initial_state()
    prev = {start.key(): None}
    queue = deque([start])
    while queue:
        s = queue.popleft()
        for d in DIRS:
            r = step(level, s, d)
            if r is None:
                continue
            ns = r[0]
            k = ns.key()
            if k in prev:
                continue
            prev[k] = (s.key(), d)
            if ns.won:
                moves = []
                while prev[k] is not None:
                    k, d2 = prev[k]
                    moves.append(d2)
                return moves[::-1]
            if len(prev) > limit:
                return None
            queue.append(ns)
    return None


if __name__ == "__main__":
    from levels import LEVELS

    ok = True
    for i, lv in enumerate(LEVELS, 1):
        moves = solve(Level(lv["map"]))
        n = None if moves is None else len(moves)
        mark = "OK" if n == lv["par"] else "NG"
        if mark == "NG":
            ok = False
        print(f"{i:2d} {lv['name']:<12} par={lv['par']:>3} solved={n} {mark}")
    raise SystemExit(0 if ok else 1)
