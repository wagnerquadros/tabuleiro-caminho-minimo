"""Interface de caminhos mínimos. Execute: python tabuleiro.py

A interface usa Tkinter, incluído na instalação padrão do Python para Windows.
O cálculo reutiliza grafo_da_grade e dijkstra_heap de roteamento.py.
Cada célula livre é um vértice; movimentos ortogonais custam 1.
"""

import tkinter as tk
from math import inf
from tkinter import ttk

from roteamento import dijkstra_heap, grafo_da_grade

ROWS, COLS = 12, 18
START = (2, 2)
COLORS = {
    "bg": "#eef2f7", "panel": "#ffffff", "ink": "#132238",
    "muted": "#56677d", "board": "#0d1829", "cell": "#15243a",
    "grid": "#23344c", "wall": "#43566e", "wall_top": "#617791",
    "blue": "#397dff", "target": "#ffce62", "path": "#4fe2af",
    "route_cell": "#193c3c", "error": "#b22a40",
}


def default_walls():
    """Mapa fixo para facilitar a repetição da demonstração em sala."""
    walls = {(r, 5) for r in range(1, 10) if r != 7}
    walls |= {(r, c) for r in range(3, 6) for c in range(9, 13)}
    walls |= {(8, c) for c in range(8, 16) if c != 12}
    walls |= {(r, c) for r in range(1, 3) for c in range(14, 17)}
    # A célula interna (9, 2) permite demonstrar um destino sem acesso.
    walls |= {(r, c) for r in range(8, 11) for c in range(1, 4)
              if r in (8, 10) or c in (1, 3)}
    return walls


