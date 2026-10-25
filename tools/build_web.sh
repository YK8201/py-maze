#!/bin/sh
# Web版(docs/index.html)を作る。GitHub Pages で docs/ を公開するとスマホで遊べる。
set -e
cd "$(dirname "$0")/.."
rm -rf game/__pycache__ build
mkdir -p build docs
cd build
pyxel package ../game ../game/main.py
pyxel app2html game.pyxapp
cd ..
{
  cat tools/web_head.html
  # 仮想ゲームパッドは画面下のボタンと重なるので無効にする。
  # crossorigin を付けると pyxel.js 内のエラーの中身がブラウザに見えるようになる。
  tail -n +2 build/game.html \
    | sed -e "s/gamepad: \"enabled\"/gamepad: \"disabled\"/" \
          -e "s#<script src=\"\([^\"]*pyxel.js\)\">#<script src=\"\\1\" crossorigin=\"anonymous\">#"
  echo '</body></html>'
} > docs/index.html
rm -rf build
echo "built docs/index.html"
