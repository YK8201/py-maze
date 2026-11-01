# 第0章 準備：Python 3.11 以降と Pyxel を入れる

ゲームを作り始める前に、プログラムを動かす環境を整えます。必要なのは Python と、その上で動く Pyxel の2つです。

## Python を確認する

Pyxel 2.9 は **Python 3.11 以降** で動きます。ターミナル（Windows なら「コマンドプロンプト」か「PowerShell」、Mac なら「ターミナル」）を開いて、次のように打ちます。

```
python --version
```

`Python 3.12.4` のようにバージョンが表示されれば入っています。Mac では `python3 --version` と打つ必要がある場合があります。表示されない、または 3.10 以前だったときは、[python.org](https://www.python.org/downloads/) から新しい Python を入れてください。Windows のインストーラーでは、最初の画面にある「Add python.exe to PATH」に必ずチェックを入れます。これを忘れると、ターミナルで `python` と打っても見つからなくなります。

## Pyxel を入れる

ターミナルで次のように打ちます（Mac では `pip3`）。

```
pip install pyxel
```

最後に `Successfully installed pyxel-...` と出れば完了です。

## 作業用のフォルダを作る

好きな場所に `slide_maze` というフォルダを作り、プログラムはその中に `main.py` という名前で保存していきます。第8章からは、同じフォルダに `levels.py` も置きます。

エディタは何でもかまいません。Python に付いてくる IDLE でも動きますが、VS Code のような、行番号と字下げが見やすいエディタのほうが楽です。

## 実行のしかた

ターミナルで `slide_maze` フォルダに移動してから実行します。

```
cd slide_maze
python main.py
```

ゲームの画面は、ウィンドウを閉じるか **Esc キー** で終了できます。

> **字下げに注意**
> Python は字下げ（行頭の空白）でプログラムの区切りを決めます。この教材ではすべて「半角スペース4つ」で字下げしています。タブとスペースが混ざると `IndentationError` というエラーになるので、エディタの設定で「Tab キーでスペース4つ」にしておくと安全です。

準備ができたら、第1章で最初のウィンドウを開きます。
