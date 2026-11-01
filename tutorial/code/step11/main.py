import pyxel

from levels import LEVELS

TILE = 8
SPEED = 2  # 1フレームに進むドット数（8 を割り切れる数にする）


class App:
    def __init__(self):
        pyxel.init(128, 160, title="SLIDE MAZE", fps=60)
        # 音を作る: 音の高さ, 音色, 音量, エフェクト, 速さ
        pyxel.sounds[0].set("c2", "t", "4", "f", 10)  # 止まった音
        pyxel.sounds[1].set("a3", "s", "3", "f", 6)  # ドットを拾った音
        pyxel.sounds[2].set("c3e3g3c4", "t", "4", "n", 12)  # クリアの音
        pyxel.sounds[3].set("c3", "n", "3", "f", 8)  # 床が崩れる音
        self.stage = 0
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
                    self.grid[y][x] = " "  # 立っているマスは拾ったことにする
                elif self.grid[y][x] == " ":
                    self.grid[y][x] = "."  # 空白のマスには全部ドットを置く
        self.moves = 0
        self.clear = False
        self.history = []
        self.moving = False  # 滑っている最中なら True
        self.dx = 0
        self.dy = 1  # 最初は下向き（目の向きにも使う）
        self.offset = 0  # 今のマスから何ドット進んだか

    def is_wall(self, x, y):
        return self.grid[y][x] == "#"

    def tile_at(self, x, y):
        # 迷路の外は壁ということにする
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.grid[y][x]
        return "#"

    def count_dots(self):
        n = 0
        for row in self.grid:
            n += row.count(".")
        return n

    def start_move(self, dx, dy):
        # 滑り始めるだけ。実際に進むのは update_move
        if self.clear or self.moving:
            return
        if self.is_wall(self.x + dx, self.y + dy):
            return
        grid_copy = [row[:] for row in self.grid]
        self.history.append((grid_copy, self.x, self.y, self.moves))
        self.moves += 1
        self.dx = dx
        self.dy = dy
        self.offset = 0
        self.moving = True

    def update_move(self):
        # 1フレーム分だけ進む
        self.offset += SPEED
        if self.offset < TILE:
            return
        # となりのマスに着いた
        self.offset = 0
        if self.grid[self.y][self.x] == "x":
            self.grid[self.y][self.x] = "#"  # 離れた崩れる床は壁になる
            pyxel.play(2, 3)
        self.x += self.dx
        self.y += self.dy
        tile = self.grid[self.y][self.x]
        if tile == ".":
            self.grid[self.y][self.x] = " "
            pyxel.play(1, 1)
        if tile == "E" and self.count_dots() == 0:
            self.clear = True
            self.moving = False
            pyxel.play(0, 2)
            return
        if tile == "o":
            self.moving = False  # ぬかるみでは止まる
        elif self.is_wall(self.x + self.dx, self.y + self.dy):
            self.moving = False  # 次が壁なら止まる
        if not self.moving:
            pyxel.play(0, 0)

    def undo(self):
        if self.moving or len(self.history) == 0:
            return
        grid, x, y, moves = self.history.pop()
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
        if self.moving:
            self.update_move()
            return  # 滑っているあいだはキーを受けつけない
        if self.clear and pyxel.btnp(pyxel.KEY_RETURN):
            self.next_stage()
        if pyxel.btnp(pyxel.KEY_UP):
            self.start_move(0, -1)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.start_move(0, 1)
        if pyxel.btnp(pyxel.KEY_LEFT):
            self.start_move(-1, 0)
        if pyxel.btnp(pyxel.KEY_RIGHT):
            self.start_move(1, 0)
        if pyxel.btnp(pyxel.KEY_R):
            self.load_level()
        if pyxel.btnp(pyxel.KEY_Z):
            self.undo()

    def draw_wall(self, x, y, px, py):
        # まわりが全部壁なら何も描かない（迷路の外側を暗くする）
        is_open = False
        for ny in range(y - 1, y + 2):
            for nx in range(x - 1, x + 2):
                if self.tile_at(nx, ny) != "#":
                    is_open = True
        if not is_open:
            return
        pyxel.rect(px, py, TILE, TILE, 1)
        # 通路に面した辺にふちをつける
        if self.tile_at(x, y - 1) != "#":
            pyxel.line(px, py, px + 7, py, 12)
        if self.tile_at(x, y + 1) != "#":
            pyxel.line(px, py + 7, px + 7, py + 7, 5)
        if self.tile_at(x - 1, y) != "#":
            pyxel.line(px, py, px, py + 7, 5)
        if self.tile_at(x + 1, y) != "#":
            pyxel.line(px + 7, py, px + 7, py + 7, 5)

    def draw(self):
        pyxel.cls(0)
        for y in range(self.h):
            for x in range(self.w):
                tile = self.grid[y][x]
                px = self.ox + x * TILE
                py = self.oy + y * TILE
                if tile == "#":
                    self.draw_wall(x, y, px, py)
                elif tile == ".":
                    pyxel.rect(px + 3, py + 3, 2, 2, 10)
                elif tile == "E":
                    if self.count_dots() == 0:
                        # 開いたゴールは点滅させる（frame_count はフレームの通し番号）
                        color = 11 if pyxel.frame_count % 30 < 15 else 3
                        pyxel.rect(px + 1, py + 1, 6, 6, color)
                    else:
                        pyxel.rectb(px + 1, py + 1, 6, 6, 5)
                elif tile == "o":
                    pyxel.rect(px + 1, py + 1, 6, 6, 4)  # ぬかるみ
                elif tile == "x":
                    pyxel.rectb(px + 1, py + 1, 6, 6, 13)  # 崩れる床
                    pyxel.line(px + 2, py + 3, px + 5, py + 5, 13)
        # マスの位置 ＋ 進んだぶん だけずらして描く
        px = self.ox + self.x * TILE + self.dx * self.offset
        py = self.oy + self.y * TILE + self.dy * self.offset
        pyxel.rect(px + 1, py + 1, 6, 6, 9)
        pyxel.rectb(px + 1, py + 1, 6, 6, 10)
        # 目は進む向きを見る
        pyxel.pset(px + 3 + self.dx, py + 3 + self.dy, 0)
        pyxel.pset(px + 4 + self.dx, py + 3 + self.dy, 0)

        # 上の文字と、クリアしたときの表示
        level = LEVELS[self.stage]
        pyxel.text(4, 2, f"STAGE {self.stage + 1} {level['name']}", 7)
        pyxel.text(4, 9, f"MOVES {self.moves}", 7)
        pyxel.text(52, 9, f"PAR {level['par']}", 10)
        pyxel.text(92, 9, f"DOTS {self.count_dots()}", 7)
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
