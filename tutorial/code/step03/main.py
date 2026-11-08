import pyxel

TILE = 8

MAP = [
    "#######",
    "# ##  #",
    "#     #",
    "#   # #",
    "#     #",
    "#     E",
    "###S###",
]


class App:
    def __init__(self):
        pyxel.init(128, 160, title="ICE LAKE")
        self.grid = [list(row) for row in MAP]
        self.h = len(self.grid)
        self.w = len(self.grid[0])
        self.ox = (128 - self.w * TILE) // 2
        self.oy = 16 + (120 - self.h * TILE) // 2
        # "S" の場所をさがして、プレイヤーをそこに置く
        for y in range(self.h):
            for x in range(self.w):
                if self.grid[y][x] == "S":
                    self.x = x
                    self.y = y
                    self.grid[y][x] = " "  # S はもう要らないので氷にする
        pyxel.run(self.update, self.draw)

    def is_rock(self, x, y):
        # 湖の外は岩ということにする
        if x < 0 or x >= self.w or y < 0 or y >= self.h:
            return True
        return self.grid[y][x] == "#"

    def move(self, dx, dy):
        # となりが岩でなければ1マス進む
        if not self.is_rock(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy

    def update(self):
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
                else:
                    pyxel.rect(px, py, TILE, TILE, 6)
        # プレイヤー（オレンジの四角）
        px = self.ox + self.x * TILE
        py = self.oy + self.y * TILE
        pyxel.rect(px + 1, py + 1, 6, 6, 9)


App()
