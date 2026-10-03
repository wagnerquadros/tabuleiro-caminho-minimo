"""Etapa 4: percorrer o caminho, uma casa por vez."""
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
        self.path_index = 0
        self.job = None
        self.root.protocol("WM_DELETE_WINDOW", self.close)
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
        self.cancel_animation()
        self.path = []
        self.target = cell
        self.status.set(f"Destino: linha {r + 1}, coluna {c + 1}.")
        self.draw_board()

    def play(self):
        if self.target is None:
            self.status.set("Marque primeiro o destino.")
            return
        self.cancel_animation()
        grade = ["".join("#" if (r, c) in self.walls else "."
                         for c in range(COLS)) for r in range(ROWS)]
        cost, self.path = dijkstra_heap(grafo_da_grade(grade), self.player, self.target)
        self.path_index = 0
        self.draw_board()
        if cost == inf:
            self.status.set("Sem rota.")
            return
        if cost == 0:
            self.status.set("Você já está no destino.")
            return
        self.status.set(f"Custo mínimo: {cost} movimentos.")
        self.job = self.root.after(160, self.tick)

    def tick(self):
        self.job = None
        self.path_index += 1
        self.player = self.path[self.path_index]
        self.draw_board()
        if self.path_index < len(self.path) - 1:
            self.job = self.root.after(160, self.tick)
        else:
            self.status.set(f"Chegou em {self.path_index} movimentos.")

    def cancel_animation(self):
        if self.job is not None:
            self.root.after_cancel(self.job)
            self.job = None

    def close(self):
        self.cancel_animation()
        self.root.destroy()

    def on_click(self, event):
        r, c = event.y // CELL, event.x // CELL
        self.select_cell((r, c))


def main():
    root = tk.Tk()
    root.title("Etapa 4 - Animar o personagem")
    Tabuleiro(root)
    root.mainloop()


if __name__ == "__main__":
    main()
