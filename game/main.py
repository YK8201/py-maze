"""PY-MAZE : じっくり考えるスライド迷路パズル

操作
    移動    : 矢印キー / WASD / スワイプ / ゲームパッド十字
    戻す    : Z / U / BackSpace / ゲームパッドA / [UNDO]
    やり直し: R / ゲームパッドB / [RESET]（やり直しも UNDO で戻せる）
    メニュー: Esc / M / ゲームパッドSTART / [MENU]
"""

import json
import os

import pyxel

from core import CRUMBLE, DOT, DOWN, EXIT, LEFT, MUD, RIGHT, UP, WALL, Level, step
from levels import LEVELS

W, H = 128, 184
TILE = 8
MAZE_Y, MAZE_H = 16, 128
SLIDE_SPEED = 0.4  # マス/フレーム
SWIPE_DIST = 5

BUTTONS_PLAY = [("UNDO", 4, 150, 38, 16), ("RESET", 45, 150, 38, 16), ("MENU", 86, 150, 38, 16)]
BUTTONS_CLEAR = [("RETRY", 20, 118, 40, 16), ("NEXT", 68, 118, 40, 16)]

HINTS = {
    0: "SWIPE: SLIDE UNTIL A WALL",
    1: "GET ALL DOTS TO OPEN THE GOAL",
    6: "MUD STOPS YOU ON IT",
    11: "CRACKED FLOOR BREAKS BEHIND YOU",
}

SAVE_KEY = "py-maze-save"


# ---------------------------------------------------------------- 保存
def load_save():
    try:
        import js  # Web版(Pyodide)では localStorage を使う

        s = js.localStorage.getItem(SAVE_KEY)
        return json.loads(s) if s else {}
    except Exception:
        pass
    try:
        with open(os.path.join(pyxel.user_data_dir("yk8201", "py-maze"), "save.json")) as f:
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
        with open(os.path.join(pyxel.user_data_dir("yk8201", "py-maze"), "save.json"), "w") as f:
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
    pyxel.sounds[1].set("a3", "s", "3", "f", 6)  # ドット
    pyxel.sounds[2].set("c3e3g3c4", "t", "4", "n", 12)  # クリア
    pyxel.sounds[3].set("g2e2", "t", "3", "f", 6)  # 戻す
    pyxel.sounds[4].set("c1", "n", "2", "f", 5)  # 動けない
    pyxel.sounds[5].set("e3g3", "t", "3", "f", 6)  # 決定
    pyxel.sounds[6].set("c3", "n", "3", "f", 8)  # 崩れる


