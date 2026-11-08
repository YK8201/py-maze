import pyxel

TILE = 8

MAP = [
    "#######",
    "#     #",
    "##~ # #",
    "#    ~#",
    "#     #",
    "#     E",
    "####S##",
]


class App:
    def __init__(self):
        pyxel.init(128, 160, title="ICE LAKE")
        self.splash = 0
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
        self.moves = 0  # 手数
        self.clear = False

    def is_rock(self, x, y):
        if x < 0 or x >= self.w or y < 0 or y >= self.h:
            return True
        return self.grid[y][x] == "#"

    def move(self, dx, dy):
        if self.clear:
            return
        if self.is_rock(self.x + dx, self.y + dy):
            return  # 1マスも動けないときは手数にかぞえない
        start_x = self.x
        start_y = self.y
        while not self.is_rock(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy
            tile = self.grid[self.y][self.x]
            if tile == "~":
                self.x = start_x
                self.y = start_y
                self.splash = 30
                return  # 落ちた手も手数にかぞえない
            if tile == "E":
                self.clear = True
                break
        self.moves += 1

    def update(self):
        if self.splash > 0:
            self.splash -= 1
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

    def draw(self):
        pyxel.cls(0)
        for y in range(self.h):
            for x in range(self.w):
                tile = self.grid[y][x]
                px = self.ox + x * TILE
                py = self.oy + y * TILE
                if tile == "#":
                    pyxel.rect(px, py, TILE, TILE, 13)
                elif tile == "E":
                    pyxel.rect(px, py, TILE, TILE, 8)
                elif tile == "~":
                    pyxel.rect(px, py, TILE, TILE, 5)
                else:
                    pyxel.rect(px, py, TILE, TILE, 6)
        px = self.ox + self.x * TILE
        py = self.oy + self.y * TILE
        pyxel.rect(px + 1, py + 1, 6, 6, 9)

        pyxel.text(4, 4, f"MOVES {self.moves}", 7)
        if self.splash > 0:
            pyxel.text(50, 4, "SPLASH!", 12)
        pyxel.text(4, 148, "ARROWS:MOVE  R:RESET", 13)
        if self.clear:
            pyxel.rect(24, 64, 80, 24, 1)
            pyxel.text(52, 70, "CLEAR!", 10)
            pyxel.text(42, 78, f"{self.moves} MOVES", 7)


App()
