"""Interface de caminhos mínimos. Execute: python tabuleiro.py

A interface usa Tkinter, incluído na instalação padrão do Python para Windows.
O cálculo reutiliza grafo_da_grade e dijkstra_heap de roteamento.py.
Cada célula livre é um vértice; movimentos ortogonais custam 1.
"""

import tkinter as tk
from concurrent.futures import ThreadPoolExecutor
from math import inf, floor, ceil
from pathlib import Path
from time import perf_counter
from tkinter import filedialog, messagebox, simpledialog, ttk

from roteamento import dijkstra_heap, grafo_da_grade
from mapas_movingai import (Mapa, ler_mapa, ler_cenarios, pontos_locais,
                           recortar, salvar_instancia, ler_instancia)

ROWS, COLS = 12, 18
START = (2, 2)
DATASET_DIR = Path(__file__).resolve().parent / "datasets" / "artificial_random"
COLORS = {
    "bg": "#eef2f7", "panel": "#ffffff", "ink": "#132238",
    "muted": "#56677d", "board": "#0d1829", "cell": "#15243a",
    "grid": "#23344c", "wall": "#43566e", "wall_top": "#617791",
    "blue": "#397dff", "target": "#ffce62", "path": "#4fe2af",
    "route_cell": "#193c3c", "error": "#b22a40",
}


def calcular_rota(grade, origem, destino):
    """Função sem Tk: construção do grafo fica fora do tempo de busca exibido."""
    grafo = grafo_da_grade(grade)
    inicio = perf_counter()
    custo, caminho = dijkstra_heap(grafo, origem, destino)
    return custo, caminho, perf_counter() - inicio


def duracao_animacao(passos, velocidade="1×"):
    """Tempo visual independente do tempo de cálculo e limitado para rotas longas."""
    if velocidade == "Instantânea":
        return 0.0
    fator = {"1×": 1, "2×": 2, "4×": 4}[velocidade]
    return min(8.0, passos * .12) / fator


