"""迷路のルール（ゲーム本体とソルバーで共有する）

タイル:
    #  壁
    .  ドット（全部集めるとゴールが開く）
    E  ゴール
    S  スタート
    o  ぬかるみ（上を通ると止まる）
    x  崩れる床（一度離れると壁になる）
    ' ' 床
"""

WALL = "#"
FLOOR = " "
DOT = "."
EXIT = "E"
START = "S"
MUD = "o"
CRUMBLE = "x"

UP, DOWN, LEFT, RIGHT = 0, 1, 2, 3
DIRS = {UP: (0, -1), DOWN: (0, 1), LEFT: (-1, 0), RIGHT: (1, 0)}


class Level:
    def __init__(self, rows):
        self.h = len(rows)
        self.w = max(len(r) for r in rows)
        self.grid = [list(r.ljust(self.w, WALL)) for r in rows]
        self.dots = []
        self.crumbles = []
        self.start = None
        self.exit = None
        for y, row in enumerate(self.grid):
            for x, c in enumerate(row):
                if c == DOT:
                    self.dots.append((x, y))
                elif c == CRUMBLE:
                    self.crumbles.append((x, y))
                elif c == START:
                    self.start = (x, y)
                    row[x] = FLOOR
                elif c == EXIT:
                    self.exit = (x, y)
        if self.start is None or self.exit is None:
            raise ValueError("level needs S and E")
        self.dot_index = {p: i for i, p in enumerate(self.dots)}
        self.crumble_index = {p: i for i, p in enumerate(self.crumbles)}

    def tile(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.grid[y][x]
        return WALL

    def initial_state(self):
        return State(
            self.start, (1 << len(self.dots)) - 1, (1 << len(self.crumbles)) - 1
        )

    def is_blocked(self, x, y, crumble_mask):
        t = self.tile(x, y)
        if t == WALL:
            return True
        if t == CRUMBLE:
            return not (crumble_mask >> self.crumble_index[(x, y)]) & 1
        return False


class State:
    """pos: プレイヤー位置, dots: 残りドットのビット, crumbles: 残っている崩れる床のビット"""

    __slots__ = ("pos", "dots", "crumbles", "won")

    def __init__(self, pos, dots, crumbles, won=False):
        self.pos = pos
        self.dots = dots
        self.crumbles = crumbles
        self.won = won

    def key(self):
        return (self.pos, self.dots, self.crumbles)


def step(level, state, d):
    """方向 d に滑らせる。動けなければ None。
    戻り値: (新しい State, 通過したマスのリスト[始点含む], 拾ったドット位置のリスト)"""
    dx, dy = DIRS[d]
    x, y = state.pos
    dots = state.dots
    crumbles = state.crumbles
    path = [(x, y)]
    picked = []
    won = False
    while True:
        nx, ny = x + dx, y + dy
        if level.is_blocked(nx, ny, state.crumbles):
            break
        x, y = nx, ny
        path.append((x, y))
        t = level.tile(x, y)
        if t == DOT:
            bit = 1 << level.dot_index[(x, y)]
            if dots & bit:
                dots &= ~bit
                picked.append((x, y))
        if t == EXIT and dots == 0:
            won = True
            break
        if t == MUD:
            break
    if len(path) == 1:
        return None
    # 離れたマスの崩れる床は壁になる（止まったマスはまだ残る）
    for p in path[:-1]:
        i = level.crumble_index.get(p)
        if i is not None:
            crumbles &= ~(1 << i)
    return State((x, y), dots, crumbles, won), path, picked
