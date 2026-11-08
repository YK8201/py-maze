# 第9章 滑るアニメーション：1フレームに少しずつ進め、マスに着くたびに判定する

今のプレイヤーは、キーを押した瞬間に行き先へ移っています。どの道を通ったのかが見えないので、どこで水に落ちたのかもわかりにくいです。この章では、プレイヤーがすっと滑っていくように見せます。

この章の変更は、これまででいちばん大きくなります。完成コード `code/step09/main.py` を横に開いて、見比べながら進めてください。

## 考え方：while のくり返しを、フレームのくり返しに置きかえる

第4章の `move` は、`while` で1マスずつ進むのを、岩にぶつかるまで1フレームの中でくり返していました。だから一瞬で移動して見えていました。

アニメーションにするには、このくり返しを何フレームかに分けます。1フレームでは少しだけ進み、残りは次のフレームに回します。Pyxel は `update` を1秒間に何十回も呼んでくれるので、その「フレームのくり返し」を `while` の代わりに使うわけです。

具体的には、次のように分けます。

- `start_move`：キーが押されたときに呼ぶ。動けるかを調べ、記録を取り、「滑っている最中」という状態にする。ここではまだ進まない
- `update_move`：滑っている最中なら毎フレーム呼ぶ。少しだけ進み、となりのマスに着いたら、これまで `while` の中でやっていた判定（水・町・岩）を行う

## 「どれだけ進んだか」をドットで覚える

プレイヤーの位置 `self.x`、`self.y` はマスの番号のままにします。それとは別に、今のマスから何ドット進んだかを `self.offset` に覚えておきます。

1フレームに `SPEED = 2` ドット進むとすると、`offset` は 0 → 2 → 4 → 6 → 8 と増えていきます。8になったら1マスぶん進んだことになるので、`self.x` か `self.y` を1つ進めて、`offset` を0に戻します。

`SPEED` は 1、2、4、8 のように、8を割り切れる数にします。3にすると 3 → 6 → 9 となって8をぴったり通らず、マスに着くたびに少しずつ位置が飛んで見えます。

## コードを書く

ファイルの最初に `SPEED` を足し、`pyxel.init` に `fps=60` を足します。fps は1秒あたりのフレーム数で、指定しなければ30です。60にすると動きがなめらかになります。

```python
TILE = 8
SPEED = 2  # 1フレームに進むドット数（8 を割り切れる数にする）
```

```python
        pyxel.init(128, 160, title="SLIDE MAZE", fps=60)
```

`load_level` の最後に、アニメーション用の変数を足します。

```python
        self.moving = False  # 滑っている最中なら True
        self.dx = 0
        self.dy = 0
        self.offset = 0  # 今のマスから何ドット進んだか
```

`move` メソッドは消して、代わりに `start_move` と `update_move` の2つを作ります。

```python
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
```

```python
    def update_move(self):
        # 1フレーム分だけ進む
        self.offset += SPEED
        if self.offset < TILE:
            return
        # となりのマスに着いた
        self.offset = 0
        self.x += self.dx
        self.y += self.dy
        tile = self.grid[self.y][self.x]
        if tile == "~":
            self.moving = False
            self.undo()  # 落ちたら、この手をなかったことにする
            self.splash = 30
            return
        if tile == "E":
            self.clear = True
            self.moving = False
            return
        if self.is_rock(self.x + self.dx, self.y + self.dy):
            self.moving = False  # 次が岩なら止まる
```

`update_move` の後半を、第8章までの `move` の `while` の中と見比べてみてください。ほとんど同じことをしています。違いは、くり返しを抜ける `break` の代わりに `self.moving = False` で「滑るのをやめる」と決めているところです。次のマスが岩なら、ここで止まります。

水に着いたときは、先に `self.moving = False` にしてから `undo` を呼んでいます。この順番には理由があります。次で `undo` に「滑っている最中は戻さない」という条件を足すので、滑るのをやめてからでないと、落ちた手を取り消せないのです。

## update と draw を書きかえる

`update` では、滑っている最中なら `update_move` だけを呼び、キーは受けつけないようにします。矢印キーで呼ぶメソッドも `start_move` に変えます。

```python
    def update(self):
        if self.splash > 0:
            self.splash -= 1
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
```

滑っている最中に UNDO されると、記録と今の位置がずれてしまいます。そこで `undo` の最初の条件にも `self.moving` を足しておきます。

```python
        if self.moving or len(self.history) == 0:
            return
```

最後に、`draw` でプレイヤーを描く位置に、進んだぶんのずれを足します。

```python
        # マスの位置 ＋ 進んだぶん だけずらして描く
        px = self.ox + self.x * TILE + self.dx * self.offset
        py = self.oy + self.y * TILE + self.dy * self.offset
        pyxel.rect(px + 1, py + 1, 6, 6, 9)
```

右に滑っているときは `dx = 1`、`dy = 0` なので、x だけが `offset` ぶんずれます。左なら `dx = -1` なので逆向きにずれます。向きの数をそのまま掛け算に使えるのが、`dx` と `dy` で向きを表しておいた利点です。

## 試してみる

`SPEED` を1や4に変えて、速さの違いを見てみてください。8にすると1フレームで1マス進みます。

水に向かって滑ると、水のマスまで進んでから元の場所に戻るようになったことにも注目してください。マスに着くたびに判定しているからです。