def livre_mais_proxima(mapa, canto):
    """Distância Manhattan; empate por linha/coluna. Não modifica obstáculos."""
    if mapa.livre(canto):
        return canto
    livres = ((r, c) for r, linha in enumerate(mapa.grade)
              for c, simbolo in enumerate(linha) if simbolo == ".")
    return min(livres, key=lambda p: (abs(p[0]-canto[0]) + abs(p[1]-canto[1]), p[0], p[1]))


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
        self.rows, self.cols = ROWS, COLS
        self.loaded_map = None
        self.map_edited = False
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.search_future = self.search_job = None
        self.map_image = None
        self.zoom = 1.0
        self.fit_size = 1.0
        self.view_job = None
        self.player_item = self.player_text = None
        self.animation_elapsed = 0.0
        self.animation_duration = 0.0
        self.animation_clock = 0.0
        self.walls = default_walls()
        self.start = START
        self.player = START
        self.visual_player = tuple(map(float, START))
        self.target = None
        self.path = []
        self.path_index = 0
        self.running = False
        self.paused = False
        self.job = None
        self.cell_size = 1
        self.offset = (0, 0)
        self.cursor = START
        self.compact = False
        self.editing_enabled = False
        self.mode = tk.StringVar(value="destino")
        self.algorithm = tk.StringVar(value="dijkstra")
        self.status = tk.StringVar(value="Marque um destino no tabuleiro.")
        self.distance = tk.StringVar(value="—")
        self.progress = tk.StringVar(value="0 movimentos realizados")
        self.destination = tk.StringVar(value="Nenhum destino selecionado")
        self.hint = tk.StringVar(value="Clique em uma casa livre para marcar o destino.")
        self.map_name = tk.StringVar(value="Mini 12 × 18 · Tabuleiro didático")
        self.map_density = tk.StringVar(value="19,0% bloqueadas")
        self.map_info = tk.StringVar(value="12 × 18 · 175 casas livres · 41 obstáculos")
        self.search_time = tk.StringVar(value="Busca: —")
        self.zoom_label = tk.StringVar(value="Visão geral")
        self.speed = tk.StringVar(value="1×")
        self.follow = tk.BooleanVar(value=False)
        self.map_files = {p.name: p for p in sorted(DATASET_DIR.glob("*.map"))}
        self.map_choice = tk.StringVar(value="random512-20-0.map")
        self.endpoints = tk.StringVar(value="Origem: linha 3, coluna 3")
        self._build_ui()
        self.set_editing(False)
        self.update_map_info()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _build_ui(self):
        root = self.root
        root.title("Rota mínima — Mapas Random")
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
        style.configure("Zoom.TButton", padding=(7, 6), font=("Segoe UI", 10))
        style.configure("Algorithm.TLabelframe", background=COLORS["bg"])
        style.configure("Algorithm.TLabelframe.Label", background=COLORS["bg"],
                        foreground=COLORS["ink"], font=("Segoe UI", 10, "bold"))
        style.configure("Mode.TRadiobutton", background=COLORS["bg"],
                        padding=(7, 8), font=("Segoe UI", 10))

        head = tk.Frame(root, bg=COLORS["bg"])
        head.pack(fill="x", padx=26, pady=(22, 16))
        tk.Label(head, text="Rota mínima", bg=COLORS["bg"], fg=COLORS["ink"],
                 font=("Segoe UI", 25, "bold")).pack(anchor="w")
        tk.Label(head, text="Carregue um mapa e aperte Play. Use Editar para alterar pontos e obstáculos.",
                 bg=COLORS["bg"], fg=COLORS["muted"], font=("Segoe UI", 11)).pack(anchor="w", pady=(4, 0))

        arquivos = tk.Frame(root, bg=COLORS["bg"])
        arquivos.pack(fill="x", padx=26, pady=(0, 8))
        tk.Label(arquivos, text="Mapa:", bg=COLORS["bg"], fg=COLORS["muted"]).pack(side="left", padx=(0, 6))
        self.map_combo = ttk.Combobox(arquivos, textvariable=self.map_choice,
                     values=tuple(self.map_files), width=26, state="readonly")
        self.map_combo.pack(side="left", padx=(0, 8))
        for texto, acao in [("Carregar mapa", self.load_selected),
                            ("Mini 12 × 18", self.load_example)]:
            ttk.Button(arquivos, text=texto, command=acao).pack(side="left", padx=(0, 5))
        # Mostra o mapa efetivamente carregado, antes da escolha do algoritmo.
        self.map_card = tk.Frame(root, bg="#e6efff", padx=14, pady=8,
                                 highlightbackground="#c8d9f0", highlightthickness=1)
        self.map_card.pack(fill="x", padx=26, pady=(0, 10))
        map_heading = tk.Frame(self.map_card, bg="#e6efff")
        map_heading.pack(fill="x")
        map_heading.columnconfigure(0, weight=1)
        self.map_name_label = tk.Label(map_heading, textvariable=self.map_name,
            bg="#e6efff", fg="#193e75", font=("Segoe UI", 14, "bold"),
            anchor="w", justify="left", wraplength=700)
        self.map_name_label.grid(row=0, column=0, sticky="ew")
        tk.Label(map_heading, textvariable=self.map_density, bg="#d4e3ff", fg="#193e75",
                 font=("Segoe UI", 11, "bold"), padx=10, pady=5).grid(
                     row=0, column=1, sticky="e", padx=(12, 0))
        self.map_info_label = tk.Label(self.map_card, textvariable=self.map_info,
            bg="#e6efff", fg="#395374", font=("Segoe UI", 10), anchor="w",
            justify="left", wraplength=1000)
        self.map_info_label.pack(fill="x", pady=(3, 0))
        # Uma variável comum torna as opções mutuamente exclusivas.
        # Força bruta fica desativada até a implementação da próxima etapa.
        self.algorithm_section = ttk.LabelFrame(root, text="Algoritmo", padding=(12, 5),
                                                 style="Algorithm.TLabelframe")
        self.algorithm_section.pack(fill="x", padx=26, pady=(0, 8))
        self.dijkstra_option = ttk.Radiobutton(self.algorithm_section, text="Dijkstra",
            value="dijkstra", variable=self.algorithm, style="Mode.TRadiobutton")
        self.dijkstra_option.pack(side="left", padx=(0, 18))
        self.brute_force_option = ttk.Radiobutton(self.algorithm_section, text="Força bruta",
            value="forca_bruta", variable=self.algorithm, style="Mode.TRadiobutton", state="disabled")
        self.brute_force_option.pack(side="left")
        body = tk.Frame(root, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=26, pady=(0, 12))
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)
        left = tk.Frame(body, bg=COLORS["bg"])
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 20))

        tools = tk.Frame(left, bg=COLORS["bg"])
        tools.pack(fill="x", pady=(0, 8))
        self.edit_button = ttk.Button(tools, text="Editar", command=self.toggle_editing,
                                      style="Zoom.TButton", width=7)
        self.edit_button.pack(side="left", padx=(0, 8))
        self.editing_options = []
        for label, value in [("Marcar destino", "destino"), ("Mover origem", "origem"),
                             ("Editar obstáculos", "obstaculo")]:
            option = ttk.Radiobutton(tools, text=label, value=value, variable=self.mode,
                            command=self.mode_changed, style="Mode.TRadiobutton", state="disabled")
            option.pack(side="left")
            self.editing_options.append(option)

        zoom_tools = tk.Frame(left, bg=COLORS["bg"])
        zoom_tools.pack(fill="x", pady=(0, 6))
        for texto, acao in [("−", lambda: self.change_zoom(1 / 1.5)),
                            ("+", lambda: self.change_zoom(1.5)), ("Ajustar mapa", self.fit_map),
                            ("Origem", lambda: self.focus_cell(self.start)),
                            ("Destino", lambda: self.focus_cell(self.target))]:
            largura = 3 if texto in ("−", "+") else (12 if texto == "Ajustar mapa" else 7)
            ttk.Button(zoom_tools, text=texto, command=acao, style="Zoom.TButton",
                       width=largura).pack(side="left", padx=(0, 4))
        tk.Label(zoom_tools, textvariable=self.zoom_label, bg=COLORS["bg"],
                 fg=COLORS["muted"], font=("Segoe UI", 9)).pack(side="left", padx=4)
        board_area = tk.Frame(left, bg=COLORS["board"])
        board_area.pack(fill="both", expand=True)
        board_area.columnconfigure(0, weight=1)
        board_area.rowconfigure(0, weight=1)
        self.canvas = tk.Canvas(board_area, bg=COLORS["board"], highlightthickness=0,
                                takefocus=True, xscrollincrement=1, yscrollincrement=1)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.x_scroll = ttk.Scrollbar(board_area, orient="horizontal", command=self.scroll_x)
        self.y_scroll = ttk.Scrollbar(board_area, orient="vertical", command=self.scroll_y)
        self.x_scroll.grid(row=1, column=0, sticky="ew")
        self.y_scroll.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(xscrollcommand=self.x_scroll.set, yscrollcommand=self.y_scroll.set)
        self.canvas.bind("<Configure>", lambda e: self.draw_board())
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Motion>", self.on_hover)
        self.canvas.bind("<Leave>", lambda e: self.canvas.delete("hover"))
        self.canvas.bind("<MouseWheel>", self.wheel_zoom)
        for button in (2, 3):
            self.canvas.bind(f"<ButtonPress-{button}>", self.pan_start)
            self.canvas.bind(f"<B{button}-Motion>", self.pan_move)
            self.canvas.bind(f"<ButtonRelease-{button}>", lambda e: self.canvas.configure(cursor=""))
        self.canvas.bind("<Return>", lambda e: self.select_cell(self.cursor))
        self.canvas.bind("<space>", lambda e: self.play())
        self.canvas.bind("<Control-0>", lambda e: self.fit_map())
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

        self.side_view = tk.Canvas(body, bg="white", width=260, highlightthickness=0)
        self.side_view.grid(row=0, column=1, sticky="ns")
        side_scroll = ttk.Scrollbar(body, orient="vertical", command=self.side_view.yview)
        side_scroll.grid(row=0, column=2, sticky="ns")
        self.side_view.configure(yscrollcommand=side_scroll.set)
        side = tk.Frame(self.side_view, bg=COLORS["panel"], width=260, padx=20, pady=20)
        self.side = side
        self.side_window = self.side_view.create_window(0, 0, window=side, anchor="nw")
        side.columnconfigure(0, weight=1)
        tk.Label(side, text="SUA ROTA", bg="white", fg=COLORS["muted"],
                 font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w")
        tk.Label(side, textvariable=self.destination, wraplength=215, justify="left",
                 bg="white", fg=COLORS["ink"], font=("Segoe UI", 12)).grid(
                     row=1, column=0, sticky="w", pady=(12, 20))
        self.play_button = ttk.Button(side, text="▶  Play", style="Play.TButton",
                                      command=self.play, state="disabled")
        self.play_button.grid(row=2, column=0, sticky="ew")
        percurso = tk.Frame(side, bg="white")
        percurso.grid(row=3, column=0, sticky="ew", pady=(9, 22))
        ttk.Button(percurso, text="Reiniciar percurso", command=self.restart).pack(fill="x")
        ttk.Button(percurso, text="Concluir animação", command=self.finish_route).pack(fill="x", pady=(5, 0))
        velocidades = tk.Frame(percurso, bg="white")
        velocidades.pack(fill="x", pady=(8, 0))
        tk.Label(velocidades, text="Velocidade:", bg="white", font=("Segoe UI", 10)).pack(side="left")
        ttk.Combobox(velocidades, textvariable=self.speed,
                     values=("1×", "2×", "4×", "Instantânea"), state="readonly", width=11).pack(side="right")
        tk.Label(percurso, text="1×: percurso completo em até 8 s.\nA velocidade vale no próximo Play.",
                 bg="white", fg=COLORS["muted"], font=("Segoe UI", 9), justify="left").pack(anchor="w", pady=(5, 0))
        tk.Checkbutton(percurso, text="Seguir personagem no zoom", variable=self.follow,
                       bg="white", font=("Segoe UI", 9)).pack(anchor="w")
        ttk.Separator(side).grid(row=4, column=0, sticky="ew")
        tk.Label(side, text="MENOR CAMINHO", bg="white", fg=COLORS["muted"],
                 font=("Segoe UI", 10, "bold")).grid(row=5, column=0, sticky="w", pady=(20, 0))
        self.distance_label = tk.Label(side, textvariable=self.distance, bg="white",
                                       fg=COLORS["ink"], font=("Segoe UI", 40, "bold"))
        self.distance_label.grid(row=6, column=0, sticky="w")
        tk.Label(side, text="movimentos", bg="white", fg=COLORS["muted"]).grid(
            row=7, column=0, sticky="w")
        metricas = tk.Frame(side, bg="white")
        metricas.grid(row=8, column=0, sticky="w", pady=(14, 18))
        for variavel in (self.endpoints, self.progress, self.search_time):
            tk.Label(metricas, textvariable=variavel, bg="white", fg=COLORS["muted"],
                     font=("Segoe UI", 10)).pack(anchor="w")
        self.status_label = tk.Label(side, textvariable=self.status, wraplength=215,
                                     justify="left", bg="white", fg=COLORS["ink"],
                                     font=("Segoe UI", 11), height=4, anchor="nw")
        self.status_label.grid(row=9, column=0, sticky="nw")
        side.rowconfigure(10, weight=1)
        tk.Label(side, text="Dijkstra · custo 1 por casa\n↑ ↓ ← →  Sem diagonais", bg="white",
                 fg=COLORS["muted"], justify="left", font=("Segoe UI", 10)).grid(
                     row=11, column=0, sticky="w", pady=(20, 12))
        self.side_view.bind("<Configure>", self.resize_sidebar)
        side.bind("<Configure>", self.update_sidebar)
        root.bind("<Configure>", self.resize_map_info, add="+")
        tk.Label(root, text="Zoom: roda do mouse · Mover mapa: arraste com botão direito · Espaço: Play / Pausar",
                 bg=COLORS["bg"], fg=COLORS["muted"], font=("Segoe UI", 10)).pack(pady=(0, 16))

    def update_sidebar(self, event=None):
        altura = max(self.side_view.winfo_height(), self.side.winfo_reqheight())
        largura = self.side_view.winfo_width()
        self.side_view.itemconfigure(self.side_window, width=largura, height=altura)
        self.side_view.configure(scrollregion=(0, 0, largura, altura))

    def resize_sidebar(self, event):
        self.fit_sidebar(event)
        self.update_sidebar()

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

    def current_grid(self):
        return tuple("".join("#" if (r, c) in self.walls else "." for c in range(self.cols))
                     for r in range(self.rows))

    def make_graph(self):
        return grafo_da_grade(self.current_grid())

    def cancel_search(self):
        if self.search_job is not None:
            self.root.after_cancel(self.search_job)
            self.search_job = None
        if self.search_future is not None:
            self.search_future.cancel()
            self.search_future = None

    def cancel_animation(self):
        if self.job is not None:
            self.root.after_cancel(self.job)
            self.job = None
        self.running = False

    def clear_route(self):
        self.cancel_search()
        self.cancel_animation()
        self.paused = False
        self.path = []
        self.path_index = 0
        self.animation_elapsed = self.animation_duration = 0.0
        self.canvas.delete("overlay")
        self.player_item = self.player_text = None
        self.visual_player = tuple(map(float, self.player))
        self.distance.set("—")
        self.update_distance_font()
        self.progress.set("0 movimentos realizados")
        self.search_time.set("Busca: —")
        self.status_label.configure(fg=COLORS["ink"])
        self.play_button.configure(text="▶  Play", state="normal" if self.target else "disabled")

    def resize_map_info(self, event):
        if event.widget is not self.root:
            return
        name_width = max(300, event.width - 290)
        info_width = max(500, event.width - 84)
        if int(self.map_name_label.cget("wraplength")) != name_width:
            self.map_name_label.configure(wraplength=name_width)
        if int(self.map_info_label.cget("wraplength")) != info_width:
            self.map_info_label.configure(wraplength=info_width)

    def set_editing(self, enabled):
        """Habilita os controles e a edição por mouse/Enter em conjunto."""
        self.editing_enabled = bool(enabled)
        for option in self.editing_options:
            option.state(["!disabled"] if enabled else ["disabled"])
        self.edit_button.configure(text="Concluir edição" if enabled else "Editar",
                                   width=14 if enabled else 7)
        self.mode_changed()

    def toggle_editing(self):
        self.set_editing(not self.editing_enabled)

    def mode_changed(self):
        if not self.editing_enabled:
            self.hint.set("Clique em Editar para alterar pontos ou obstáculos · Roda: zoom · Botão direito: mover mapa")
            return
        hints = {"destino": "Clique em uma casa livre para marcar o destino.",
                 "origem": "Clique em uma casa livre para reposicionar o personagem.",
                 "obstaculo": "Clique para adicionar ou remover uma parede."}
        self.hint.set(hints[self.mode.get()])

    def select_cell(self, cell):
        if not self.editing_enabled:
            self.status.set("Clique em Editar para habilitar a alteração de pontos e obstáculos.")
            return
        r, c = cell
        if not (0 <= r < self.rows and 0 <= c < self.cols):
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
            self.map_edited = True
            self.update_map_info()
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
        self.endpoints.set(f"Origem: linha {self.start[0] + 1}, coluna {self.start[1] + 1}")
        self.draw_board()

    def play(self):
        if self.search_future is not None:
            return
        if self.running:
            self.advance_animation(perf_counter() - self.animation_clock)
            self.cancel_animation()
            if self.path_index == len(self.path) - 1:
                return
            self.paused = True
            self.play_button.configure(text="▶  Continuar")
            self.status.set("Pausado. Aperte Continuar para seguir pela rota.")
            return
        if self.paused:
            self.paused = False
            self.running = True
            self.play_button.configure(text="Ⅱ  Pausar")
            self.status.set("Percorrendo a rota mais curta.")
            self.animation_clock = perf_counter()
            self.job = self.root.after(20, self.tick)
            return
        if self.target is None:
            self.status.set("Marque primeiro um destino no tabuleiro.")
            return
        self.clear_route()
        # Uma cópia da entrada impede que edições alterem uma busca em andamento.
        self.draw_overlay()
        grade = self.current_grid()
        if self.rows * self.cols > 6000:
            self.status.set("Calculando a rota no mapa completo…")
            self.play_button.configure(state="disabled", text="Calculando…")
            self.search_future = self.executor.submit(calcular_rota, grade, self.player, self.target)
            self.search_job = self.root.after(40, self.poll_search)
        else:
            self.apply_result(calcular_rota(grade, self.player, self.target))

    def poll_search(self):
        """Consulta a tarefa sem esperar por ela na thread da janela."""
        self.search_job = None
        future = self.search_future
        if future is None:
            return
        if not future.done():
            self.search_job = self.root.after(40, self.poll_search)
            return
        self.search_future = None
        try:
            resultado = future.result()
        except Exception as erro:
            self.play_button.configure(text="▶  Play", state="normal")
            self.status.set(f"Não foi possível calcular: {erro}")
            return
        self.apply_result(resultado)

    def apply_result(self, resultado):
        cost, self.path, tempo = resultado
        self.search_time.set(f"Busca: {tempo * 1000:.2f} ms")
        self.play_button.configure(state="normal", text="▶  Play")
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
        self.animation_duration = duracao_animacao(len(self.path) - 1, self.speed.get())
        self.animation_elapsed = 0.0
        self.animation_clock = perf_counter()
        self.status.set("Percorrendo a rota mais curta.")
        self.play_button.configure(text="Ⅱ  Pausar")
        self.draw_overlay()
        if self.animation_duration == 0:
            self.finish_route()
        else:
            self.job = self.root.after(20, self.tick)

    def advance_animation(self, segundos):
        """Avança pelo tempo decorrido. Células puladas visualmente continuam na rota."""
        if len(self.path) < 2:
            return
        self.animation_elapsed += max(0, segundos)
        passos = len(self.path) - 1
        posicao = passos if self.animation_duration == 0 else min(
            passos, passos * self.animation_elapsed / self.animation_duration)
        indice = min(passos, floor(posicao))
        self.path_index = indice
        self.player = self.path[indice]
        if indice == passos:
            self.visual_player = tuple(map(float, self.player))
            self.running = self.paused = False
            self.play_button.configure(text="▶  Play")
            self.status.set("Destino alcançado! Clique em outra casa para continuar.")
        else:
            a, b = self.path[indice:indice + 2]
            fracao = posicao - indice
            self.visual_player = (a[0] + (b[0] - a[0]) * fracao,
                                  a[1] + (b[1] - a[1]) * fracao)
        self.progress.set(f"{indice} de {passos} movimentos")
        # Mantém os mesmos objetos: nenhum quadrado ou linha da rota é recriado.
        self.update_player()
        if self.follow.get() and self.zoom > 1:
            self.focus_cell(self.visual_player, only_if_outside=True)

    def tick(self):
        self.job = None
        if not self.running:
            return
        agora = perf_counter()
        self.advance_animation(agora - self.animation_clock)
        self.animation_clock = agora
        if self.running:
            self.job = self.root.after(20, self.tick)

    def finish_route(self):
        """Exibe imediatamente a chegada, mantendo o caminho e seu custo."""
        if len(self.path) < 2 or (not self.running and not self.paused):
            return
        self.cancel_animation()
        self.advance_animation(self.animation_duration)

    def restart(self):
        self.clear_route()
        self.player = self.start
        self.visual_player = tuple(map(float, self.start))
        self.status.set("De volta à origem. Aperte Play para repetir o percurso."
                        if self.target else "Marque um destino no tabuleiro.")
        self.draw_board()

    def restore(self):
        self.clear_route()
        self.rows, self.cols = ROWS, COLS
        self.loaded_map = None
        self.map_edited = False
        self.walls = default_walls()
        self.start = self.player = START
        self.visual_player = tuple(map(float, START))
        self.target = None
        self.cursor = START
        self.zoom = 1.0
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)
        self.endpoints.set("Origem: linha 3, coluna 3")
        self.mode.set("destino")
        self.set_editing(False)
        self.destination.set("Nenhum destino selecionado")
        self.status.set("Mini 12 × 18 carregado. Clique em Editar para marcar um destino.")
        self.play_button.configure(state="disabled")
        self.update_map_info()
        self.draw_board()

    def update_map_info(self):
        nome = self.loaded_map.nome if self.loaded_map else "Mini 12 × 18 · Tabuleiro didático"
        bloqueadas = len(self.walls)
        livres = f"{self.rows * self.cols - bloqueadas:,}".replace(",", ".")
        texto = f"{self.rows} × {self.cols} · {livres} casas livres · {bloqueadas:,} obstáculos".replace(",", ".")
        if self.loaded_map and (self.rows, self.cols, self.loaded_map.deslocamento) != (
                self.loaded_map.linhas_originais, self.loaded_map.colunas_originais, (0, 0)):
            r, c = self.loaded_map.deslocamento
            texto += f" · recorte em ({r}, {c}) do original {self.loaded_map.linhas_originais} × {self.loaded_map.colunas_originais}"
        if self.map_edited:
            texto += " · editado"
        self.map_name.set(nome)
        self.map_density.set(f"{100 * bloqueadas / (self.rows * self.cols):.1f}% bloqueadas".replace(".", ","))
        self.map_info.set(texto)

    def load_board(self, mapa, origem=None, destino=None):
        """Valida tudo antes de substituir o tabuleiro atual."""
        avisos = []
        if origem is None:
            origem = livre_mais_proxima(mapa, (0, 0))
            if origem != (0, 0):
                avisos.append(f"Origem (1, 1) bloqueada → ({origem[0]+1}, {origem[1]+1}).")
        if destino is None:
            canto = (mapa.linhas - 1, mapa.colunas - 1)
            destino = livre_mais_proxima(mapa, canto)
            if destino != canto:
                avisos.append(f"Destino ({canto[0]+1}, {canto[1]+1}) bloqueado → ({destino[0]+1}, {destino[1]+1}).")
        if not mapa.livre(origem) or not mapa.livre(destino):
            raise ValueError("Os pontos precisam estar em casas livres do mapa.")
        self.clear_route()
        self.loaded_map = mapa
        self.map_edited = mapa.alterado
        self.rows, self.cols = mapa.linhas, mapa.colunas
        self.walls = mapa.paredes
        self.start = self.player = self.cursor = origem
        self.visual_player = tuple(map(float, origem))
        self.target = destino
        self.mode.set("destino")
        self.set_editing(False)
        self.destination.set(f"Destino: linha {destino[0] + 1}, coluna {destino[1] + 1}"
                             if destino is not None else "Nenhum destino selecionado")
        self.play_button.configure(state="normal" if destino is not None else "disabled")
        self.status.set(" ".join(avisos) + (" " if avisos else "") + "Mapa carregado. Aperte Play.")
        self.endpoints.set(f"Origem: linha {origem[0]+1}, coluna {origem[1]+1}")
        self.zoom = 1.0
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)
        self.mode_changed()
        self.update_map_info()
        self.draw_board()

    def load_map_file(self, caminho):
        if Path(caminho).suffix.lower() == ".json":
            self.load_board(*ler_instancia(caminho))
        else:
            self.load_board(ler_mapa(caminho))

    def open_map(self):
        caminho = filedialog.askopenfilename(parent=self.root, title="Abrir mapa ou instância",
            initialdir=DATASET_DIR, filetypes=[("Mapas e instâncias", "*.map *.json"), ("Todos", "*.*")])
        if caminho:
            try:
                self.load_map_file(caminho)
            except (OSError, ValueError, UnicodeError) as erro:
                messagebox.showerror("Mapa não carregado", str(erro), parent=self.root)

    def load_selected(self):
        try:
            self.load_map_file(self.map_files[self.map_choice.get()])
        except (OSError, ValueError, UnicodeError, KeyError) as erro:
            messagebox.showerror("Mapa não carregado", str(erro), parent=self.root)

    def load_example(self):
        """O Mini usa o tabuleiro fixo do antigo botão Restaurar tabuleiro."""
        self.restore()

    def current_map(self):
        base = self.loaded_map
        return Mapa(self.current_grid(), base.nome if base else "tabuleiro_didatico",
            base.fonte if base else "gerado pelo aplicativo", base.sha256_original if base else "",
            base.linhas_originais if base else self.rows,
            base.colunas_originais if base else self.cols,
            base.deslocamento if base else (0, 0), self.map_edited)

    def crop_dialog(self):
        atual = self.current_map()
        dialogo = tk.Toplevel(self.root)
        dialogo.title("Recortar região do mapa")
        dialogo.transient(self.root)
        dialogo.grab_set()
        tk.Label(dialogo, text="Informe posições do mapa atual, começando em 1.\nO recorte mantém as células sem redimensionar.",
                 justify="left").grid(row=0, column=0, columnspan=2, padx=18, pady=14)
        valores = []
        for i, (titulo, valor) in enumerate([("Linha inicial", 1), ("Coluna inicial", 1),
                                            ("Quantidade de linhas", min(12, self.rows)),
                                            ("Quantidade de colunas", min(18, self.cols))], 1):
            tk.Label(dialogo, text=titulo).grid(row=i, column=0, sticky="w", padx=18, pady=5)
            campo = ttk.Entry(dialogo, width=10)
            campo.insert(0, str(valor))
            campo.grid(row=i, column=1, padx=18, pady=5)
            valores.append(campo)
        def aplicar():
            try:
                r, c, h, w = (int(campo.get()) for campo in valores)
                mapa = recortar(atual, r - 1, c - 1, h, w)
                self.load_board(mapa)
            except ValueError as erro:
                messagebox.showerror("Recorte inválido", str(erro), parent=dialogo)
                return
            dialogo.destroy()
        ttk.Button(dialogo, text="Aplicar recorte", command=aplicar).grid(
            row=5, column=0, columnspan=2, padx=18, pady=16)
        valores[0].focus_set()

    def apply_scenario(self, cenario):
        if self.loaded_map is None:
            raise ValueError("Carregue primeiro o mapa ao qual o cenário pertence.")
        mapa = self.current_map()
        origem, destino = pontos_locais(mapa, cenario)
        self.load_board(mapa, origem, destino)
        self.status.set("Cenário carregado. Play recalcula a rota com quatro direções e custo 1.")

    def open_scenario(self):
        if self.loaded_map is None:
            messagebox.showinfo("Carregar cenário", "Abra primeiro um mapa público.", parent=self.root)
            return
        caminho = filedialog.askopenfilename(parent=self.root, title="Abrir cenários do mapa",
            initialdir=DATASET_DIR, filetypes=[("Cenários Moving AI", "*.scen")])
        if not caminho:
            return
        try:
            cenarios = ler_cenarios(caminho, self.loaded_map)
            indice = simpledialog.askinteger("Escolher caso", f"Este arquivo tem {len(cenarios)} casos.\nQual caso deseja carregar? (1 a {len(cenarios)})",
                parent=self.root, initialvalue=1, minvalue=1, maxvalue=len(cenarios))
            if indice is not None:
                self.apply_scenario(cenarios[indice - 1])
        except (OSError, ValueError, UnicodeError) as erro:
            messagebox.showerror("Cenário não carregado", str(erro), parent=self.root)

    def save_instance(self):
        caminho = filedialog.asksaveasfilename(parent=self.root, title="Salvar instância reproduzível",
            defaultextension=".json", filetypes=[("Instância do tabuleiro", "*.json")])
        if caminho:
            try:
                salvar_instancia(caminho, self.current_map(), self.current_grid(), self.start, self.target)
                self.status.set("Instância salva com mapa, pontos, regras e procedência do recorte.")
            except (OSError, ValueError) as erro:
                messagebox.showerror("Instância não salva", str(erro), parent=self.root)

    def center(self, cell):
        r, c = cell
        x, y = self.offset
        s = self.cell_size
        return x + (c + .5) * s, y + (r + .5) * s

    def cell_at(self, x, y):
        # Eventos do mouse usam coordenadas da janela; o mapa usa o Canvas virtual.
        x, y = self.canvas.canvasx(0) + x, self.canvas.canvasy(0) + y
        ox, oy = self.offset
        r, c = floor((y - oy) / self.cell_size), floor((x - ox) / self.cell_size)
        return (r, c) if 0 <= r < self.rows and 0 <= c < self.cols else None

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
            self.hint.set(f"Linha {cell[0]+1}, coluna {cell[1]+1} · Roda: zoom · Botão direito: mover mapa")

    def move_cursor(self, delta):
        r, c = self.cursor
        self.cursor = (max(0, min(self.rows - 1, r + delta[0])),
                       max(0, min(self.cols - 1, c + delta[1])))
        self.focus_cell(self.cursor, only_if_outside=True)
        self.canvas.delete("hover")
        self.draw_cursor(self.cursor)
        acao = "Enter para selecionar" if self.editing_enabled else "Editar para habilitar seleção"
        self.hint.set(f"Linha {self.cursor[0] + 1}, coluna {self.cursor[1] + 1} · {acao}")
        return "break"

    def draw_cursor(self, cell):
        x, y = self.center(cell)
        half = max(.5, self.cell_size / 2 - 1)
        self.canvas.create_rectangle(x - half, y - half, x + half, y + half,
                                     outline="#a9c4ed", width=2, tags="hover")

    def queue_view(self):
        """Agrupa eventos de arraste/rolagem em um único redesenho da região visível."""
        if self.view_job is None:
            self.view_job = self.root.after_idle(self.refresh_view)

    def refresh_view(self):
        self.view_job = None
        self.draw_background()

    def scroll_x(self, *args):
        self.canvas.xview(*args)
        self.queue_view()

    def scroll_y(self, *args):
        self.canvas.yview(*args)
        self.queue_view()

    def pan_start(self, event):
        self.canvas.scan_mark(event.x, event.y)
        self.canvas.configure(cursor="fleur")

    def pan_move(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.queue_view()
        return "break"

    def wheel_zoom(self, event):
        if event.delta:
            self.change_zoom(1.5 if event.delta > 0 else 1 / 1.5, (event.x, event.y))
        return "break"

    def change_zoom(self, factor, anchor=None):
        cv = self.canvas
        if anchor is None:
            anchor = (cv.winfo_width() / 2, cv.winfo_height() / 2)
        # Preserva a posição do mapa sob o ponteiro durante o zoom.
        cx = (cv.canvasx(anchor[0]) - self.offset[0]) / self.cell_size
        cy = (cv.canvasy(anchor[1]) - self.offset[1]) / self.cell_size
        limite = max(1.0, 64.0 / self.fit_size)
        novo = max(1.0, min(limite, self.zoom * factor))
        if abs(novo - self.zoom) < .00001:
            return
        self.zoom = novo
        self.draw_board()
        left = self.offset[0] + cx * self.cell_size - anchor[0]
        top = self.offset[1] + cy * self.cell_size - anchor[1]
        cv.xview_moveto(max(0, left) / self.world_size[0])
        cv.yview_moveto(max(0, top) / self.world_size[1])
        self.draw_background()

    def fit_map(self):
        self.zoom = 1.0
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)
        self.draw_board()
        return "break"

    def focus_cell(self, cell, only_if_outside=False):
        if cell is None:
            return
        cv = self.canvas
        x, y = self.center(cell)
        w, h = cv.winfo_width(), cv.winfo_height()
        left, top = cv.canvasx(0), cv.canvasy(0)
        margem = min(40, w / 4, h / 4)
        if only_if_outside and left + margem <= x <= left + w - margem and top + margem <= y <= top + h - margem:
            return
        cv.xview_moveto(max(0, x - w / 2) / self.world_size[0])
        cv.yview_moveto(max(0, y - h / 2) / self.world_size[1])
        self.queue_view()

    def draw_board(self):
        """Recalcula a projeção apenas em mudanças do mapa, tamanho ou zoom."""
        cv = self.canvas
        width, height = cv.winfo_width(), cv.winfo_height()
        if width < 20 or height < 20:
            return
        self.hint_label.configure(wraplength=max(250, width - 10))
        self.fit_size = max(.01, min((width - 32) / self.cols, (height - 32) / self.rows))
        self.zoom = max(1.0, min(self.zoom, max(1.0, 64 / self.fit_size)))
        self.cell_size = self.fit_size * self.zoom
        mw, mh = self.cell_size * self.cols, self.cell_size * self.rows
        self.offset = (max(16, (width - mw) / 2), max(16, (height - mh) / 2))
        self.world_size = (max(width, ceil(mw + 32)), max(height, ceil(mh + 32)))
        cv.configure(scrollregion=(0, 0, *self.world_size))
        self.zoom_label.set("Visão geral" if self.zoom == 1 else f"{self.zoom:.1f}×")
        cv.delete("all")
        self.player_item = self.player_text = None
        self.draw_background()
        self.draw_overlay()

    def draw_background(self):
        """Só desenha células/pixels visíveis, mesmo quando o mapa virtual é enorme."""
        cv, s = self.canvas, self.cell_size
        if cv.winfo_width() < 20 or cv.winfo_height() < 20:
            return
        cv.delete("map")
        ox, oy = self.offset
        vx, vy = cv.canvasx(0), cv.canvasy(0)
        vw, vh = cv.winfo_width(), cv.winfo_height()
        c0, r0 = max(0, floor((vx-ox)/s)), max(0, floor((vy-oy)/s))
        c1 = min(self.cols, ceil((vx+vw-ox)/s))
        r1 = min(self.rows, ceil((vy+vh-oy)/s))
        if c0 >= c1 or r0 >= r1:
            return
        if s >= 6 and (r1-r0)*(c1-c0) <= 6000:
            self.map_image = None
            for r in range(r0, r1):
                for c in range(c0, c1):
                    x, y = ox+c*s, oy+r*s
                    wall = (r, c) in self.walls
                    cv.create_rectangle(x, y, x+s, y+s,
                        fill=COLORS["wall"] if wall else COLORS["cell"],
                        outline=COLORS["grid"], tags="map")
                    if wall and s >= 12:
                        cv.create_line(x+2, y+2, x+s-2, y+2,
                                       fill=COLORS["wall_top"], width=2, tags="map")
            intervalo = max(1, ceil(22/s))
            for c in range(c0, c1, intervalo):
                cv.create_text(ox+(c+.5)*s, oy-8, text=str(c+1),
                               fill="#92a8c5", font=("Segoe UI", 8), tags="map")
            for r in range(r0, r1, intervalo):
                cv.create_text(ox-9, oy+(r+.5)*s, text=str(r+1),
                               fill="#92a8c5", font=("Segoe UI", 8), tags="map")
        else:
            self.draw_overview()
        cv.tag_lower("map")

    def draw_overview(self):
        """Raster da janela visível. Não cria uma imagem do tamanho total do zoom."""
        cv, s = self.canvas, self.cell_size
        ox, oy = self.offset
        x0, y0 = max(floor(ox), floor(cv.canvasx(0))), max(floor(oy), floor(cv.canvasy(0)))
        x1 = min(ceil(ox+self.cols*s), ceil(cv.canvasx(cv.winfo_width())))
        y1 = min(ceil(oy+self.rows*s), ceil(cv.canvasy(cv.winfo_height())))
        largura, altura = x1-x0, y1-y0
        if largura <= 0 or altura <= 0:
            return
        colunas = [min(self.cols-1, max(0, floor((x+.5-ox)/s))) for x in range(x0,x1)]
        livre = bytes.fromhex(COLORS["cell"][1:])
        parede = bytes.fromhex(COLORS["wall"][1:])
        linhas_pixels = {}
        pixels = bytearray()
        for y in range(y0, y1):
            r = min(self.rows-1, max(0, floor((y+.5-oy)/s)))
            if r not in linhas_pixels:
                linhas_pixels[r] = b"".join(parede if (r,c) in self.walls else livre for c in colunas)
            pixels.extend(linhas_pixels[r])
        dados = f"P6\n{largura} {altura}\n255\n".encode() + pixels
        self.map_image = tk.PhotoImage(master=self.root, data=bytes(dados), format="PPM")
        cv.create_image(x0, y0, image=self.map_image, anchor="nw", tags="map")

    def draw_overlay(self):
        """A rota é uma única linha. Objetos do personagem ficam separados."""
        cv, s = self.canvas, self.cell_size
        cv.delete("overlay")
        if len(self.path) > 1:
            points = [xy for cell in self.path for xy in self.center(cell)]
            cv.create_line(*points, fill=COLORS["path"], width=max(1.5, min(6,s*.12)),
                           capstyle="round", joinstyle="round", tags=("overlay", "route"))
        x, y = self.center(self.start)
        radius = max(3, s * .27)
        cv.create_oval(x-radius, y-radius, x+radius, y+radius,
                       outline="#75a8ff", dash=(3,2), width=2, tags="overlay")
        if self.target is not None:
            x, y = self.center(self.target)
            radius = max(4, s * .36)
            cv.create_oval(x-radius, y-radius, x+radius, y+radius,
                           fill=COLORS["board"], outline=COLORS["target"], width=2, tags="overlay")
            if s >= 12:
                cv.create_text(x, y, text="D", fill=COLORS["target"],
                               font=("Segoe UI", max(8,int(s*.25)), "bold"), tags="overlay")
        self.player_item = cv.create_oval(0,0,0,0, fill=COLORS["blue"],
                                          outline="#b4d0ff", width=2, tags=("overlay", "player"))
        self.player_text = None
        if s >= 12:
            self.player_text = cv.create_text(0,0, text="P", fill="white",
                font=("Segoe UI", max(8,int(s*.24)), "bold"), tags=("overlay", "player"))
        self.update_player()
        cv.tag_raise("hover")

    def update_player(self):
        if self.player_item is None:
            return
        x, y = self.center(self.visual_player)
        radius = max(3, self.cell_size * .27)
        self.canvas.coords(self.player_item, x-radius, y-radius, x+radius, y+radius)
        if self.player_text is not None:
            self.canvas.coords(self.player_text, x, y)

    def close(self):
        self.cancel_search()
        self.cancel_animation()
        if self.view_job is not None:
            self.root.after_cancel(self.view_job)
        self.executor.shutdown(wait=False, cancel_futures=True)
        self.root.destroy()


def main():
    root = tk.Tk()
    app = RouteBoard(root)
    # A seleção inicial já mostra um mapa do pacote recebido.
    root.after_idle(app.load_selected)
    root.mainloop()


if __name__ == "__main__":
    main()
