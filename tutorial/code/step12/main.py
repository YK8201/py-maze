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
        pyxel.init(128, 160, title="ICE LAKE", fps=60)
        # 音を作る: 音の高さ, 音色, 音量, エフェクト, 速さ
        pyxel.sounds[0].set("c2", "t", "4", "f", 10)  # 止まった音
        pyxel.sounds[1].set("c4g3", "n", "3", "f", 4)  # 氷が割れる音
        pyxel.sounds[2].set("c3e3g3c4", "t", "4", "n", 12)  # クリアの音
        pyxel.sounds[3].set("a2f2c2", "n", "543", "f", 10)  # 水に落ちる音
        self.splash = 0
        self.stage = 0  # 今のステージ番号（0 から数える）
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
                    self.grid[y][x] = " "
        self.moves = 0  # 手数
        self.clear = False
        self.history = []  # 1手ごとの記録（UNDO用）
        self.moving = False  # 滑っている最中なら True
        self.dx = 0
        self.dy = -1  # 最初は上向き（目の向きにも使う）
        self.offset = 0  # 今のマスから何ドット進んだか

    def is_rock(self, x, y):
        if x < 0 or x >= self.w or y < 0 or y >= self.h:
            return True
        return self.grid[y][x] == "#"

    def start_move(self, dx, dy):
        # 滑り始めるだけ。実際に進むのは update_move
        if self.clear or self.moving:
            return
        if self.is_rock(self.x + dx, self.y + dy):
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
            self.grid[self.y][self.x] = "~"  # 離れたもろい氷は割れて水になる
            pyxel.play(1, 1)
        self.x += self.dx
        self.y += self.dy
        tile = self.grid[self.y][self.x]
        if tile == "~":
            self.splash_x = self.x  # 水しぶきを出す場所
            self.splash_y = self.y
            self.moving = False
            self.undo()  # 落ちたら、この手をなかったことにする
            self.splash = 30
            pyxel.play(0, 3)
            return
        if tile == "E":
            self.clear = True
            self.moving = False
            pyxel.play(0, 2)
            return
        if self.is_rock(self.x + self.dx, self.y + self.dy):
            self.moving = False  # 次が岩なら止まる
            pyxel.play(0, 0)

    def undo(self):
        if self.moving or len(self.history) == 0:
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
        if self.splash > 0:
            self.splash -= 1
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

    def on_shore(self, x, y):
        # 湖のいちばん外側のマスなら True
        return x == 0 or y == 0 or x == self.w - 1 or y == self.h - 1

    def draw_tile(self, x, y, px, py):
        tile = self.grid[y][x]
        if tile == "E":
            # 町: 雪の上に、赤い屋根の家
            pyxel.rect(px, py, TILE, TILE, 7)
            pyxel.tri(px, py + 4, px + 7, py + 4, px + 3, py, 8)
            pyxel.rect(px + 1, py + 4, 6, 4, 15)
            pyxel.rect(px + 3, py + 5, 2, 3, 4)
        elif self.on_shore(x, y):
            # 岸: 白い雪
            pyxel.rect(px, py, TILE, TILE, 7)
        elif tile == "#":
            # 岩: 氷の上の灰色の石。右下に影をつける
            pyxel.rect(px, py, TILE, TILE, 6)
            pyxel.rect(px + 1, py + 1, 6, 6, 13)
            pyxel.line(px + 2, py + 7, px + 6, py + 7, 5)
            pyxel.line(px + 7, py + 2, px + 7, py + 6, 5)
        elif tile == "~":
            # 水: 波の線を少しずつ動かす（frame_count はフレームの通し番号）
            pyxel.rect(px, py, TILE, TILE, 5)
            wave = (pyxel.frame_count // 12 + x + y) % 4
            pyxel.line(px + 1 + wave, py + 3, px + 3 + wave, py + 3, 12)
        elif tile == "x":
            # もろい氷: ひびを入れる
            pyxel.rect(px, py, TILE, TILE, 12)
            pyxel.line(px + 1, py + 2, px + 3, py + 4, 7)
            pyxel.line(px + 3, py + 4, px + 6, py + 3, 7)
            pyxel.line(px + 3, py + 4, px + 4, py + 6, 7)
        else:
            # 氷: マスごとに位置を変えて、白いきらめきを1つ
            pyxel.rect(px, py, TILE, TILE, 6)
            k = (x * 7 + y * 11) % 5
            pyxel.pset(px + 1 + k, py + 1 + (k * 3) % 6, 7)

    def draw_player(self, px, py):
        # オレンジの体と、黒いシルクハット
        pyxel.rect(px + 1, py + 3, 6, 5, 9)
        pyxel.rect(px + 2, py, 4, 2, 0)
        pyxel.line(px + 1, py + 2, px + 6, py + 2, 0)
        # 目は進む向きを見る
        pyxel.pset(px + 3 + self.dx, py + 4 + self.dy, 0)
        pyxel.pset(px + 4 + self.dx, py + 4 + self.dy, 0)

    def draw_button(self, button):
        name, x, y, w, h = button
        pyxel.rect(x, y, w, h, 1)
        pyxel.rectb(x, y, w, h, 12)
        # 文字は1文字が幅4ドットなので、まん中に来るように計算する
        pyxel.text(x + (w - len(name) * 4) // 2, y + 5, name, 7)

    def draw(self):
        pyxel.cls(0)
        # 湖を1マスずつ描く
        for y in range(self.h):
            for x in range(self.w):
                px = self.ox + x * TILE
                py = self.oy + y * TILE
                self.draw_tile(x, y, px, py)
        # マスの位置 ＋ 進んだぶん だけずらして描く
        px = self.ox + self.x * TILE + self.dx * self.offset
        py = self.oy + self.y * TILE + self.dy * self.offset
        self.draw_player(px, py)
        # 水しぶきの輪（時間がたつほど大きくなる）
        if self.splash > 0:
            r = 2 + (30 - self.splash) // 4
            sx = self.ox + self.splash_x * TILE + 4
            sy = self.oy + self.splash_y * TILE + 4
            pyxel.circb(sx, sy, r, 7)

        # 上の文字と、クリアしたときの表示
        level = LEVELS[self.stage]
        pyxel.text(4, 2, f"STAGE {self.stage + 1} {level['name']}", 7)
        pyxel.text(4, 9, f"MOVES {self.moves}", 7)
        pyxel.text(52, 9, f"PAR {level['par']}", 10)
        if self.splash > 0:
            pyxel.text(92, 9, "SPLASH!", 12)
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
