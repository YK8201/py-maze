import pyxel

from levels import LEVELS

TILE = 8
SPEED = 2  # 1フレームに進むドット数（8 を割り切れる数にする）
SWIPE = 5  # これだけ指を動かしたらスワイプとみなす

# 画面のボタン: (名前, x, y, 幅, 高さ)
UNDO_BUTTON = ("UNDO", 8, 138, 52, 16)
RESET_BUTTON = ("RESET", 68, 138, 52, 16)
NEXT_BUTTON = ("NEXT", 40, 82, 48, 16)


class App:
    def __init__(self):
        pyxel.init(128, 160, title="SLIDE MAZE", fps=60)
        # 音を作る: 音の高さ, 音色, 音量, エフェクト, 速さ
        pyxel.sounds[0].set("c2", "t", "4", "f", 10)  # 止まった音
        pyxel.sounds[1].set("a3", "s", "3", "f", 6)  # ドットを拾った音
        pyxel.sounds[2].set("c3e3g3c4", "t", "4", "n", 12)  # クリアの音
        pyxel.sounds[3].set("c3", "n", "3", "f", 8)  # 床が崩れる音
        self.stage = 0
        self.touch_start = None  # 指を置いた場所
        self.swiped = False
        self.swipe = None  # このフレームのスワイプの向き (dx, dy)
        self.tap = None  # このフレームでタップされた場所 (x, y)
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

    def update_touch(self):
        # スマホのタッチは、Pyxel ではマウスの左ボタンとして届く
        self.swipe = None
        self.tap = None
        mx = pyxel.mouse_x
        my = pyxel.mouse_y
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            self.touch_start = (mx, my)
            self.swiped = False
        if self.touch_start and pyxel.btn(pyxel.MOUSE_BUTTON_LEFT) and not self.swiped:
            dx = mx - self.touch_start[0]
            dy = my - self.touch_start[1]
            if abs(dx) >= SWIPE or abs(dy) >= SWIPE:
                # 横と縦、大きく動いたほうの向きにする
                if abs(dx) > abs(dy):
                    self.swipe = (1 if dx > 0 else -1, 0)
                else:
                    self.swipe = (0, 1 if dy > 0 else -1)
                self.swiped = True  # 1回のタッチで1手だけ
        if pyxel.btnr(pyxel.MOUSE_BUTTON_LEFT):
            if self.touch_start and not self.swiped:
                self.tap = self.touch_start  # 動かさずに離したらタップ
            self.touch_start = None

    def tapped(self, button):
        # ボタンの四角の中がタップされたか
        if self.tap is None:
            return False
        name, x, y, w, h = button
        tx, ty = self.tap
        return x <= tx < x + w and y <= ty < y + h

    def update(self):
        self.update_touch()
        if self.moving:
            self.update_move()
            return  # 滑っているあいだはキーを受けつけない
        if self.clear and (pyxel.btnp(pyxel.KEY_RETURN) or self.tapped(NEXT_BUTTON)):
            self.next_stage()
            return
        if pyxel.btnp(pyxel.KEY_UP):
            self.start_move(0, -1)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.start_move(0, 1)
        if pyxel.btnp(pyxel.KEY_LEFT):
            self.start_move(-1, 0)
        if pyxel.btnp(pyxel.KEY_RIGHT):
            self.start_move(1, 0)
        if self.swipe:
            self.start_move(self.swipe[0], self.swipe[1])
        if pyxel.btnp(pyxel.KEY_R) or self.tapped(RESET_BUTTON):
            self.load_level()
        if pyxel.btnp(pyxel.KEY_Z) or self.tapped(UNDO_BUTTON):
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

    def draw_button(self, button):
        name, x, y, w, h = button
        pyxel.rect(x, y, w, h, 1)
        pyxel.rectb(x, y, w, h, 12)
        # 文字は1文字が幅4ドットなので、まん中に来るように計算する
        pyxel.text(x + (w - len(name) * 4) // 2, y + 5, name, 7)

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
        self.draw_button(UNDO_BUTTON)
        self.draw_button(RESET_BUTTON)
        if self.clear:
            pyxel.rect(16, 56, 96, 48, 1)
            pyxel.rectb(16, 56, 96, 48, 12)
            pyxel.text(52, 62, "CLEAR!", 10)
            pyxel.text(36, 71, f"MOVES {self.moves}  PAR {level['par']}", 7)
            if self.stage + 1 < len(LEVELS):
                self.draw_button(NEXT_BUTTON)
            else:
                pyxel.text(44, 88, "ALL CLEAR!", 6)


App()
