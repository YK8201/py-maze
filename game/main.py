"""PY-MAZE : 氷の湖を渡るスライドパズル（レイトン教授「氷の湖」風）

操作
    移動    : 矢印キー / WASD / スワイプ / ゲームパッド十字
    戻す    : Z / U / BackSpace / ゲームパッドA / [UNDO]
    やり直し: R / ゲームパッドB / [RESET]（やり直しも UNDO で戻せる）
    メニュー: Esc / M / ゲームパッドSTART / [MENU]
"""

import json
import os

import pyxel

from core import DIRS, DOWN, EXIT, ICE, LEFT, RIGHT, ROCK, THIN, UP, WATER, Level, step
from levels import LEVELS

W, H = 128, 184
TILE = 8
MAZE_Y, MAZE_H = 16, 128
SLIDE_SPEED = 0.4  # マス/フレーム
SWIPE_DIST = 5

BUTTONS_PLAY = [("UNDO", 4, 150, 38, 16), ("RESET", 45, 150, 38, 16), ("MENU", 86, 150, 38, 16)]
BUTTONS_CLEAR = [("RETRY", 20, 118, 40, 16), ("NEXT", 68, 118, 40, 16)]

HINTS = {
    0: "SWIPE: SLIDE UNTIL A ROCK",
    1: "REACH THE TOWN ACROSS THE LAKE",
    3: "WATER: DON'T FALL IN!",
    8: "THIN ICE BREAKS AFTER YOU PASS",
}

SAVE_KEY = "py-maze-save-v3"  # 氷の湖版。旧ステージの記録とは分ける
SAVE_FILE = "save-v3.json"


# ---------------------------------------------------------------- 保存
def load_save():
    try:
        import js  # Web版(Pyodide)では localStorage を使う

        s = js.localStorage.getItem(SAVE_KEY)
        return json.loads(s) if s else {}
    except Exception:
        pass
    try:
        with open(os.path.join(pyxel.user_data_dir("yk8201", "py-maze"), SAVE_FILE)) as f:
            return json.load(f)
    except Exception:
        return {}


def write_save(data):
    s = json.dumps(data)
    try:
        import js

        js.localStorage.setItem(SAVE_KEY, s)
        return
    except Exception:
        pass
    try:
        with open(os.path.join(pyxel.user_data_dir("yk8201", "py-maze"), SAVE_FILE), "w") as f:
            f.write(s)
    except Exception:
        pass


# ---------------------------------------------------------------- 入力
class Input:
    """キーボード・ゲームパッド・タッチ(マウス)をまとめて扱う"""

    KEYS = {
        UP: (pyxel.KEY_UP, pyxel.KEY_W, pyxel.GAMEPAD1_BUTTON_DPAD_UP),
        DOWN: (pyxel.KEY_DOWN, pyxel.KEY_S, pyxel.GAMEPAD1_BUTTON_DPAD_DOWN),
        LEFT: (pyxel.KEY_LEFT, pyxel.KEY_A, pyxel.GAMEPAD1_BUTTON_DPAD_LEFT),
        RIGHT: (pyxel.KEY_RIGHT, pyxel.KEY_D, pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT),
    }

    def __init__(self):
        self.touch_start = None
        self.swiped = False
        self.swipe = None
        self.tap = None

    def update(self):
        self.swipe = None
        self.tap = None
        mx, my = pyxel.mouse_x, pyxel.mouse_y
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            self.touch_start = (mx, my)
            self.swiped = False
        if self.touch_start and pyxel.btn(pyxel.MOUSE_BUTTON_LEFT) and not self.swiped:
            dx, dy = mx - self.touch_start[0], my - self.touch_start[1]
            if max(abs(dx), abs(dy)) >= SWIPE_DIST:
                if abs(dx) > abs(dy):
                    self.swipe = RIGHT if dx > 0 else LEFT
                else:
                    self.swipe = DOWN if dy > 0 else UP
                self.swiped = True  # 1回のタッチで1手だけ
        if pyxel.btnr(pyxel.MOUSE_BUTTON_LEFT):
            if self.touch_start and not self.swiped:
                self.tap = self.touch_start
            self.touch_start = None

    def direction(self):
        for d, keys in self.KEYS.items():
            if any(pyxel.btnp(k) for k in keys):
                return d
        return self.swipe

    def tapped(self, rect):
        if self.tap is None:
            return False
        x, y, w, h = rect
        return x <= self.tap[0] < x + w and y <= self.tap[1] < y + h

    def holding(self, rect):
        if self.touch_start is None or self.swiped:
            return False
        x, y, w, h = rect
        mx, my = pyxel.mouse_x, pyxel.mouse_y
        return x <= mx < x + w and y <= my < y + h

    @staticmethod
    def any_btnp(*keys):
        return any(pyxel.btnp(k) for k in keys)


