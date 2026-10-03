"""Etapa 2: desenhar o mapa e marcar o destino com um clique."""
import tkinter as tk
from cenario import default_walls

ROWS, COLS, CELL = 12, 18, 34


class Tabuleiro:
    def __init__(self, root):
        self.root = root
        self.walls = default_walls()
        self.player = (2, 2)
        self.target = None
        self.status = tk.StringVar(value="Clique em uma casa livre.")
        self.canvas = tk.Canvas(root, width=COLS * CELL, height=ROWS * CELL,
                                highlightthickness=0)
        self.canvas.pack(padx=16, pady=16)
        self.canvas.bind("<Button-1>", self.on_click)
        tk.Label(root, textvariable=self.status).pack(pady=8)
        self.draw_board()

    def center(self, cell):
        r, c = cell
        return (c + 0.5) * CELL, (r + 0.5) * CELL

    def draw_board(self):
        self.canvas.delete("all")
        for r in range(ROWS):
            for c in range(COLS):
                x, y = c * CELL, r * CELL
                color = "#43566e" if (r, c) in self.walls else "#15243a"
                self.canvas.create_rectangle(x, y, x + CELL, y + CELL,
                                              fill=color, outline="#23344c")
        if self.target is not None:
            x, y = self.center(self.target)
            self.canvas.create_oval(x - 12, y - 12, x + 12, y + 12,
                                    outline="#ffce62", width=3)
        x, y = self.center(self.player)
        self.canvas.create_oval(x - 9, y - 9, x + 9, y + 9,
                                fill="#397dff", outline="white")

    def select_cell(self, cell):
        r, c = cell
        if not (0 <= r < ROWS and 0 <= c < COLS):
            return
        if cell in self.walls:
            self.status.set("Escolha uma casa sem obstáculo.")
            return
        self.target = cell
        self.status.set(f"Destino: linha {r + 1}, coluna {c + 1}.")
        self.draw_board()

    def on_click(self, event):
        r, c = event.y // CELL, event.x // CELL
        self.select_cell((r, c))


def main():
    root = tk.Tk()
    root.title("Etapa 2 - Tabuleiro e clique")
    Tabuleiro(root)
    root.mainloop()


if __name__ == "__main__":
    main()
