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
        self.clear = False
        self.splash = 0  # 水に落ちたあと、文字を出しておく残りフレーム数
        pyxel.run(self.update, self.draw)

    def is_rock(self, x, y):
        if x < 0 or x >= self.w or y < 0 or y >= self.h:
            return True
        return self.grid[y][x] == "#"

    def move(self, dx, dy):
        if self.clear:
            return
        start_x = self.x  # 落ちたときに戻る場所を覚えておく
        start_y = self.y
        while not self.is_rock(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy
            tile = self.grid[self.y][self.x]
            if tile == "~":
                # 水に落ちた！ 元の場所に戻す
                self.x = start_x
                self.y = start_y
                self.splash = 30
                return
            if tile == "E":
                self.clear = True
                break

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
                    pyxel.rect(px, py, TILE, TILE, 5)  # 水（暗い青）
                else:
                    pyxel.rect(px, py, TILE, TILE, 6)
        px = self.ox + self.x * TILE
        py = self.oy + self.y * TILE
        pyxel.rect(px + 1, py + 1, 6, 6, 9)

        if self.splash > 0:
            pyxel.text(50, 4, "SPLASH!", 12)
        if self.clear:
            pyxel.rect(24, 64, 80, 24, 1)
            pyxel.text(52, 73, "CLEAR!", 10)


App()