# ---------------------------------------------------------------- プレイ画面
class Play:
    def __init__(self, app, index):
        self.app = app
        self.index = index
        self.data = LEVELS[index]
        self.level = Level(self.data["map"])
        self.state = self.level.initial_state()
        self.history = []  # 戻す用の (state, moves)
        self.moves = 0
        self.anim = None
        self.buffered = None
        self.cleared = False
        self.clear_timer = 0
        lw, lh = self.level.w * TILE, self.level.h * TILE
        self.ox = (W - lw) // 2
        self.oy = MAZE_Y + (MAZE_H - lh) // 2
        self.face = DOWN
        self.bump = 0

    # ---- 操作
    def try_move(self, d):
        r = step(self.level, self.state, d)
        self.face = d
        if r is None:
            self.bump = 6
            pyxel.play(3, 4)
            return
        new_state, path, picked = r
        self.history.append((self.state, self.moves))
        self.anim = {"path": path, "t": 0.0, "picked": picked, "new": new_state, "old": self.state}
        self.moves += 1

    def finish_anim(self):
        a = self.anim
        self.state = a["new"]
        self.anim = None
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
        if not self.history:
            return
        self.state, self.moves = self.history.pop()
        self.cleared = False
        self.buffered = None
        pyxel.play(3, 3)

    def reset(self):
        if self.anim:
            self.finish_anim()
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
        if self.anim:
            if d is not None:
                self.buffered = d
            a = self.anim
            prev_i = int(a["t"])
            a["t"] += SLIDE_SPEED
            last = len(a["path"]) - 1
            cur_i = min(int(a["t"]), last)
            for i in range(prev_i + 1, cur_i + 1):
                if a["path"][i] in a["picked"]:
                    pyxel.play(1, 1)
                if a["path"][i - 1] in self.level.crumble_index:
                    pyxel.play(2, 6)
            if a["t"] >= last:
                self.finish_anim()
                if self.buffered is not None and not self.cleared:
                    d, self.buffered = self.buffered, None
                    self.try_move(d)
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
    def view(self):
        """アニメ中は通過済みのドット/崩れる床だけ反映した見た目の状態を返す"""
        if not self.anim:
            return self.state.dots, self.state.crumbles, self.state.pos
        a = self.anim
        old = a["old"]
        dots, crumbles = old.dots, old.crumbles
        i = min(int(a["t"]), len(a["path"]) - 1)
        for k, p in enumerate(a["path"][: i + 1]):
            if p in a["picked"]:
                dots &= ~(1 << self.level.dot_index[p])
            if k < i and p in self.level.crumble_index:
                crumbles &= ~(1 << self.level.crumble_index[p])
        return dots, crumbles, None

    def player_pixel(self):
        if not self.anim:
            x, y = self.state.pos
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

    def draw_maze(self, dots, crumbles):
        lv = self.level
        open_exit = dots == 0
        for y in range(lv.h):
            for x in range(lv.w):
                px, py = self.ox + x * TILE, self.oy + y * TILE
                t = lv.tile(x, y)
                if t == WALL:
                    if self.near_open(x, y):
                        pyxel.rect(px, py, TILE, TILE, 1)
                        self.wall_edges(x, y, px, py)
                    continue
                if t == CRUMBLE and not (crumbles >> lv.crumble_index[(x, y)]) & 1:
                    # 崩れて壁になった床
                    pyxel.rect(px, py, TILE, TILE, 1)
                    pyxel.pset(px + 2, py + 2, 13)
                    pyxel.pset(px + 5, py + 3, 13)
                    pyxel.pset(px + 3, py + 5, 13)
                    pyxel.rectb(px, py, TILE, TILE, 5)
                    continue
                if t == DOT and (dots >> lv.dot_index[(x, y)]) & 1:
                    pyxel.rect(px + 3, py + 3, 2, 2, 10)
                elif t == EXIT:
                    if open_exit:
                        c = 11 if (pyxel.frame_count // 15) % 2 else 3
                        pyxel.rect(px + 1, py + 1, 6, 6, 3)
                        pyxel.rectb(px + 1, py + 1, 6, 6, c)
                        pyxel.rect(px + 3, py + 3, 2, 2, 11)
                    else:
                        pyxel.rectb(px + 1, py + 1, 6, 6, 5)
                        pyxel.line(px + 2, py + 2, px + 5, py + 5, 5)
                        pyxel.line(px + 5, py + 2, px + 2, py + 5, 5)
                elif t == MUD:
                    pyxel.rect(px + 1, py + 1, 6, 6, 4)
                    pyxel.pset(px + 2, py + 3, 2)
                    pyxel.pset(px + 5, py + 2, 2)
                    pyxel.pset(px + 4, py + 5, 2)
                elif t == CRUMBLE:
                    pyxel.rectb(px + 1, py + 1, 6, 6, 13)
                    pyxel.line(px + 2, py + 3, px + 4, py + 5, 13)
                    pyxel.line(px + 4, py + 5, px + 5, py + 2, 13)

    def near_open(self, x, y):
        lv = self.level
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if lv.tile(x + dx, y + dy) != WALL:
                    return True
        return False

    def wall_edges(self, x, y, px, py):
        lv = self.level
        if lv.tile(x, y - 1) != WALL:
            pyxel.line(px, py, px + 7, py, 12)
        if lv.tile(x, y + 1) != WALL:
            pyxel.line(px, py + 7, px + 7, py + 7, 5)
        if lv.tile(x - 1, y) != WALL:
            pyxel.line(px, py, px, py + 7, 5)
        if lv.tile(x + 1, y) != WALL:
            pyxel.line(px + 7, py, px + 7, py + 7, 5)

    def draw_player(self):
        px, py = self.player_pixel()
        px, py = round(px), round(py)
        if self.anim:
            # 軌跡
            a = self.anim
            sx, sy = a["path"][0]
            sx, sy = self.ox + sx * TILE, self.oy + sy * TILE
            if sx == px:
                y0, y1 = sorted((sy, py))
                pyxel.rect(px + 3, y0 + 3, 2, y1 - y0 + 2, 2)
            else:
                x0, x1 = sorted((sx, px))
                pyxel.rect(x0 + 3, py + 3, x1 - x0 + 2, 2, 2)
        if self.bump:
            dx, dy = {UP: (0, -1), DOWN: (0, 1), LEFT: (-1, 0), RIGHT: (1, 0)}[self.face]
            px += dx * (self.bump % 2)
            py += dy * (self.bump % 2)
        pyxel.rect(px + 1, py + 1, 6, 6, 9)
        pyxel.rectb(px + 1, py + 1, 6, 6, 10)
        # 目は進行方向を向く
        ex, ey = {UP: (0, -1), DOWN: (0, 1), LEFT: (-1, 0), RIGHT: (1, 0)}[self.face]
        pyxel.pset(px + 3 + ex, py + 3 + ey, 0)
        pyxel.pset(px + 4 + ex, py + 3 + ey, 0)

    def draw(self):
        pyxel.cls(0)
        dots, crumbles, _ = self.view()
        self.draw_maze(dots, crumbles)
        self.draw_player()

        # ヘッダー
        pyxel.rect(0, 0, W, 14, 1)
        pyxel.text(3, 2, f"{self.index + 1:02d} {self.data['name']}", 7)
        best = self.app.best(self.index)
        if best is not None:
            mark = "*" if best <= self.data["par"] else ""
            s = f"BEST {best}{mark}"
            pyxel.text(W - 3 - len(s) * 4, 2, s, 10 if mark else 13)
        left = bin(dots).count("1")
        pyxel.text(3, 8, f"MOVES {self.moves}", 7)
        pyxel.text(46, 8, f"PAR {self.data['par']}", 10)
        s = f"DOTS {len(self.level.dots) - left}/{len(self.level.dots)}"
        pyxel.text(W - 3 - len(s) * 4, 8, s, 11 if left == 0 else 6)

        # ボタン
        inp = self.app.input
        for label, x, y, w, h in BUTTONS_PLAY:
            enabled = label == "MENU" or bool(self.history)
            draw_button(label, x, y, w, h, inp.holding((x, y, w, h)), enabled)
        hint = HINTS.get(self.index)
        if hint:
            text_c(W // 2, 172, hint, 13)
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
        self.legend(6, y, "dot", "COLLECT ALL")
        self.legend(6, y + 9, "exit", "GOAL")
        self.legend(6, y + 18, "mud", "STOPS YOU")
        self.legend(6, y + 27, "crumble", "BREAKS AFTER")
        pyxel.text(70, y + 1, "* = PAR CLEAR", 10)
        pyxel.text(70, y + 10, "UNDO ANYTIME", 13)
        pyxel.text(70, y + 19, "NO TIME LIMIT", 13)

    @staticmethod
    def legend(x, y, kind, label):
        if kind == "dot":
            pyxel.rect(x + 3, y + 3, 2, 2, 10)
        elif kind == "exit":
            pyxel.rect(x + 1, y + 1, 6, 6, 3)
            pyxel.rectb(x + 1, y + 1, 6, 6, 11)
        elif kind == "mud":
            pyxel.rect(x + 1, y + 1, 6, 6, 4)
            pyxel.pset(x + 2, y + 3, 2)
            pyxel.pset(x + 5, y + 2, 2)
        elif kind == "crumble":
            pyxel.rectb(x + 1, y + 1, 6, 6, 13)
            pyxel.line(x + 2, y + 3, x + 4, y + 5, 13)
            pyxel.line(x + 4, y + 5, x + 5, y + 2, 13)
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
        text_c(W // 2, 74, "A QUIET SLIDING PUZZLE", 6)
        # 滑るプレイヤーのデモ
        t = (pyxel.frame_count % 120) / 120
        px = 20 + int(abs(t * 2 - 1) * 80)
        pyxel.rect(18, 90, 92, 1, 5)
        pyxel.rect(px + 1, 83, 6, 6, 9)
        pyxel.rectb(px + 1, 83, 6, 6, 10)
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
