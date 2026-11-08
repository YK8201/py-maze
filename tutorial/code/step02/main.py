import pyxel

TILE = 8  # 1マスの大きさ（ドット）

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
        # 文字列のままだと書きかえられないので、1文字ずつのリストにする
        self.grid = [list(row) for row in MAP]
        self.h = len(self.grid)
        self.w = len(self.grid[0])
        # 湖を画面のまん中に置くための、左上の位置
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
                    pyxel.rect(px, py, TILE, TILE, 13)  # 岩（灰色）
                elif tile == "E":
                    pyxel.rect(px, py, TILE, TILE, 8)  # 町（赤）
                else:
                    pyxel.rect(px, py, TILE, TILE, 6)  # 氷（水色）


App()
