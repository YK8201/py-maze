# 最短手数をコンピュータに求めさせるプログラム
# levels.py と同じフォルダに置いて、python solver.py で実行する
from collections import deque

from levels import LEVELS

# 向きの名前と (dx, dy)
DIRECTIONS = {"U": (0, -1), "D": (0, 1), "L": (-1, 0), "R": (1, 0)}


def count_dots(grid):
    n = 0
    for row in grid:
        n += row.count(".")
    return n


def slide(grid, x, y, dx, dy):
    """ゲームと同じルールで1手だけ滑らせる。
    動けなければ None、動けたら (新しい迷路, x, y, クリアしたか) を返す"""
    if grid[y + dy][x + dx] == "#":
        return None
    grid = [row[:] for row in grid]  # 元の迷路をこわさないようにコピー
    while True:
        if grid[y][x] == "x":
            grid[y][x] = "#"
        x += dx
        y += dy
        tile = grid[y][x]
        if tile == ".":
            grid[y][x] = " "
        if tile == "E" and count_dots(grid) == 0:
            return grid, x, y, True
        if tile == "o" or grid[y + dy][x + dx] == "#":
            return grid, x, y, False


def solve(level):
    """幅優先探索で最短の手順を見つける。見つからなければ None"""
    grid = [list(row) for row in level["map"]]
    for y in range(len(grid)):
        for x in range(len(grid[y])):
            if grid[y][x] == "S":
                sx, sy = x, y
                grid[y][x] = " "
    queue = deque()  # これから調べる状態の行列（先に入れたものから取り出す）
    queue.append((grid, sx, sy, ""))
    seen = set()  # もう調べた状態
    while queue:
        grid, x, y, path = queue.popleft()
        for name, (dx, dy) in DIRECTIONS.items():
            result = slide(grid, x, y, dx, dy)
            if result is None:
                continue
            new_grid, nx, ny, won = result
            if won:
                return path + name
            # 「位置」と「迷路のようす」が同じなら同じ状態とみなす
            key = (nx, ny, "".join("".join(row) for row in new_grid))
            if key in seen:
                continue
            seen.add(key)
            queue.append((new_grid, nx, ny, path + name))
    return None


for i, level in enumerate(LEVELS):
    answer = solve(level)
    if answer is None:
        print(f"{i + 1} {level['name']}: 解けません！")
    else:
        print(f"{i + 1} {level['name']}: {len(answer)}手 {answer}  (par {level['par']})")
