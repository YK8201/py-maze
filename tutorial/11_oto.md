# 第11章 音と見た目：効果音は4行で作れ、絵は1マスずつの関数に分ける

ゲームの中身はできあがりました。この章では効果音を付け、湖とプレイヤーの見た目を、雪と氷の世界らしく整えます。仕組みの理解というより、手ざわりを良くする仕上げの章です。好みに合わせて自由に変えてください。

![第11章の完成画面](images/ch11.png)

## 効果音を作る

Pyxel では、音を文字で書いて作れます。`__init__` の `pyxel.init` の下に、次の4行を足します。

```python
        # 音を作る: 音の高さ, 音色, 音量, エフェクト, 速さ
        pyxel.sounds[0].set("c2", "t", "4", "f", 10)  # 止まった音
        pyxel.sounds[1].set("c4g3", "n", "3", "f", 4)  # 氷が割れる音
        pyxel.sounds[2].set("c3e3g3c4", "t", "4", "n", 12)  # クリアの音
        pyxel.sounds[3].set("a2f2c2", "n", "543", "f", 10)  # 水に落ちる音
```

`pyxel.sounds[0].set(...)` は、0番の音を作る命令です。かっこの中の5つの値は次の意味です。

| 値 | 例 | 意味 |
| --- | --- | --- |
| 音の高さ | `"c3e3g3c4"` | ドレミを英語の音名（c d e f g a b）と高さの数字で並べる。`c3e3g3c4` は「ド・ミ・ソ・高いド」 |
| 音色 | `"t"` | `t` 三角波（やわらかい）、`s` 矩形波（ピコピコ）、`n` ノイズ（ザッ） |
| 音量 | `"4"` | 0〜7。`"543"` のように並べると、1音ずつ音量を変えられる |
| エフェクト | `"f"` | `n` なし、`f` だんだん小さくする |
| 速さ | `12` | 1音の長さ。大きいほどゆっくり |

水に落ちる音は、ノイズの音色で高い音から低い音へ下げ、音量も下げていくことで「ザブン」と沈む感じを出しています。

鳴らすときは `pyxel.play(チャンネル, 音の番号)` と書きます。チャンネルは0〜3の4つあり、同じチャンネルで次の音を鳴らすと前の音は止まります。氷が割れる音と止まった音が重なっても両方聞こえるように、別のチャンネルを使います。

`update_move` の中の、氷が割れたところ・水に落ちたところ・町に着いたところ・止まったところで、それぞれ音を鳴らします。

```python
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
```

水に落ちたところでは、音を鳴らすほかに、落ちた場所を `self.splash_x` と `self.splash_y` に覚えています。このあと、そこに水しぶきを描くためです。`undo` を呼ぶとプレイヤーの位置は元に戻ってしまうので、その前に覚えておきます。

## 1マスの絵を描く関数を作る

湖の見た目を凝ろうとすると、`draw` の中の `if` がどんどん長くなります。そこで、1マスぶんの絵を描く処理を `draw_tile` というメソッドに分けます。

```python
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
```

マスの種類ごとに、次のように描いています。

- **町**：雪の上に、`pyxel.tri`（三角形）で赤い屋根、その下に壁とドア
- **岸**：湖のいちばん外側のマスは、岩でもスタートの跡でも、白い雪にする
- **岩**：氷の上に灰色の石。右と下に暗い線を引いて、影にする
- **水**：暗い青に、明るい波の線。`pyxel.frame_count` を使って、時間とともに波を左右に動かす
- **もろい氷**：濃い青に、白いひびを3本
- **氷**：水色に、白いきらめきを1点

岸かどうかを調べる `on_shore` は、x か y がいちばん外側の番号なら `True` を返すメソッドです。

```python
    def on_shore(self, x, y):
        # 湖のいちばん外側のマスなら True
        return x == 0 or y == 0 or x == self.w - 1 or y == self.h - 1
```

`pyxel.frame_count` は、ゲームが始まってから何フレーム目かを表す数です。12で割った答えは12フレームごとに1増えるので、波の線が少しずつ動きます。`+ x + y` を足しているのは、マスごとに波の位置をずらして、全部の波が同じ形にそろってしまわないようにするためです。氷のきらめきの位置も、同じように x と y から計算してマスごとにずらしています。

`draw` の中の、マスを描く二重の `for` は、`draw_tile` を呼ぶだけの短い形になります。

```python
        # 湖を1マスずつ描く
        for y in range(self.h):
            for x in range(self.w):
                px = self.ox + x * TILE
                py = self.oy + y * TILE
                self.draw_tile(x, y, px, py)
```

## プレイヤーにシルクハットをかぶせる

プレイヤーも、レイトン教授にならってシルクハットをかぶせます。

```python
    def draw_player(self, px, py):
        # オレンジの体と、黒いシルクハット
        pyxel.rect(px + 1, py + 3, 6, 5, 9)
        pyxel.rect(px + 2, py, 4, 2, 0)
        pyxel.line(px + 1, py + 2, px + 6, py + 2, 0)
        # 目は進む向きを見る
        pyxel.pset(px + 3 + self.dx, py + 4 + self.dy, 0)
        pyxel.pset(px + 4 + self.dx, py + 4 + self.dy, 0)
```

`pyxel.pset` は1ドットだけ打つ命令です。目の位置を `dx` と `dy` のぶんだけずらすと、滑る向きを見ているように見えます。ゲーム開始時に上を見ているように、`load_level` の `self.dy = 0` を `self.dy = -1` に変えておきます。

## 水しぶきの輪

最後に、水に落ちたときの水しぶきを描きます。`draw` でプレイヤーを描いたあとに、次の部分を足します。

```python
        # 水しぶきの輪（時間がたつほど大きくなる）
        if self.splash > 0:
            r = 2 + (30 - self.splash) // 4
            sx = self.ox + self.splash_x * TILE + 4
            sy = self.oy + self.splash_y * TILE + 4
            pyxel.circb(sx, sy, r, 7)
```

`pyxel.circb` は円の輪を描く命令です。`self.splash` は30から0へ減っていくので、`30 - self.splash` は落ちてからのフレーム数になります。それを4で割った数を半径に足しているので、輪がだんだん広がっていきます。
