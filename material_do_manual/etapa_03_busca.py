"""Etapa 3: calcular e desenhar o caminho mínimo."""
import tkinter as tk
from cenario import default_walls
from roteamento import grafo_da_grade, dijkstra_heap
from math import inf

ROWS, COLS, CELL = 12, 18, 34


class Tabuleiro:
    def __init__(self, root):
        self.root = root
        self.walls = default_walls()
        self.player = (2, 2)
        self.target = None
        self.path = []
        self.status = tk.StringVar(value="Clique em uma casa livre.")
        self.canvas = tk.Canvas(root, width=COLS * CELL, height=ROWS * CELL,
                                highlightthickness=0)
        self.canvas.pack(padx=16, pady=16)
        self.canvas.bind("<Button-1>", self.on_click)
        tk.Label(root, textvariable=self.status).pack(pady=8)
        tk.Button(root, text="Play", command=self.play).pack(pady=8)
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
        if len(self.path) > 1:
            points = [xy for cell in self.path for xy in self.center(cell)]
            self.canvas.create_line(*points, fill="#4fe2af", width=3)
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
        self.path = []
        self.target = cell
        self.status.set(f"Destino: linha {r + 1}, coluna {c + 1}.")
        self.draw_board()

    def play(self):
        if self.target is None:
            self.status.set("Marque primeiro o destino.")
            return
        grade = ["".join("#" if (r, c) in self.walls else "."
                         for c in range(COLS)) for r in range(ROWS)]
        grafo = grafo_da_grade(grade)
        cost, self.path = dijkstra_heap(grafo, self.player, self.target)
        self.status.set("Sem rota." if cost == inf else f"Custo mínimo: {cost} movimentos.")
        self.draw_board()

    def on_click(self, event):
        r, c = event.y // CELL, event.x // CELL
        self.select_cell((r, c))


def main():
    root = tk.Tk()
    root.title("Etapa 3 - Calcular a rota")
    Tabuleiro(root)
    root.mainloop()


if __name__ == "__main__":
    main()
