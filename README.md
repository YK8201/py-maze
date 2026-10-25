# PY-MAZE

Pyxel で作った、Tomb of the Mask 風のスライド迷路パズルです。
時間制限や敵はなく、最短手数（PAR）を目指してじっくり考えるゲームにしています。

## ルール

- 上下左右に動くと、壁にぶつかるまで滑り続けます
- 黄色いドットを全部集めるとゴールが開きます
- ぬかるみ（茶色）の上を通るとそこで止まります
- ひび割れた床は、一度通り過ぎると壁になります
- PAR（最短手数）以内でクリアすると ★ がつきます
- UNDO は何回でも使えます。RESET も UNDO で取り消せます

全20ステージ。クリアした数 +3 ステージ目まで遊べます（詰まったら飛ばせます）。

## 操作

| 操作 | キーボード | スマホ |
| --- | --- | --- |
| 移動 | 矢印キー / WASD | スワイプ |
| 1手戻す | Z / U / BackSpace | UNDO ボタン |
| 最初から | R | RESET ボタン |
| ステージ選択 | Esc / M | MENU ボタン |
| 決定 | Enter / Space | タップ |

## 遊び方

### PC

```sh
pip install pyxel
pyxel run game/main.py
```

### スマホ（Web版）

`docs/index.html` が Web 版です。GitHub Pages で `docs/` フォルダを公開すると、
スマホのブラウザで遊べます（Settings → Pages → Branch でブランチと `/docs` を選択）。
GitHub の無料プランでは、Pages を使うにはリポジトリを公開（Public）にする必要があります。

ゲームを変更したら、Web 版を作り直します。

```sh
./tools/build_web.sh
```

## ファイル構成

- `game/main.py` … ゲーム本体（画面・入力・描画）
- `game/core.py` … ルール（ゲームとソルバーで共有）
- `game/levels.py` … ステージデータ
- `game/solver.py` … 最短手数を求めるソルバー。`python game/solver.py` で全ステージの PAR を検証
- `tools/gen_levels.py` … ステージ候補の自動生成ツール
- `tools/build_web.sh` … Web 版のビルド

### ステージを増やす

```sh
python tools/gen_levels.py --w 11 --h 13 --dots 4 --mud 1 --crumble 2 --min-par 14 --count 3
```

出力された迷路を `game/levels.py` に貼り付け、`python game/solver.py` で PAR を確認してください。
迷路は手で書いても構いません（`#` 壁、`.` ドット、`S` スタート、`E` ゴール、`o` ぬかるみ、`x` ひび割れた床）。
