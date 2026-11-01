# 第13章 おまけ：コンピュータに最短手数を探させる

自分でステージを作ると、2つのことが気になります。そもそも解けるのか、解けるなら最短で何手か、です。手で確かめるのは大変なので、コンピュータに全部の動き方を調べさせます。使うのは **幅優先探索** という方法です。

## 幅優先探索の考え方

スタートの局面から、上下左右の4通りに動いてみます。これで「1手でたどり着ける局面」がわかります。次に、そのそれぞれから4通りに動いてみて、「2手でたどり着ける局面」を集めます。これを、クリアできる局面が見つかるまで続けます。

手数の少ない順に調べているので、最初に見つかったクリアの手順が、そのまま最短の手順になります。池に石を投げたとき、波紋が近いところから順に広がっていくのに似ています。

## 「同じ局面」は2度調べない

動き方の組み合わせは、手数が増えるとすぐに膨大になります。ただ、別の手順でたどり着いても、プレイヤーの位置と迷路のようす（どのドットが残っていて、どの床が崩れたか）が同じなら、そこから先は同じです。そこで、一度調べた局面を覚えておき、同じ局面に来たら飛ばします。これで調べる量がぐっと減ります。

## コードを書く

`solver.py` という新しいファイルを、`levels.py` と同じフォルダに作ります。

```python
# 最短手数をコンピュータに求めさせるプログラム
# levels.py と同じフォルダに置いて、python solver.py で実行する
from collections import deque

from levels import LEVELS

# 向きの名前と (dx, dy)
DIRECTIONS = {"U": (0, -1), "D": (0, 1), "L": (-1, 0), "R": (1, 0)}


def start_state(level):
    """ゲームの load_level と同じように迷路を準備して (迷路, x, y) を返す"""
    grid = [list(row) for row in level["map"]]
    for y in range(len(grid)):
        for x in range(len(grid[y])):
            if grid[y][x] == "S":
                sx, sy = x, y
                grid[y][x] = " "
            elif grid[y][x] == " ":
                grid[y][x] = "."
    return grid, sx, sy


def count_dots(grid):
    n = 0
    for row in grid:
        n += row.count(".")
    return n


def slide(grid, x, y, dx, dy):
    """ゲームと同じルールで1手だけ滑らせる。
    動けなければ None、動けたら (新しい迷路, x, y, クリアしたか) を返す"""
    if grid[y + dy][x + dx] == "#":
        return None
    grid = [row[:] for row in grid]  # 元の迷路をこわさないようにコピー
    while True:
        if grid[y][x] == "x":
            grid[y][x] = "#"
        x += dx
        y += dy
        tile = grid[y][x]
        if tile == ".":
            grid[y][x] = " "
        if tile == "E" and count_dots(grid) == 0:
            return grid, x, y, True
        if tile == "o" or grid[y + dy][x + dx] == "#":
            return grid, x, y, False


def make_key(grid, x, y):
    """「位置」と「迷路のようす」をまとめて、局面を表す1つの値にする"""
    return (x, y, "".join("".join(row) for row in grid))


def solve(level):
    """幅優先探索で最短の手順を見つける。見つからなければ None"""
    grid, sx, sy = start_state(level)
    queue = deque()  # これから調べる局面の行列（先に入れたものから取り出す）
    queue.append((grid, sx, sy, ""))
    seen = set()  # もう調べた局面
    seen.add(make_key(grid, sx, sy))
    while queue:
        grid, x, y, path = queue.popleft()
        for name, (dx, dy) in DIRECTIONS.items():
            result = slide(grid, x, y, dx, dy)
            if result is None:
                continue
            new_grid, nx, ny, won = result
            if won:
                return path + name
            key = make_key(new_grid, nx, ny)
            if key in seen:
                continue
            seen.add(key)
            queue.append((new_grid, nx, ny, path + name))
    return None


if __name__ == "__main__":
    for i, level in enumerate(LEVELS):
        answer = solve(level)
        if answer is None:
            print(f"{i + 1} {level['name']}: 解けません！")
        else:
            print(f"{i + 1} {level['name']}: {len(answer)}手 {answer}  (par {level['par']})")
```

実行すると、ステージごとに最短手数と手順が表示されます。手順の `U` `D` `L` `R` は、上・下・左・右です。

```
1 SLIDE: 3手 RDL  (par 3)
2 TURN: 5手 LDRUL  (par 5)
3 CORRIDOR: 8手 URLDRULD  (par 8)
...
10 MIRE: 20手 LRDLUDLURLDLURULRRUD  (par 20)
```

## コードの読みどころ

`start_state` 関数は、ゲームの `load_level` と同じように迷路を準備します。空白のマスをドットにするところも同じです。

`slide` 関数は、第4章と第5章で作った `move` と同じルールで1手ぶん滑らせます。違うのは、`self.grid` を書きかえずに、迷路のコピーを作ってそれを動かすところです。探索では1つの局面から4通りに動いてみるので、元の迷路をこわしてしまうと、残りの3通りが試せなくなります。ここでも第7章のコピーが役に立っています。

`queue` は、これから調べる局面を並べておく行列です。`deque` は、先に入れたものから順に取り出すのが得意なリストのような入れ物で、`append` で最後に足し、`popleft` で先頭から取り出します。先に入れたもの、つまり手数の少ない局面から順に調べることになるので、幅優先探索になります。

`seen` は、一度調べた局面を覚えておく **集合（set）** です。集合は、ある値が入っているかどうかを `in` で調べるのがとても速い入れ物です。局面は、`make_key` 関数で「プレイヤーの x、y」と「迷路を1つの文字列につないだもの」の組にして表しています。

最後の `if __name__ == "__main__":` の中は、`python solver.py` でこのファイルを直接実行したときだけ動きます。第14章で、ほかのファイルからこのファイルの関数を借りるときに、全ステージを解いて表示する部分まで動いてしまわないようにするためです。

## 自作ステージを確かめる

自分で作ったステージを `levels.py` に足して `solver.py` を実行すると、解けるかどうかと最短手数がわかります。「解けません！」と出たら、どう滑っても通れないマスがあるか（第5章）、ゴールにたどり着けない迷路になっています。出てきた手数を `"par"` に書けば、ゲームでも正しい PAR が表示されます。

通路のマスが多い迷路や、崩れる床がたくさんある迷路では、残っているドットや崩れた床の組み合わせが増えて、調べ終わるまでに時間がかかることがあります。そのときは、迷路を小さくするか、崩れる床を減らしてみてください。

## さらに作りこむなら

ここから先は、自分のアイデアで広げていってください。たとえば次のようなものがあります。

- タイトル画面と、好きなステージを選べる画面
- ステージごとの最少手数を記録して、PAR で解けたステージに印を付ける
- 新しい仕掛け（ワープ、一方通行、スイッチで開く扉など）
- `solver.py` を改造して、ランダムな迷路を作り、手数の多いものだけを残すステージ自動生成

このリポジトリの `game/` フォルダにある完成版には、上の4つのうち、最初の2つと自動生成が入っています（自動生成は `tools/gen_levels.py`）。この教材とは書き方が違うところもあるので、読み比べてみるのもおもしろいと思います。

次の第14章では、自分でステージを作るときに役立つ、迷わせても詰まない迷路のコツを紹介します。
