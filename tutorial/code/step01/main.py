import pyxel


class App:
    def __init__(self):
        pyxel.init(128, 160, title="SLIDE MAZE")
        pyxel.run(self.update, self.draw)

    def update(self):
        pass

    def draw(self):
        pyxel.cls(0)
        pyxel.text(44, 60, "HELLO MAZE", 7)
        pyxel.rect(60, 80, 8, 8, 9)


App()