def confirm_pressed():
    return Input.any_btnp(pyxel.KEY_RETURN, pyxel.KEY_SPACE, pyxel.KEY_Z, pyxel.GAMEPAD1_BUTTON_A)


# ---------------------------------------------------------------- 描画ヘルパー
def text_c(x, y, s, col):
    pyxel.text(x - len(s) * 2, y, s, col)


def draw_button(label, x, y, w, h, pressed=False, enabled=True):
    face = 5 if pressed else 1
    pyxel.rect(x, y + 1, w, h, 0)
    pyxel.rect(x, y + (1 if pressed else 0), w, h, face)
    pyxel.rectb(x, y + (1 if pressed else 0), w, h, 12 if enabled else 5)
    text_c(x + w // 2, y + (h - 5) // 2 + (1 if pressed else 0), label, 7 if enabled else 13)


def draw_big_text(cx, cy, s, col, scale):
    """文字を画像バンクに書いて (cx, cy) を中心に拡大表示する"""
    img = pyxel.images[0]
    w = len(s) * 4
    img.rect(0, 0, w, 6, 0)
    img.text(0, 0, s, col)
    # blt の拡大は描画範囲の中心が基準
    pyxel.blt(cx - w // 2, cy - 3, 0, 0, 0, w, 6, 0, scale=scale)


def setup_sounds():
    pyxel.sounds[0].set("c2", "t", "4", "f", 10)  # 止まる
    pyxel.sounds[1].set("c4g3", "n", "3", "f", 4)  # もろい氷が割れる
    pyxel.sounds[2].set("c3e3g3c4", "t", "4", "n", 12)  # クリア
    pyxel.sounds[3].set("g2e2", "t", "3", "f", 6)  # 戻す
    pyxel.sounds[4].set("c1", "n", "2", "f", 5)  # 動けない
    pyxel.sounds[5].set("e3g3", "t", "3", "f", 6)  # 決定
    pyxel.sounds[6].set("a2f2c2", "n", "543", "f", 10)  # 水に落ちる


# ---------------------------------------------------------------- マスの絵
def draw_ice(px, py, x, y):
    pyxel.rect(px, py, TILE, TILE, 6)
    # 氷のきらめき（マスごとに位置を変える）
    k = (x * 7 + y * 11) % 5
    pyxel.pset(px + 1 + k, py + 1 + (k * 3) % 6, 7)


def draw_snow(px, py, x, y):
    pyxel.rect(px, py, TILE, TILE, 7)
    if (x + y) % 3 == 0:
        pyxel.pset(px + 2, py + 5, 6)
        pyxel.pset(px + 5, py + 2, 13)


def draw_rock(px, py):
    pyxel.rect(px, py, TILE, TILE, 6)
    pyxel.rect(px + 1, py + 1, 6, 6, 13)
    pyxel.line(px + 2, py + 7, px + 6, py + 7, 5)
    pyxel.line(px + 7, py + 2, px + 7, py + 6, 5)
    pyxel.pset(px + 2, py + 2, 7)


def draw_water(px, py, x, y):
    pyxel.rect(px, py, TILE, TILE, 5)
    s = (pyxel.frame_count // 12 + x + y) % 4
    pyxel.line(px + 1 + s, py + 3, px + 3 + s, py + 3, 12)
    pyxel.line(px + 4 - s % 2, py + 6, px + 5 - s % 2, py + 6, 12)


def draw_thin(px, py):
    pyxel.rect(px, py, TILE, TILE, 12)
    pyxel.line(px + 1, py + 2, px + 3, py + 4, 7)
    pyxel.line(px + 3, py + 4, px + 6, py + 3, 7)
    pyxel.line(px + 3, py + 4, px + 4, py + 6, 7)


def draw_broken(px, py, x, y):
    draw_water(px, py, x, y)
    # 割れた氷のかけら
    pyxel.pset(px, py, 6)
    pyxel.pset(px + 7, py + 1, 6)
    pyxel.pset(px + 1, py + 7, 6)


def draw_town(px, py):
    pyxel.rect(px, py, TILE, TILE, 7)
    pyxel.tri(px, py + 4, px + 7, py + 4, px + 3, py, 8)
    pyxel.rect(px + 1, py + 4, 6, 4, 15)
    pyxel.rect(px + 3, py + 5, 2, 3, 4)


def draw_player_at(px, py, face, sink=0):
    """プレイヤー（シルクハットの人）。sink は水に沈んだ量（0〜6）"""
    ex, ey = {UP: (0, -1), DOWN: (0, 1), LEFT: (-1, 0), RIGHT: (1, 0)}[face]
    body_h = 5 - min(sink, 5)
    if body_h > 0:
        pyxel.rect(px + 1, py + 3 + sink, 6, body_h, 9)
        if sink < 2:
            pyxel.pset(px + 3 + ex, py + 4 + ey, 0)
            pyxel.pset(px + 4 + ex, py + 4 + ey, 0)
    if sink < 7:
        hat_y = py + sink
        pyxel.rect(px + 2, hat_y, 4, 2, 0)
        pyxel.line(px + 1, hat_y + 2, px + 6, hat_y + 2, 0)


# ---------------------------------------------------------------- プレイ画面
class Play:
    SPLASH_FRAMES = 45

    def __init__(self, app, index):
        self.app = app
        self.index = index
        self.data = LEVELS[index]
        self.level = Level(self.data["map"])
        self.state = self.level.initial_state()
        self.history = []  # 戻す用の (state, moves)
        self.moves = 0
        self.falls = 0
        self.anim = None
        self.splash = None  # 水に落ちたときの演出 {"pos", "t"}
        self.buffered = None
        self.cleared = False
        self.clear_timer = 0
        self.stuck_cache = {}
        lw, lh = self.level.w * TILE, self.level.h * TILE
        self.ox = (W - lw) // 2
        self.oy = MAZE_Y + (MAZE_H - lh) // 2
        self.face = UP
        self.bump = 0

    # ---- 詰みの判定
    def stuck(self):
        """今の局面から、落ちずに町へ行く方法がもうなければ True"""
        key = self.state.key()
        if key not in self.stuck_cache:
            seen = {key}
            todo = [self.state]
            found = False
            while todo and not found:
                s = todo.pop()
                for d in DIRS:
                    r = step(self.level, s, d)
                    if r is None or r[2]:
                        continue
                    ns = r[0]
                    if ns.won:
                        found = True
                        break
                    if ns.key() not in seen:
                        seen.add(ns.key())
                        todo.append(ns)
            self.stuck_cache[key] = not found
        return self.stuck_cache[key]

    # ---- 操作
    def try_move(self, d):
        r = step(self.level, self.state, d)
        self.face = d
        if r is None:
            self.bump = 6
            pyxel.play(3, 4)
            return
        new_state, path, fell = r
        self.anim = {"path": path, "t": 0.0, "new": new_state, "old": self.state, "fell": fell}
        if not fell:
            self.history.append((self.state, self.moves))
            self.moves += 1

    def finish_anim(self):
        a = self.anim
        self.anim = None
        if a["fell"]:
            # 落ちた手はなかったことにする（演出のあと元の場所に戻る）
            self.splash = {"pos": a["path"][-1], "t": 0}
            self.falls += 1
            pyxel.play(0, 6)
            return
        self.state = a["new"]
        if self.state.won:
            self.cleared = True
            self.clear_timer = 0
            self.app.record(self.index, self.moves)
            pyxel.play(0, 2)
        else:
            pyxel.play(0, 0)

    def undo(self):
        if self.anim:
            self.finish_anim()
        self.splash = None
        if not self.history:
            return
        self.state, self.moves = self.history.pop()
        self.cleared = False
        self.buffered = None
        pyxel.play(3, 3)

    def reset(self):
        if self.anim:
            self.finish_anim()
        self.splash = None
        if self.moves == 0 and not self.history:
            return
        # やり直しも履歴に積むので UNDO で戻せる
        self.history.append((self.state, self.moves))
        self.state = self.level.initial_state()
        self.moves = 0
        self.cleared = False
        self.buffered = None
        pyxel.play(3, 3)

    def update(self):
        inp = self.app.input
        if self.bump:
            self.bump -= 1

        if self.cleared:
            self.clear_timer += 1
            if self.clear_timer < 20:
                return
            rx, nx = BUTTONS_CLEAR
            if inp.tapped(nx[1:]) or confirm_pressed():
                self.app.start_level(self.index + 1)
            elif inp.tapped(rx[1:]) or Input.any_btnp(pyxel.KEY_R, pyxel.GAMEPAD1_BUTTON_B):
                self.history.append((self.state, self.moves))
                self.state = self.level.initial_state()
                self.moves = 0
                self.cleared = False
            elif Input.any_btnp(pyxel.KEY_U, pyxel.KEY_BACKSPACE):
                self.undo()
            elif Input.any_btnp(pyxel.KEY_ESCAPE, pyxel.KEY_M, pyxel.GAMEPAD1_BUTTON_START):
                self.app.open_select(self.index)
            return

        d = inp.direction()
        if self.splash:
            self.splash["t"] += 1
            if self.splash["t"] >= self.SPLASH_FRAMES or (d is not None and self.splash["t"] > 15):
                self.splash = None
            return

        if self.anim:
            if d is not None:
                self.buffered = d
            a = self.anim
            prev_i = int(a["t"])
            a["t"] += SLIDE_SPEED
            last = len(a["path"]) - 1
            cur_i = min(int(a["t"]), last)
            for i in range(prev_i + 1, cur_i + 1):
                if a["path"][i - 1] in self.level.thin_index:
                    pyxel.play(2, 1)  # もろい氷が割れる
            if a["t"] >= last:
                self.finish_anim()
                if self.buffered is not None and not self.cleared and not self.splash:
                    d, self.buffered = self.buffered, None
                    self.try_move(d)
                self.buffered = None
            return

        if d is not None:
            self.try_move(d)
            return

        undo_b, reset_b, menu_b = BUTTONS_PLAY
        if inp.tapped(undo_b[1:]) or Input.any_btnp(
            pyxel.KEY_Z, pyxel.KEY_U, pyxel.KEY_BACKSPACE, pyxel.GAMEPAD1_BUTTON_A
        ):
            self.undo()
        elif inp.tapped(reset_b[1:]) or Input.any_btnp(pyxel.KEY_R, pyxel.GAMEPAD1_BUTTON_B):
            self.reset()
        elif inp.tapped(menu_b[1:]) or Input.any_btnp(
            pyxel.KEY_ESCAPE, pyxel.KEY_M, pyxel.GAMEPAD1_BUTTON_START
        ):
            self.app.open_select(self.index)

    # ---- 描画
    def view_thins(self):
        """アニメ中は、通り過ぎたもろい氷だけ割れて見えるようにする"""
        if not self.anim:
            return self.state.thins
        a = self.anim
        thins = a["old"].thins
        i = min(int(a["t"]), len(a["path"]) - 1)
        for p in a["path"][:i]:
            k = self.level.thin_index.get(p)
            if k is not None:
                thins &= ~(1 << k)
        return thins

    def player_pixel(self):
        if not self.anim:
            x, y = self.splash["pos"] if self.splash else self.state.pos
            return self.ox + x * TILE, self.oy + y * TILE
        a = self.anim
        path = a["path"]
        t = min(a["t"], len(path) - 1)
        i = int(t)
        f = t - i
        x0, y0 = path[i]
        x1, y1 = path[min(i + 1, len(path) - 1)]
        return (
            self.ox + (x0 + (x1 - x0) * f) * TILE,
            self.oy + (y0 + (y1 - y0) * f) * TILE,
        )

    def draw_lake(self, thins):
        lv = self.level
        for y in range(lv.h):
            for x in range(lv.w):
                px, py = self.ox + x * TILE, self.oy + y * TILE
                t = lv.tile(x, y)
                shore = x in (0, lv.w - 1) or y in (0, lv.h - 1)
                if (x, y) == lv.start:
                    draw_snow(px, py, x, y)
                    pyxel.pset(px + 2, py + 3, 13)  # 足あと
                    pyxel.pset(px + 5, py + 5, 13)
                elif t == ROCK:
                    if shore:
                        draw_snow(px, py, x, y)
                    else:
                        draw_rock(px, py)
                elif t == ICE:
                    draw_ice(px, py, x, y)
                elif t == WATER:
                    draw_water(px, py, x, y)
                elif t == THIN:
                    if (thins >> lv.thin_index[(x, y)]) & 1:
                        draw_thin(px, py)
                    else:
                        draw_broken(px, py, x, y)
                elif t == EXIT:
                    draw_town(px, py)

    def draw_player(self):
        px, py = self.player_pixel()
        px, py = round(px), round(py)
        if self.anim:
            # 氷に残る滑った跡
            a = self.anim
            sx, sy = a["path"][0]
            sx, sy = self.ox + sx * TILE, self.oy + sy * TILE
            if sx == px:
                y0, y1 = sorted((sy, py))
                pyxel.rect(px + 3, y0 + 4, 2, y1 - y0 + 1, 7)
            else:
                x0, x1 = sorted((sx, px))
                pyxel.rect(x0 + 3, py + 6, x1 - x0 + 2, 1, 7)
        if self.splash:
            t = self.splash["t"]
            # 水しぶきの輪
            r = 2 + t // 4
            if r < 10:
                pyxel.circb(px + 4, py + 4, r, 7 if t % 8 < 4 else 12)
            draw_player_at(px, py, self.face, sink=min(7, t // 3))
            return
        if self.bump:
            dx, dy = {UP: (0, -1), DOWN: (0, 1), LEFT: (-1, 0), RIGHT: (1, 0)}[self.face]
            px += dx * (self.bump % 2)
            py += dy * (self.bump % 2)
        draw_player_at(px, py, self.face)

    def draw(self):
        pyxel.cls(0)
        self.draw_lake(self.view_thins())
        self.draw_player()

        # ヘッダー
        pyxel.rect(0, 0, W, 14, 1)
        pyxel.text(3, 2, f"{self.index + 1:02d} {self.data['name']}", 7)
        best = self.app.best(self.index)
        if best is not None:
            mark = "*" if best <= self.data["par"] else ""
            s = f"BEST {best}{mark}"
            pyxel.text(W - 3 - len(s) * 4, 2, s, 10 if mark else 13)
        pyxel.text(3, 8, f"MOVES {self.moves}", 7)
        pyxel.text(46, 8, f"PAR {self.data['par']}", 10)
        s = f"FALLS {self.falls}"
        pyxel.text(W - 3 - len(s) * 4, 8, s, 12)

        # ボタン
        inp = self.app.input
        for label, x, y, w, h in BUTTONS_PLAY:
            enabled = label == "MENU" or bool(self.history)
            draw_button(label, x, y, w, h, inp.holding((x, y, w, h)), enabled)

        # 下の一行: 落ちた・詰んだ・ヒント
        if self.splash:
            text_c(W // 2, 172, "SPLASH! BACK TO THE LAST SPOT", 12)
        elif not self.anim and not self.cleared and self.stuck():
            col = 8 if (pyxel.frame_count // 20) % 2 else 14
            text_c(W // 2, 172, "STUCK: NO WAY TO TOWN. UNDO!", col)
        elif HINTS.get(self.index):
            text_c(W // 2, 172, HINTS[self.index], 13)
        else:
            text_c(W // 2, 172, "SWIPE OR ARROW KEYS", 5)

        if self.cleared:
            self.draw_clear()

    def draw_clear(self):
        t = min(self.clear_timer, 20)
        pyxel.dither(t / 20 * 0.85)
        pyxel.rect(0, 0, W, H, 0)
        pyxel.dither(1.0)
        if self.clear_timer < 10:
            return
        pyxel.rect(12, 54, W - 24, 86, 1)
        pyxel.rectb(12, 54, W - 24, 86, 12)
        draw_big_text(W // 2, 68, "CLEAR", 10, 2)
        par = self.data["par"]
        text_c(W // 2, 80, f"MOVES {self.moves}  PAR {par}", 7)
        if self.moves <= par:
            text_c(W // 2, 92, "* PERFECT *", 10 if (pyxel.frame_count // 10) % 2 else 9)
        else:
            text_c(W // 2, 92, "TRY FEWER MOVES?", 6)
        text_c(W // 2, 102, "(UNDO: U KEY)", 5)
        if self.clear_timer >= 20:
            inp = self.app.input
            for label, x, y, w, h in BUTTONS_CLEAR:
                if label == "NEXT" and self.index + 1 >= len(LEVELS):
                    label = "END"
                draw_button(label, x, y, w, h, inp.holding((x, y, w, h)))


# ---------------------------------------------------------------- ステージ選択
class Select:
    COLS, CELL, GAP, X0, Y0 = 5, 22, 2, 5, 20

    def __init__(self, app, cursor=0):
        self.app = app
        self.cursor = cursor

    def cell_rect(self, i):
        c, r = i % self.COLS, i // self.COLS
        return (
            self.X0 + c * (self.CELL + self.GAP),
            self.Y0 + r * (self.CELL + self.GAP),
            self.CELL,
            self.CELL,
        )

    def update(self):
        inp = self.app.input
        d = inp.direction()
        n = len(LEVELS)
        if d == LEFT:
            self.cursor = (self.cursor - 1) % n
        elif d == RIGHT:
            self.cursor = (self.cursor + 1) % n
        elif d == UP:
            self.cursor = (self.cursor - self.COLS) % n
        elif d == DOWN:
            self.cursor = (self.cursor + self.COLS) % n
        for i in range(n):
            if inp.tapped(self.cell_rect(i)):
                self.cursor = i
                self.open(i)
                return
        if confirm_pressed():
            self.open(self.cursor)
        elif Input.any_btnp(pyxel.KEY_ESCAPE, pyxel.GAMEPAD1_BUTTON_B):
            self.app.scene = Title(self.app)

    def open(self, i):
        if self.app.unlocked(i):
            pyxel.play(3, 5)
            self.app.start_level(i)
        else:
            pyxel.play(3, 4)

    def draw(self):
        pyxel.cls(0)
        pyxel.rect(0, 0, W, 14, 1)
        text_c(W // 2, 4, "SELECT STAGE", 7)
        for i, lv in enumerate(LEVELS):
            x, y, w, h = self.cell_rect(i)
            best = self.app.best(i)
            unlocked = self.app.unlocked(i)
            face = 1 if unlocked else 0
            pyxel.rect(x, y, w, h, face)
            border = 12 if best is not None else (5 if unlocked else 1)
            pyxel.rectb(x, y, w, h, border)
            if unlocked:
                text_c(x + w // 2, y + 5, f"{i + 1}", 7)
                if best is not None:
                    col = 10 if best <= lv["par"] else 13
                    text_c(x + w // 2, y + 13, "*" if best <= lv["par"] else "-", col)
            else:
                text_c(x + w // 2, y + 8, "..", 5)
            if i == self.cursor:
                pyxel.rectb(x - 1, y - 1, w + 2, h + 2, 10 if (pyxel.frame_count // 15) % 2 else 9)

        lv = LEVELS[self.cursor]
        y = 120
        text_c(W // 2, y, f"{self.cursor + 1:02d} {lv['name']}", 7)
        best = self.app.best(self.cursor)
        info = f"PAR {lv['par']}" + (f"  BEST {best}" if best is not None else "")
        if not self.app.unlocked(self.cursor):
            info = "LOCKED"
        text_c(W // 2, y + 8, info, 10 if best is not None and best <= lv["par"] else 13)

        # 凡例
        y = 142
        pyxel.rect(0, y - 4, W, 1, 1)
        self.legend(6, y, "rock", "STOPS YOU")
        self.legend(6, y + 9, "town", "GOAL (TOWN)")
        self.legend(6, y + 18, "water", "SPLASH!")
        self.legend(6, y + 27, "thin", "BREAKS AFTER")
        pyxel.text(70, y + 1, "* = PAR CLEAR", 10)
        pyxel.text(70, y + 10, "UNDO ANYTIME", 13)
        pyxel.text(70, y + 19, "NO TIME LIMIT", 13)

    @staticmethod
    def legend(x, y, kind, label):
        if kind == "rock":
            draw_rock(x, y)
        elif kind == "town":
            draw_town(x, y)
        elif kind == "water":
            draw_water(x, y, 0, 0)
        elif kind == "thin":
            draw_thin(x, y)
        pyxel.text(x + 11, y + 2, label, 6)


# ---------------------------------------------------------------- タイトル
class Title:
    def __init__(self, app):
        self.app = app

    def update(self):
        inp = self.app.input
        if inp.tap or confirm_pressed() or inp.swipe is not None:
            pyxel.play(3, 5)
            self.app.open_select(self.app.next_stage())

    def draw(self):
        pyxel.cls(0)
        # 背景の飾り迷路
        for y in range(0, H, TILE):
            for x in range(0, W, TILE):
                if (x * 7 + y * 13) // 8 % 5 == 0:
                    pyxel.rect(x, y, TILE, TILE, 1)
        pyxel.rect(8, 44, W - 16, 66, 0)
        pyxel.rectb(8, 44, W - 16, 66, 5)
        draw_big_text(W // 2, 60, "PY-MAZE", 10, 3)
        text_c(W // 2, 74, "A QUIET ICE LAKE PUZZLE", 6)
        # 滑るプレイヤーのデモ
        t = (pyxel.frame_count % 120) / 120
        px = 20 + int(abs(t * 2 - 1) * 80)
        pyxel.rect(18, 83, 92, 8, 6)
        draw_player_at(px, 83, RIGHT if t < 0.5 else LEFT)
        if (pyxel.frame_count // 20) % 2:
            text_c(W // 2, 130, "TAP OR PRESS ENTER", 7)
        cleared = sum(1 for i in range(len(LEVELS)) if self.app.best(i) is not None)
        text_c(W // 2, 150, f"CLEARED {cleared}/{len(LEVELS)}", 13)


# ---------------------------------------------------------------- アプリ
class App:
    def __init__(self):
        pyxel.init(W, H, title="PY-MAZE", fps=60, quit_key=pyxel.KEY_NONE)
        setup_sounds()
        self.input = Input()
        self.save = load_save()
        self.scene = Title(self)
        pyxel.run(self.update, self.draw)

    def best(self, i):
        return self.save.get(str(i))

    def unlocked(self, i):
        # 詰まっても先に進めるよう、クリア数+3 まで開放
        cleared = sum(1 for k in range(len(LEVELS)) if self.best(k) is not None)
        return i < cleared + 3 or self.best(i) is not None

    def next_stage(self):
        for i in range(len(LEVELS)):
            if self.best(i) is None:
                return i
        return 0

    def record(self, i, moves):
        b = self.best(i)
        if b is None or moves < b:
            self.save[str(i)] = moves
            write_save(self.save)

    def start_level(self, i):
        if i >= len(LEVELS):
            self.open_select(len(LEVELS) - 1)
            return
        self.scene = Play(self, i)

    def open_select(self, cursor=0):
        self.scene = Select(self, cursor)

    def update(self):
        self.input.update()
        self.scene.update()

    def draw(self):
        self.scene.draw()


if __name__ == "__main__":
    App()
