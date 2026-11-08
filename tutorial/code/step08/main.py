import pyxel

from levels import LEVELS

TILE = 8


class App:
    def __init__(self):
        pyxel.init(128, 160, title="ICE LAKE")
        self.splash = 0
        self.stage = 0  # 今のステージ番号（0 から数える）
        self.load_level()
        pyxel.run(self.update, self.draw)

    def load_level(self):
        level = LEVELS[self.stage]
        self.grid = [list(row) for row in level["map"]]
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
        self.history = []  # 1手ごとの記録（UNDO用）

    def is_rock(self, x, y):
        if x < 0 or x >= self.w or y < 0 or y >= self.h:
            return True
        return self.grid[y][x] == "#"

    def move(self, dx, dy):
        if self.clear:
            return
        if self.is_rock(self.x + dx, self.y + dy):
            return  # 1マスも動けないときは手数にかぞえない
        # 動く前のようすを記録しておく（湖はコピーしてから）
        grid_copy = [row[:] for row in self.grid]
        self.history.append((grid_copy, self.x, self.y, self.moves))
        self.moves += 1
        while not self.is_rock(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy
            tile = self.grid[self.y][self.x]
            if tile == "~":
                self.undo()  # 落ちたら、この手をなかったことにする
                self.splash = 30
                return
            if tile == "E":
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

    def next_stage(self):
        if self.stage + 1 < len(LEVELS):
            self.stage += 1
            self.load_level()

    def update(self):
        if self.splash > 0:
            self.splash -= 1
        if self.clear and pyxel.btnp(pyxel.KEY_RETURN):
            self.next_stage()
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

        # 上の文字と、クリアしたときの表示
        level = LEVELS[self.stage]
        pyxel.text(4, 2, f"STAGE {self.stage + 1} {level['name']}", 7)
        pyxel.text(4, 9, f"MOVES {self.moves}", 7)
        pyxel.text(52, 9, f"PAR {level['par']}", 10)
        if self.splash > 0:
            pyxel.text(92, 9, "SPLASH!", 12)
        pyxel.text(4, 148, "ARROWS:MOVE Z:UNDO R:RESET", 13)
        if self.clear:
            pyxel.rect(16, 60, 96, 36, 1)
            pyxel.text(52, 66, "CLEAR!", 10)
            pyxel.text(36, 75, f"MOVES {self.moves}  PAR {level['par']}", 7)
            if self.stage + 1 < len(LEVELS):
                pyxel.text(30, 86, "ENTER: NEXT STAGE", 6)
            else:
                pyxel.text(44, 86, "ALL CLEAR!", 6)


App()
