"""氷の湖のルール（ゲーム本体とソルバーで共有する）

『レイトン教授と超文明Aの遺産』のナゾ「氷の湖」を参考にしたルール。

タイル:
    #   岩・岸（ぶつかると手前で止まる）
    ' ' 氷（止まらずに滑り続ける）
    x   もろい氷（乗っても通ってもよいが、離れると割れて水になる）
    ~   水（入ると落ちる。その手は失敗）
    S   スタート
    E   町（ゴール）。着いたらクリア
"""

ROCK = "#"
ICE = " "
THIN = "x"
WATER = "~"
START = "S"
EXIT = "E"

UP, DOWN, LEFT, RIGHT = 0, 1, 2, 3
DIRS = {UP: (0, -1), DOWN: (0, 1), LEFT: (-1, 0), RIGHT: (1, 0)}


class Level:
    def __init__(self, rows):
        self.h = len(rows)
        self.w = max(len(r) for r in rows)
        self.grid = [list(r.ljust(self.w, ROCK)) for r in rows]
        self.thins = []
        self.start = None
        self.exit = None
        for y, row in enumerate(self.grid):
            for x, c in enumerate(row):
                if c == THIN:
                    self.thins.append((x, y))
                elif c == START:
                    self.start = (x, y)
                    row[x] = ICE
                elif c == EXIT:
                    self.exit = (x, y)
        if self.start is None or self.exit is None:
            raise ValueError("level needs S and E")
        self.thin_index = {p: i for i, p in enumerate(self.thins)}

    def tile(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.grid[y][x]
        return ROCK

    def initial_state(self):
        return State(self.start, (1 << len(self.thins)) - 1)

    def tile_now(self, x, y, thin_mask):
        """割れたもろい氷を水として返す"""
        t = self.tile(x, y)
        if t == THIN and not (thin_mask >> self.thin_index[(x, y)]) & 1:
            return WATER
        return t


class State:
    """pos: プレイヤー位置, thins: まだ割れていないもろい氷のビット"""

    __slots__ = ("pos", "thins", "won")

    def __init__(self, pos, thins, won=False):
        self.pos = pos
        self.thins = thins
        self.won = won

    def key(self):
        return (self.pos, self.thins)


def step(level, state, d):
    """方向 d に滑らせる。
    岩が目の前にあって動けなければ None。
    戻り値: (新しい State, 通過したマスのリスト[始点含む], 水に落ちたか)
    落ちたときの State は落ちる直前のようすで、ゲームではこの手を取り消す"""
    dx, dy = DIRS[d]
    x, y = state.pos
    path = [(x, y)]
    won = False
    fell = False
    while True:
        nx, ny = x + dx, y + dy
        t = level.tile_now(nx, ny, state.thins)
        if t == ROCK:
            break
        x, y = nx, ny
        path.append((x, y))
        if t == WATER:
            fell = True
            break
        if t == EXIT:
            won = True
            break
    if len(path) == 1:
        return None
    # 離れたもろい氷は割れて水になる（止まったマスはまだ割れない）
    thins = state.thins
    for p in path[:-1]:
        i = level.thin_index.get(p)
        if i is not None:
            thins &= ~(1 << i)
    return State((x, y), thins, won), path, fell
