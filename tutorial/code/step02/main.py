import pyxel

TILE = 8  # 1マスの大きさ（ドット）

MAP = [
    "#######",
    "#S    #",
    "##### #",
    "#E    #",
    "#######",
]


class App:
    def __init__(self):
        pyxel.init(128, 160, title="SLIDE MAZE")
        # 文字列のままだと書きかえられないので、1文字ずつのリストにする
        self.grid = [list(row) for row in MAP]
        self.h = len(self.grid)
        self.w = len(self.grid[0])
        # 迷路を画面のまん中に置くための、左上の位置
        self.ox = (128 - self.w * TILE) // 2
        self.oy = 16 + (120 - self.h * TILE) // 2
        pyxel.run(self.update, self.draw)

    def update(self):
        pass

    def draw(self):
        pyxel.cls(0)
        for y in range(self.h):
            for x in range(self.w):
                tile = self.grid[y][x]
                px = self.ox + x * TILE
                py = self.oy + y * TILE
                if tile == "#":
                    pyxel.rect(px, py, TILE, TILE, 1)
                elif tile == "E":
                    pyxel.rectb(px + 1, py + 1, 6, 6, 11)


App()
