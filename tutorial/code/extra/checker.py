# 湖が「詰むか」と「どれくらい迷うか」を調べるプログラム
# solver.py・levels.py と同じフォルダに置いて、python checker.py で実行する
import random
from collections import deque

from levels import LEVELS
from solver import DIRECTIONS, make_key, slide, solve, start_state


def all_states(level):
    """スタートからたどり着ける局面を全部集める。
    戻り値は (スタートの局面, 局面ごとの湖, 局面ごとの「次の局面のリスト」)。
    町に着く動きは、次の局面を "CLEAR" と書いておく"""
    grid, x, y = start_state(level)
    start = make_key(grid, x, y)
    boards = {start: (grid, x, y)}
    nexts = {}
    queue = deque([start])
    while queue:
        key = queue.popleft()
        grid, x, y = boards[key]
        nexts[key] = []
        for dx, dy in DIRECTIONS.values():
            result = slide(grid, x, y, dx, dy)
            if result is None:
                continue
            new_grid, nx, ny, won = result
            if won:
                nexts[key].append("CLEAR")
                continue
            new_key = make_key(new_grid, nx, ny)
            nexts[key].append(new_key)
            if new_key not in boards:
                boards[new_key] = (new_grid, nx, ny)
                queue.append(new_key)
    return start, boards, nexts


def find_ok(nexts):
    """町につながる局面の集合を返す。これに入らない局面は詰んでいる"""
    ok = set()
    changed = True
    while changed:  # 「町につながる局面」が増えなくなるまでくり返す
        changed = False
        for key, next_keys in nexts.items():
            if key in ok:
                continue
            for n in next_keys:
                if n == "CLEAR" or n in ok:
                    ok.add(key)
                    changed = True
                    break
    return ok


def wander(start, nexts, ok, players=300, limit=3000):
    """でたらめに動くプレイヤーが、町に着くまでに平均何手かかるか。
    詰んだらスタートからやり直す（手数はそのまま数え続ける）"""
    total = 0
    for _ in range(players):
        key = start
        moves = 0
        while moves < limit:
            if len(nexts[key]) == 0:  # どこにも動けない
                key = start
                continue
            key = random.choice(nexts[key])
            moves += 1
            if key == "CLEAR":
                break
            if key not in ok:  # 詰んだらやり直し
                key = start
        total += moves
    return total / players


def show(grid, x, y):
    """局面を文字で表示する。P がプレイヤー"""
    for row_y, row in enumerate(grid):
        line = "".join(row)
        if row_y == y:
            line = line[:x] + "P" + line[x + 1 :]
        print("    " + line)


for i, level in enumerate(LEVELS):
    answer = solve(level)
    if answer is None:
        print(f"{i + 1} {level['name']}: 解けません！")
        continue
    start, boards, nexts = all_states(level)
    ok = find_ok(nexts)
    stuck = [key for key in nexts if key not in ok]
    score = wander(start, nexts, ok) / len(answer)
    print(f"{i + 1} {level['name']}: 局面 {len(nexts)}個  詰み {len(stuck)}個  迷い度 {score:.1f}")
    if stuck:
        # 詰んだ局面の例を1つ見せる（割れた氷が少ないものを選ぶ）
        key = min(stuck, key=lambda k: k[2].count("~"))
        print("  たとえばこの局面からは、もう町に行けません:")
        show(*boards[key])
