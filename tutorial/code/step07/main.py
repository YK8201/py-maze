import pyxel

TILE = 8

MAP = [
    "#######",
    "#.   S#",
    "# #####",
    "# #E  #",
    "# ### #",
    "#    .#",
    "#######",
]


class App:
    def __init__(self):
        pyxel.init(128, 160, title="SLIDE MAZE")
        self.load_level()
        pyxel.run(self.update, self.draw)

    def load_level(self):
        # ステージを最初の状態にする（やり直しにも使う）
        self.grid = [list(row) for row in MAP]
        self.h = len(self.grid)
        self.w = len(self.grid[0])
        self.ox = (128 - self.w * TILE) // 2
        self.oy = 16 + (120 - self.h * TILE) // 2
        for y in range(self.h):
            for x in range(self.w):
                if self.grid[y][x] == "S":
                    self.x = x
                    self.y = y
                    self.grid[y][x] = " "
        self.moves = 0
        self.clear = False
        self.history = []  # 1手ごとの記録（UNDO用）

    def is_wall(self, x, y):
        return self.grid[y][x] == "#"

    def count_dots(self):
        n = 0
        for row in self.grid:
            n += row.count(".")
        return n

    def move(self, dx, dy):
        if self.clear:
            return
        if self.is_wall(self.x + dx, self.y + dy):
            return  # 1マスも動けないときは手数にかぞえない
        # 動く前のようすを記録しておく（迷路はコピーしてから）
        grid_copy = [row[:] for row in self.grid]
        self.history.append((grid_copy, self.x, self.y, self.moves))
        self.moves += 1
        while not self.is_wall(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy
            tile = self.grid[self.y][self.x]
            if tile == ".":
                self.grid[self.y][self.x] = " "
            if tile == "E" and self.count_dots() == 0:
                self.clear = True
                break

    def undo(self):
        if len(self.history) == 0:
            return
        grid, x, y, moves = self.history.pop()  # 最後の記録を取り出す
        self.grid = grid
        self.x = x
        self.y = y
        self.moves = moves
        self.clear = False

    def update(self):
        if pyxel.btnp(pyxel.KEY_UP):
            self.move(0, -1)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.move(0, 1)
        if pyxel.btnp(pyxel.KEY_LEFT):
            self.move(-1, 0)
        if pyxel.btnp(pyxel.KEY_RIGHT):
            self.move(1, 0)
        if pyxel.btnp(pyxel.KEY_R):
            self.load_level()
        if pyxel.btnp(pyxel.KEY_Z):
            self.undo()

    def draw(self):
        pyxel.cls(0)
        for y in range(self.h):
            for x in range(self.w):
                tile = self.grid[y][x]
                px = self.ox + x * TILE
                py = self.oy + y * TILE
                if tile == "#":
                    pyxel.rect(px, py, TILE, TILE, 1)
                elif tile == ".":
                    pyxel.rect(px + 3, py + 3, 2, 2, 10)
                elif tile == "E":
                    if self.count_dots() == 0:
                        pyxel.rect(px + 1, py + 1, 6, 6, 11)
                    else:
                        pyxel.rectb(px + 1, py + 1, 6, 6, 5)
        px = self.ox + self.x * TILE
        py = self.oy + self.y * TILE
        pyxel.rect(px + 1, py + 1, 6, 6, 9)

        pyxel.text(4, 4, f"MOVES {self.moves}", 7)
        pyxel.text(80, 4, f"DOTS {self.count_dots()}", 7)
        pyxel.text(4, 148, "ARROWS:MOVE Z:UNDO R:RESET", 13)
        if self.clear:
            pyxel.rect(24, 64, 80, 24, 1)
            pyxel.text(52, 70, "CLEAR!", 10)
            pyxel.text(42, 78, f"{self.moves} MOVES", 7)


App()
