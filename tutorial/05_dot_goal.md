# 第5章 ドットとゴール：拾ったドットは迷路から消し、残り0でゴールが開く

ドットを拾えるようにして、全部拾ったらゴールが開き、通ればクリアになるようにします。ここまで作ると、ちゃんと考えて解くパズルになります。迷路も、少し考えがいのあるものに変えます。

![第5章の完成画面](images/ch05.png)

## コードを書く

変更が何か所かに分かれているので、全体を載せます。前の章から変わったのは、`MAP` の中身、`self.clear`、`count_dots` メソッド、`move` メソッドの `while` の中、それに `draw` の後半です。

```python
import pyxel

TILE = 8

MAP = [
    "#######",
    "#.   S#",
    "# #####",
    "# #E  #",
    "# ### #",
    "#    .#",
    "#######",
]


class App:
    def __init__(self):
        pyxel.init(128, 160, title="SLIDE MAZE")
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
        self.clear = False  # クリアしたら True
        pyxel.run(self.update, self.draw)

    def is_wall(self, x, y):
        return self.grid[y][x] == "#"

    def count_dots(self):
        # 残っているドットの数をかぞえる
        n = 0
        for row in self.grid:
            n += row.count(".")
        return n

    def move(self, dx, dy):
        if self.clear:
            return
        while not self.is_wall(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy
            tile = self.grid[self.y][self.x]
            if tile == ".":
                self.grid[self.y][self.x] = " "  # ドットを拾う
            if tile == "E" and self.count_dots() == 0:
                self.clear = True  # ゴールが開いていればクリア
                break

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
                    pyxel.rect(px, py, TILE, TILE, 1)
                elif tile == ".":
                    pyxel.rect(px + 3, py + 3, 2, 2, 10)
                elif tile == "E":
                    if self.count_dots() == 0:
                        pyxel.rect(px + 1, py + 1, 6, 6, 11)  # 開いたゴール
                    else:
                        pyxel.rectb(px + 1, py + 1, 6, 6, 5)  # 閉じたゴール
        px = self.ox + self.x * TILE
        py = self.oy + self.y * TILE
        pyxel.rect(px + 1, py + 1, 6, 6, 9)

        pyxel.text(4, 4, f"DOTS {self.count_dots()}", 7)
        if self.clear:
            pyxel.rect(24, 64, 80, 24, 1)
            pyxel.text(52, 73, "CLEAR!", 10)


App()
```

この迷路は5手で解けます。まず自分で解いてみてください。

## ドットを拾う＝迷路の文字を書きかえる

`move` の `while` の中で、1マス進むたびにそのマスを調べています。

```python
            tile = self.grid[self.y][self.x]
            if tile == ".":
                self.grid[self.y][self.x] = " "  # ドットを拾う
            if tile == "E" and self.count_dots() == 0:
                self.clear = True  # ゴールが開いていればクリア
                break
```

ドットのマスに来たら、そのマスを通路 `" "` に書きかえます。これが「拾う」です。第2章で迷路をリストにしておいたのは、このためでした。

滑っている途中のマスも1つずつ調べているので、止まらずに通り過ぎたドットも拾えます。

## 残りのドットを数える

`count_dots` は、迷路の中に残っている `.` の数を返します。

```python
    def count_dots(self):
        # 残っているドットの数をかぞえる
        n = 0
        for row in self.grid:
            n += row.count(".")
        return n
```

`row.count(".")` は、リスト `row` の中に `"."` がいくつあるかを数える命令です。それを全部の行について足しています。

## ゴールは「ドットが0個なら」クリア

ゴールのマス `E` に来たとき、`count_dots()` が0ならクリアです。クリアしたことは `self.clear` という変数で覚えておきます。`self.clear` のように、状態を `True` と `False` で覚えておく変数を **フラグ** と呼びます。

クリアしたら `break` でくり返しを抜けて、その場で止まります。ドットが残っているときはゴールの上を通り過ぎるだけです。

`if` を2つ並べた順番にも意味があります。先にドットを拾ってからゴールを調べているので、最後のドットのすぐ先にゴールがあっても、同じ1回の滑りでクリアできます。

クリアしたあとは `move` の最初の `if self.clear: return` で何もしなくなり、プレイヤーは動きません。

## 文字の中に数を入れる

`draw` では、残りのドット数を画面に出しています。

```python
pyxel.text(4, 4, f"DOTS {self.count_dots()}", 7)
```

文字列の前に `f` を付けると、`{ }` の中に書いた式の値が文字列に入ります。これを **f文字列** と呼びます。ドットが2個残っていれば `DOTS 2` と表示されます。

ゴールは、ドットが残っているあいだは暗い青の枠に、0個になると緑の四角に描き分けています。開いたかどうかが一目でわかるようにするためです。

## 試してみる

`MAP` に `.` を増やして、難しくしてみてください。どこに置いても拾えるとは限りません。滑って通るマスにしか行けないので、どうやっても通れないマスにドットを置くと、そのステージは解けなくなります。それを確かめるには、自分で解いてみるしかありません。第13章では、これをコンピュータに確かめさせる方法を紹介します。