class RouteBoard:
    def __init__(self, root):
        self.root = root
        self.walls = default_walls()
        self.start = START
        self.player = START
        self.visual_player = tuple(map(float, START))
        self.target = None
        self.path = []
        self.path_index = 0
        self.frame = 0
        self.running = False
        self.paused = False
        self.job = None
        self.cell_size = 1
        self.offset = (0, 0)
        self.cursor = START
        self.compact = False
        self.mode = tk.StringVar(value="destino")
        self.status = tk.StringVar(value="Marque um destino no tabuleiro.")
        self.distance = tk.StringVar(value="—")
        self.progress = tk.StringVar(value="0 movimentos realizados")
        self.destination = tk.StringVar(value="Nenhum destino selecionado")
        self.hint = tk.StringVar(value="Clique em uma casa livre para marcar o destino.")
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _build_ui(self):
        root = self.root
        root.title("Rota mínima — Tabuleiro interativo")
        root.configure(bg=COLORS["bg"])
        width = min(1160, root.winfo_screenwidth() - 80)
        height = min(830, root.winfo_screenheight() - 100)
        root.geometry(f"{width}x{height}")
        root.minsize(920, 660)
        root.option_add("*Font", ("Segoe UI", 11))
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("TButton", padding=(14, 10), font=("Segoe UI", 11),
                        background="#e3eaf4", foreground=COLORS["ink"], borderwidth=0)
        style.map("TButton", background=[("active", "#d5e0ef")])
        style.configure("Play.TButton", background=COLORS["blue"],
                        foreground="white", font=("Segoe UI", 12, "bold"))
        style.map("Play.TButton", background=[("active", "#2867d7"),
                                               ("disabled", "#b7c9e8")],
                  foreground=[("disabled", "#53677e")])
        style.configure("Mode.TRadiobutton", background=COLORS["bg"],
                        padding=(7, 8), font=("Segoe UI", 10))

        head = tk.Frame(root, bg=COLORS["bg"])
        head.pack(fill="x", padx=26, pady=(22, 16))
        tk.Label(head, text="Rota mínima", bg=COLORS["bg"], fg=COLORS["ink"],
                 font=("Segoe UI", 25, "bold")).pack(anchor="w")
        tk.Label(head, text="Escolha um destino. O ponto azul encontra o caminho entre os obstáculos.",
                 bg=COLORS["bg"], fg=COLORS["muted"], font=("Segoe UI", 11)).pack(anchor="w", pady=(4, 0))

        body = tk.Frame(root, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=26, pady=(0, 12))
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)
        left = tk.Frame(body, bg=COLORS["bg"])
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 20))

        tools = tk.Frame(left, bg=COLORS["bg"])
        tools.pack(fill="x", pady=(0, 8))
        tk.Label(tools, text="Clique para:", bg=COLORS["bg"], fg=COLORS["muted"],
                 font=("Segoe UI", 10)).pack(side="left")
        for label, value in [("Marcar destino", "destino"), ("Mover origem", "origem"),
                             ("Editar obstáculos", "obstaculo")]:
            ttk.Radiobutton(tools, text=label, value=value, variable=self.mode,
                            command=self.mode_changed, style="Mode.TRadiobutton").pack(side="left")

        self.canvas = tk.Canvas(left, bg=COLORS["board"], highlightthickness=2,
                                highlightbackground=COLORS["board"],
                                highlightcolor=COLORS["blue"], takefocus=True)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda e: self.draw_board())
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Motion>", self.on_hover)
        self.canvas.bind("<Leave>", lambda e: self.canvas.delete("hover"))
        self.canvas.bind("<Return>", lambda e: self.select_cell(self.cursor))
        self.canvas.bind("<space>", lambda e: self.play())
        for key, delta in [("Up", (-1, 0)), ("Down", (1, 0)),
                           ("Left", (0, -1)), ("Right", (0, 1))]:
            self.canvas.bind(f"<{key}>", lambda e, d=delta: self.move_cursor(d))

        self.hint_label = tk.Label(left, textvariable=self.hint, bg=COLORS["bg"],
                                  fg=COLORS["muted"], anchor="w", justify="left",
                                  font=("Segoe UI", 10))
        self.hint_label.pack(fill="x", pady=(9, 5))
        legend = tk.Frame(left, bg=COLORS["bg"])
        legend.pack(fill="x")
        for text, color in [("●  Personagem", "#2868df"), ("◎  Destino", "#916000"),
                            ("━  Rota", "#08764e"), ("■  Obstáculo", "#43566e")]:
            tk.Label(legend, text=text, bg=COLORS["bg"], fg=color,
                     font=("Segoe UI", 10)).pack(side="left", padx=(0, 16))

        side = tk.Frame(body, bg=COLORS["panel"], width=260, padx=20, pady=20)
        self.side = side
        side.grid(row=0, column=1, sticky="ns")
        side.grid_propagate(False)
        side.columnconfigure(0, weight=1)
        tk.Label(side, text="SUA ROTA", bg="white", fg=COLORS["muted"],
                 font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w")
        tk.Label(side, textvariable=self.destination, wraplength=215, justify="left",
                 bg="white", fg=COLORS["ink"], font=("Segoe UI", 12)).grid(
                     row=1, column=0, sticky="w", pady=(12, 20))
        self.play_button = ttk.Button(side, text="▶  Play", style="Play.TButton",
                                      command=self.play, state="disabled")
        self.play_button.grid(row=2, column=0, sticky="ew")
        ttk.Button(side, text="Reiniciar percurso", command=self.restart).grid(
            row=3, column=0, sticky="ew", pady=(9, 22))
        ttk.Separator(side).grid(row=4, column=0, sticky="ew")
        tk.Label(side, text="MENOR CAMINHO", bg="white", fg=COLORS["muted"],
                 font=("Segoe UI", 10, "bold")).grid(row=5, column=0, sticky="w", pady=(20, 0))
        self.distance_label = tk.Label(side, textvariable=self.distance, bg="white",
                                       fg=COLORS["ink"], font=("Segoe UI", 40, "bold"))
        self.distance_label.grid(row=6, column=0, sticky="w")
        tk.Label(side, text="movimentos", bg="white", fg=COLORS["muted"]).grid(
            row=7, column=0, sticky="w")
        tk.Label(side, textvariable=self.progress, bg="white", fg=COLORS["muted"],
                 font=("Segoe UI", 10)).grid(row=8, column=0, sticky="w", pady=(14, 18))
        self.status_label = tk.Label(side, textvariable=self.status, wraplength=215,
                                     justify="left", bg="white", fg=COLORS["ink"],
                                     font=("Segoe UI", 11), height=4, anchor="nw")
        self.status_label.grid(row=9, column=0, sticky="nw")
        side.rowconfigure(10, weight=1)
        tk.Label(side, text="Dijkstra · custo 1 por casa\n↑ ↓ ← →  Sem diagonais", bg="white",
                 fg=COLORS["muted"], justify="left", font=("Segoe UI", 10)).grid(
                     row=11, column=0, sticky="w", pady=(20, 12))
        ttk.Button(side, text="Restaurar tabuleiro", command=self.restore).grid(
            row=12, column=0, sticky="ew")
        side.bind("<Configure>", self.fit_sidebar)
        tk.Label(root, text="Teclado no tabuleiro: setas para escolher · Enter para marcar · Espaço para Play / Pausar",
                 bg=COLORS["bg"], fg=COLORS["muted"], font=("Segoe UI", 10)).pack(pady=(0, 16))

    def fit_sidebar(self, event):
        """Reduz o espaçamento em janelas baixas, mantendo todos os controles."""
        compact = event.height < 590
        if compact == self.compact:
            return
        self.compact = compact
        self.side.configure(pady=8 if compact else 20)
        spacings = {
            1: ((5, 8), (12, 20)), 3: ((6, 8), (9, 22)),
            5: ((8, 0), (20, 0)), 8: ((4, 8), (14, 18)),
            11: ((6, 6), (20, 12)),
        }
        for row, (small, normal) in spacings.items():
            self.side.grid_slaves(row=row)[0].grid_configure(pady=small if compact else normal)
        self.status_label.configure(font=("Segoe UI", 10 if compact else 11))
        self.update_distance_font()

    def update_distance_font(self):
        size = 23 if self.distance.get() == "Sem rota" else (26 if self.compact else 40)
        self.distance_label.configure(font=("Segoe UI", size, "bold"))

    def make_graph(self):
        grade = ["".join("#" if (r, c) in self.walls else "." for c in range(COLS))
                 for r in range(ROWS)]
        return grafo_da_grade(grade)

    def cancel_animation(self):
        if self.job is not None:
            self.root.after_cancel(self.job)
            self.job = None
        self.running = False

    def clear_route(self):
        self.cancel_animation()
        self.paused = False
        self.path = []
        self.path_index = self.frame = 0
        self.visual_player = tuple(map(float, self.player))
        self.distance.set("—")
        self.update_distance_font()
        self.progress.set("0 movimentos realizados")
        self.status_label.configure(fg=COLORS["ink"])
        self.play_button.configure(text="▶  Play", state="normal" if self.target else "disabled")

    def mode_changed(self):
        hints = {"destino": "Clique em uma casa livre para marcar o destino.",
                 "origem": "Clique em uma casa livre para reposicionar o personagem.",
                 "obstaculo": "Clique para adicionar ou remover uma parede."}
        self.hint.set(hints[self.mode.get()])

    def select_cell(self, cell):
        r, c = cell
        if not (0 <= r < ROWS and 0 <= c < COLS):
            return
        self.cursor = cell
        mode = self.mode.get()
        if mode == "obstaculo":
            if cell in (self.player, self.start, self.target):
                self.status.set("Mova os pontos antes de colocar uma parede nessa casa.")
                return
            self.clear_route()
            if cell in self.walls:
                self.walls.remove(cell)
            else:
                self.walls.add(cell)
            self.status.set("Mapa atualizado. Aperte Play para calcular uma nova rota."
                            if self.target else "Mapa atualizado. Marque um destino.")
            self.draw_board()
            return
        if cell in self.walls:
            self.status.set("Essa casa é um obstáculo. Escolha uma casa livre.")
            return
        self.clear_route()
        if mode == "origem":
            self.start = self.player = cell
            self.visual_player = tuple(map(float, cell))
            self.status.set("Origem reposicionada. Marque o destino ou aperte Play.")
        else:
            self.target = cell
            self.destination.set(f"Destino: linha {r + 1}, coluna {c + 1}")
            self.status.set("Destino marcado. Aperte Play para encontrar a rota.")
        self.play_button.configure(state="normal" if self.target else "disabled")
        self.draw_board()

    def play(self):
        if self.running:
            self.cancel_animation()
            self.paused = True
            self.play_button.configure(text="▶  Continuar")
            self.status.set("Pausado. Aperte Continuar para seguir pela rota.")
            return
        if self.paused:
            self.paused = False
            self.running = True
            self.play_button.configure(text="Ⅱ  Pausar")
            self.status.set("Percorrendo a rota mais curta.")
            self.job = self.root.after(20, self.tick)
            return
        if self.target is None:
            self.status.set("Marque primeiro um destino no tabuleiro.")
            return
        self.clear_route()
        # Calculamos a rota a partir da posição ATUAL do personagem.
        cost, self.path = dijkstra_heap(self.make_graph(), self.player, self.target)
        if cost == inf:
            self.distance.set("Sem rota")
            self.update_distance_font()
            self.status.set("O destino está isolado. Remova um obstáculo ou escolha outra casa.")
            self.status_label.configure(fg=COLORS["error"])
            self.draw_overlay()
            return
        self.distance.set(str(cost))
        self.progress.set(f"0 de {cost} movimentos")
        if cost == 0:
            self.status.set("O personagem já está no destino. Escolha outra casa.")
            self.draw_overlay()
            return
        self.running = True
        self.status.set("Percorrendo a rota mais curta.")
        self.play_button.configure(text="Ⅱ  Pausar")
        self.draw_overlay()
        self.job = self.root.after(20, self.tick)

    def tick(self):
        """Anima só o desenho; o caminho completo já foi calculado por Dijkstra."""
        self.job = None
        if not self.running:
            return
        self.frame += 1
        a, b = self.path[self.path_index:self.path_index + 2]
        fraction = self.frame / 8
        self.visual_player = (a[0] + (b[0] - a[0]) * fraction,
                              a[1] + (b[1] - a[1]) * fraction)
        if self.frame == 8:
            self.player = b
            self.path_index += 1
            self.frame = 0
            self.progress.set(f"{self.path_index} de {len(self.path) - 1} movimentos")
            if self.path_index == len(self.path) - 1:
                self.running = False
                self.play_button.configure(text="▶  Play")
                self.status.set("Destino alcançado! Clique em outra casa para continuar.")
        self.draw_overlay()
        if self.running:
            self.job = self.root.after(20, self.tick)

    def restart(self):
        self.clear_route()
        self.player = self.start
        self.visual_player = tuple(map(float, self.start))
        self.status.set("De volta à origem. Aperte Play para repetir o percurso."
                        if self.target else "Marque um destino no tabuleiro.")
        self.draw_board()

    def restore(self):
        self.clear_route()
        self.walls = default_walls()
        self.start = self.player = START
        self.visual_player = tuple(map(float, START))
        self.target = None
        self.cursor = START
        self.mode.set("destino")
        self.mode_changed()
        self.destination.set("Nenhum destino selecionado")
        self.status.set("Tabuleiro restaurado. Marque um destino.")
        self.play_button.configure(state="disabled")
        self.draw_board()

    def center(self, cell):
        r, c = cell
        x, y = self.offset
        s = self.cell_size
        return x + (c + .5) * s, y + (r + .5) * s

    def cell_at(self, x, y):
        ox, oy = self.offset
        r, c = int((y - oy) // self.cell_size), int((x - ox) // self.cell_size)
        return (r, c) if 0 <= r < ROWS and 0 <= c < COLS else None

    def on_click(self, event):
        self.canvas.focus_set()
        cell = self.cell_at(event.x, event.y)
        if cell is not None:
            self.select_cell(cell)

    def on_hover(self, event):
        self.canvas.delete("hover")
        cell = self.cell_at(event.x, event.y)
        if cell is not None:
            self.draw_cursor(cell)

    def move_cursor(self, delta):
        r, c = self.cursor
        self.cursor = (max(0, min(ROWS - 1, r + delta[0])),
                       max(0, min(COLS - 1, c + delta[1])))
        self.canvas.delete("hover")
        self.draw_cursor(self.cursor)
        self.hint.set(f"Linha {self.cursor[0] + 1}, coluna {self.cursor[1] + 1} · Enter para selecionar")
        return "break"

    def draw_cursor(self, cell):
        x, y = self.center(cell)
        half = self.cell_size / 2 - 1
        self.canvas.create_rectangle(x - half, y - half, x + half, y + half,
                                     outline="#a9c4ed", width=2, tags="hover")

    def draw_board(self):
        cv = self.canvas
        width, height = cv.winfo_width(), cv.winfo_height()
        if width < 20 or height < 20:
            return
        cv.delete("all")
        self.hint_label.configure(wraplength=max(250, width - 10))
        self.cell_size = min((width - 42) / COLS, (height - 42) / ROWS)
        s = self.cell_size
        self.offset = ((width - s * COLS) / 2, (height - s * ROWS) / 2)
        ox, oy = self.offset
        for r in range(ROWS):
            for c in range(COLS):
                x, y = ox + c * s, oy + r * s
                cv.create_rectangle(x, y, x + s, y + s, fill=COLORS["cell"],
                                    outline=COLORS["grid"])
                if (r, c) in self.walls:
                    cv.create_rectangle(x + 3, y + 3, x + s - 3, y + s - 3,
                                        fill=COLORS["wall"], outline="")
                    cv.create_line(x + 4, y + 4, x + s - 4, y + 4,
                                   fill=COLORS["wall_top"], width=2)
        for c in range(COLS):
            cv.create_text(ox + (c + .5) * s, oy - 12, text=str(c + 1),
                           fill="#92a8c5", font=("Segoe UI", 8))
        for r in range(ROWS):
            cv.create_text(ox - 13, oy + (r + .5) * s, text=str(r + 1),
                           fill="#92a8c5", font=("Segoe UI", 8))
        self.draw_overlay()

    def draw_overlay(self):
        cv, s = self.canvas, self.cell_size
        cv.delete("dynamic")
        if len(self.path) > 1:
            for cell in self.path:
                x, y = self.center(cell)
                h = s / 2 - 2
                cv.create_rectangle(x - h, y - h, x + h, y + h,
                                    fill=COLORS["route_cell"], outline="", tags="dynamic")
            points = [xy for cell in self.path for xy in self.center(cell)]
            cv.create_line(*points, fill=COLORS["path"], width=max(2, s * .08),
                           capstyle="round", joinstyle="round", tags="dynamic")
            for cell in self.path[1:-1]:
                x, y = self.center(cell)
                cv.create_oval(x - 2, y - 2, x + 2, y + 2,
                               fill=COLORS["path"], outline="", tags="dynamic")
        x, y = self.center(self.start)
        radius = s * .27
        cv.create_oval(x - radius, y - radius, x + radius, y + radius,
                       outline="#75a8ff", dash=(3, 2), width=2, tags="dynamic")
        if self.target is not None:
            x, y = self.center(self.target)
            radius = s * .36
            cv.create_oval(x - radius, y - radius, x + radius, y + radius,
                           fill=COLORS["board"], outline=COLORS["target"], width=3, tags="dynamic")
            cv.create_text(x, y, text="D", fill=COLORS["target"],
                           font=("Segoe UI", max(8, int(s * .25)), "bold"), tags="dynamic")
        x, y = self.center(self.visual_player)
        radius = s * .27
        cv.create_oval(x - radius, y - radius, x + radius, y + radius,
                       fill=COLORS["blue"], outline="#b4d0ff", width=2, tags="dynamic")
        cv.create_text(x, y, text="P", fill="white",
                       font=("Segoe UI", max(8, int(s * .24)), "bold"), tags="dynamic")
        cv.tag_raise("hover")

    def close(self):
        self.cancel_animation()
        self.root.destroy()


def main():
    root = tk.Tk()
    RouteBoard(root)
    root.mainloop()


if __name__ == "__main__":
    main()
