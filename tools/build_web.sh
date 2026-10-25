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
  echo '<!doctype html>'
  echo '<html lang="ja"><head><meta charset="utf-8"><title>PY-MAZE</title>'
  echo '<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">'
  echo '</head><body style="background:#000">'
  tail -n +2 build/game.html | sed "s/gamepad: \"enabled\"/gamepad: \"disabled\"/"
  echo '</body></html>'
} > docs/index.html
rm -rf build
echo "built docs/index.html"
