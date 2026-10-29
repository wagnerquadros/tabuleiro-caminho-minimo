"""Interface de caminhos mínimos. Execute: python tabuleiro.py

A interface usa Tkinter, incluído na instalação padrão do Python para Windows.
O cálculo usa BFS, as duas versões de Dijkstra, BMSSP e força bruta de roteamento.py.
Cada célula livre é um vértice; movimentos ortogonais custam 1.
"""

import base64
import json
import struct
import subprocess
import sys
import tkinter as tk
import zlib
from concurrent.futures import CancelledError, ThreadPoolExecutor
from math import inf, floor, ceil
from pathlib import Path
import re
from queue import Empty, SimpleQueue
from time import perf_counter
from tkinter import messagebox, ttk
from threading import Event, Thread

from roteamento import bfs, bmssp, dijkstra_simples, dijkstra_heap, forca_bruta, grafo_da_grade
from mapas_movingai import ler_mapa, pontos_definidos

ROWS, COLS = 12, 18
BLOCO = 256
EXPLORADOR = Path(__file__).resolve().with_name("explorador.py")
START = (2, 2)
DATASET_DIR = Path(__file__).resolve().parent / "datasets" / "artificial_random"
ALGORITMOS = {
    "dijkstra_simples": ("Dijkstra — livro (varredura)", dijkstra_simples),
    "dijkstra": ("Dijkstra — min-heap", dijkstra_heap),
    "bfs": ("BFS — fila FIFO", bfs),
    "bmssp": ("BMSSP — Duan et al. (2025)", bmssp),
    "forca_bruta": ("Força bruta", forca_bruta),
}

ROTULOS_CURTOS = {
    "dijkstra_simples": "Dijkstra (livro)", "dijkstra": "Dijkstra (heap)",
    "bfs": "BFS", "bmssp": "BMSSP", "forca_bruta": "Força bruta",
}
DESCRICOES = {
    "dijkstra_simples": "Skiena, seção 6.3.1 · varredura linear · O(V²) · para ao alcançar o destino",
    "dijkstra": "Fila de prioridade min-heap · O(V log V) na grade · para ao alcançar o destino",
    "bfs": "Fila FIFO · O(V) · vale só quando todo movimento custa 1",
    "bmssp": "Duan et al. (2025) · O(m log^(2/3) n) teórico · calcula todas as casas",
    "forca_bruta": "Enumera todas as rotas simples · tempo exponencial · use mapas pequenos",
}

COLORS = {
    "bg": "#09090b", "panel": "#09090b", "card": "#09090b",
    "secondary": "#27272a", "secondary_hover": "#323236", "accent": "#1f1f23",
    "line": "#27272a", "ring": "#3f3f46", "ink": "#fafafa", "muted": "#a1a1aa",
    "primary": "#fafafa", "primary_fg": "#18181b", "primary_hover": "#e4e4e7",
    "board": "#09090b", "cell": "#2a2a30", "grid": "#3a3a42",
    "wall": "#101013", "wall_top": "#1c1c20",
    "blue": "#3b82f6", "target": "#fbbf24", "path": "#2dd4bf",
    "attempt": "#fb923c",
    "explored": "#ca8a04", "explored_front": "#fde047", "explored_grid": "#a16207",
    "error": "#f87171",
}


def png_arredondado(raio, cor, contorno=None, lado=None):
    """PNG (base64) de um retângulo com cantos arredondados e borda opcional de 1 px.

    O Tkinter não arredonda widgets; o ttk estica esta imagem como fundo
    (borda = raio + 2), preservando os cantos. Fora do arredondado é transparente.
    O miolo é grande porque o ttk o repete em mosaico: um miolo minúsculo
    exigiria milhares de cópias para cobrir o tabuleiro.
    """
    lado = lado or 2 * raio + 124
    preenchimento = bytes.fromhex(cor.lstrip("#"))
    borda = bytes.fromhex((contorno or cor).lstrip("#"))
    amostras = [(i + .5) / 4 for i in range(4)]

    def cobertura(px, py, r, recuo):
        """1 se o ponto está no retângulo arredondado recuado em `recuo` px."""
        a, b = recuo + r, lado - recuo - r
        cx, cy = min(max(px, a), b), min(max(py, a), b)
        return (px - cx) ** 2 + (py - cy) ** 2 <= r * r and \
            recuo <= px <= lado - recuo and recuo <= py <= lado - recuo

    def pixel(x, y):
        fora = dentro = 0
        for sy in amostras:
            for sx in amostras:
                fora += cobertura(x + sx, y + sy, raio, 0)
                dentro += cobertura(x + sx, y + sy, max(raio - 1, 0), 1)
        if not fora:
            return bytes(4)
        # Mistura borda e preenchimento pela fração interna; alfa pela externa.
        t = dentro / fora
        rgb = bytes(round(f * t + c * (1 - t)) for f, c in zip(preenchimento, borda))
        return rgb + bytes((round(255 * fora / 16),))

    cheio = preenchimento + b"\xff"
    aresta = borda + b"\xff"
    linhas = bytearray()
    for y in range(lado):
        linhas.append(0)
        if raio + 1 <= y < lado - raio - 1:
            # Linha do meio: só a primeira e a última coluna são borda.
            linhas += aresta + cheio * (lado - 2) + aresta
            continue
        for x in range(lado):
            linhas += pixel(x, y)

    return codificar_png(lado, lado, linhas)


def codificar_png(largura, altura, linhas):
    """Base64 de um PNG RGBA; `linhas` já traz o byte de filtro 0 em cada linha."""
    def bloco(tipo, dados):
        corpo = tipo + dados
        return struct.pack(">I", len(dados)) + corpo + struct.pack(">I", zlib.crc32(corpo))

    png = (bytes.fromhex("89504e470d0a1a0a")  # assinatura PNG
           + bloco(b"IHDR", struct.pack(">IIBBBBB", largura, altura, 8, 6, 0, 0, 0))
           + bloco(b"IDAT", zlib.compress(bytes(linhas)))
           + bloco(b"IEND", b""))
    return base64.b64encode(png).decode("ascii")


def png_interruptor(trilho, botao, ligado, largura=34, altura=20, margem=8):
    """Interruptor no estilo shadcn: pílula com um círculo à esquerda ou à direita.

    A margem transparente à direita separa o interruptor do texto.
    """
    raio = altura / 2
    centro_x = largura - raio if ligado else raio
    rt, rb = bytes.fromhex(trilho.lstrip("#")), bytes.fromhex(botao.lstrip("#"))
    amostras = [(i + .5) / 4 for i in range(4)]
    linhas = bytearray()
    for y in range(altura):
        linhas.append(0)
        for x in range(largura + margem):
            na_pilula = no_botao = 0
            for sy in amostras:
                for sx in amostras:
                    px, py = x + sx, y + sy
                    cx = min(max(px, raio), largura - raio)
                    na_pilula += px <= largura and (px - cx) ** 2 + (py - raio) ** 2 <= raio * raio
                    no_botao += (px - centro_x) ** 2 + (py - raio) ** 2 <= (raio - 2.5) ** 2
            if not na_pilula:
                linhas += bytes(4)
                continue
            t = no_botao / 16
            linhas += bytes(round(b * t + a * (1 - t)) for a, b in zip(rt, rb))
            linhas.append(round(255 * na_pilula / 16))
    return codificar_png(largura + margem, altura, linhas)


class BuscaAoVivo:
    """Executa explorador.py em outro processo e recebe a exploração enquanto ela acontece.

    Imita um Future (done, result, cancel), então o tabuleiro trata esta busca
    como as demais tarefas de segundo plano. Uma linha de execução apenas lê a
    saída do processo; a janela consome `casas` e `progresso` quando quiser.
    """

    def __init__(self, grade, origem, destino, algoritmo, explorar=True):
        self.explorar = explorar
        self.casas = SimpleQueue()
        self.progresso = SimpleQueue()
        self.exploracao_completa = False
        self.tentativa = None
        self._resultado = self._erro = None
        self._pronto = self._cancelado = False
        self._fim = Event()
        self._entrada = json.dumps({"grade": list(grade), "origem": list(origem),
                                    "destino": list(destino), "algoritmo": algoritmo,
                                    "explorar": explorar})
        self.processo = subprocess.Popen(
            [sys.executable, "-B", str(EXPLORADOR)], cwd=str(EXPLORADOR.parent),
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        Thread(target=self._ler, daemon=True).start()

    def _ler(self):
        try:
            # A entrada é escrita aqui para não travar a janela em mapas grandes.
            self.processo.stdin.write(self._entrada)
            self.processo.stdin.close()
            for linha in self.processo.stdout:
                tipo, _, resto = linha.rstrip("\n").partition(" ")
                if tipo == "C":
                    self.casas.put([tuple(map(int, par.split(","))) for par in resto.split()])
                elif tipo == "P":
                    self.progresso.put(tuple(map(int, resto.split())))
                elif tipo == "A":
                    self.tentativa = tuple(tuple(map(int, par.split(","))) for par in resto.split())
                elif tipo == "F":
                    self.exploracao_completa = True
                    self.tentativa = None
                elif tipo == "R":
                    dados = json.loads(resto)
                    custo = inf if dados["custo"] is None else dados["custo"]
                    self._resultado = (custo, [tuple(c) for c in dados["caminho"]], dados["tempo"])
                elif tipo == "E":
                    self._erro = RuntimeError(resto)
            self.processo.wait()
            if self._resultado is None and self._erro is None and not self._cancelado:
                detalhe = self.processo.stderr.read().strip().splitlines()
                self._erro = RuntimeError(detalhe[-1] if detalhe else "o processo terminou sem resultado")
        except (OSError, ValueError) as erro:
            if not self._cancelado:
                self._erro = erro
        finally:
            self.exploracao_completa = True
            self._pronto = True
            self._fim.set()

    def done(self):
        return self._pronto

    def running(self):
        return not self._pronto and not self._cancelado

    def result(self, timeout=None):
        """Como Future.result: espera, e uma busca cancelada lança CancelledError."""
        if not self._fim.wait(timeout):
            raise TimeoutError("a busca ainda não terminou")
        if self._cancelado:
            raise CancelledError()
        if self._erro is not None:
            raise self._erro
        return self._resultado

    def cancel(self):
        self._cancelado = True
        if self.processo.poll() is None:
            self.processo.kill()
        return True


class GrafoRegistrado(dict):
    """Grafo que anota, na ordem, cada casa cujos vizinhos o algoritmo consulta.

    Todos os algoritmos de roteamento.py leem grafo[u] ao expandir u, então
    essa leitura marca a casa como examinada. Só a primeira vez conta.
    """

    def __init__(self, grafo):
        super().__init__(grafo)
        self.ordem = {}

    def __getitem__(self, vertice):
        self.ordem.setdefault(vertice, None)
        return dict.__getitem__(self, vertice)


def calcular_rota(grade, origem, destino, algoritmo="dijkstra", cancelar=None, progresso=None,
                  explorar=False):
    """Função sem Tk: construção do grafo fica fora do tempo de busca exibido.

    Com explorar=True, devolve também a ordem das casas examinadas; o registro
    acrescenta um pequeno custo ao tempo medido.
    """
    busca = ALGORITMOS[algoritmo][1]
    grafo = grafo_da_grade(grade)
    if explorar:
        grafo = GrafoRegistrado(grafo)
    inicio = perf_counter()
    if algoritmo == "forca_bruta":
        custo, caminho = busca(grafo, origem, destino, cancelar, progresso)
    else:
        custo, caminho = busca(grafo, origem, destino, cancelar)
    tempo = perf_counter() - inicio
    if explorar:
        return custo, caminho, tempo, list(grafo.ordem)
    return custo, caminho, tempo


def cantos_da_rota(rota):
    """Mantém só as casas onde a rota muda de direção (e as pontas).

    Trechos retos viram um segmento: o Tk desenha linhas grossas em tempo que
    cresce rápido com o número de pontos, e rotas longas travariam a janela.
    """
    if len(rota) < 3:
        return list(rota)
    cantos = [rota[0]]
    for anterior, atual, proxima in zip(rota, rota[1:], rota[2:]):
        if (atual[0] - anterior[0], atual[1] - anterior[1]) != (proxima[0] - atual[0], proxima[1] - atual[1]):
            cantos.append(atual)
    cantos.append(rota[-1])
    return cantos


def ordem_no_catalogo(caminho):
    """Ordem numérica: teste2 antes de teste10."""
    numeros = tuple(int(x) for x in re.findall(r"\d+", caminho.stem))
    return (numeros if caminho.stem.startswith(("teste", "n")) else (), caminho.name)


def duracao_exploracao(casas, velocidade="1×"):
    """Tempo da animação da exploração: até 6 s em 1×, proporcional às casas."""
    if velocidade == "Instantânea":
        return 0.0
    fator = {"1×": 1, "2×": 2, "4×": 4}[velocidade]
    return min(6.0, max(.8, casas * .03)) / fator


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


def regiao_jogavel(grade, margem=1):
    """Retângulo (linha0, coluna0, linha1, coluna1) que contém todas as casas livres.

    Mapas com bordas bloqueadas ocupam só parte da grade; ajustar a visão a esta
    região evita mostrar uma grande área bloqueada. As bordas são exclusivas.
    """
    linhas = [r for r, linha in enumerate(grade) if "." in linha]
    if not linhas:
        return 0, 0, len(grade), len(grade[0])
    c0 = min(linha.find(".") for linha in grade if "." in linha)
    c1 = max(linha.rfind(".") for linha in grade)
    return (max(0, linhas[0] - margem), max(0, c0 - margem),
            min(len(grade), linhas[-1] + 1 + margem), min(len(grade[0]), c1 + 1 + margem))


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
        self.region = None
        self.pending_fit = False
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.search_future = self.search_job = None
        self.search_cancel = None
        self.search_started = self.search_progress = None
        self.map_image = None
        self.zoom = 1.0
        self.world_size = None
        self.tiles = {}
        self.tile_job = None
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
        self.algorithm_info = tk.StringVar(value=DESCRICOES["dijkstra"])
        self.status = tk.StringVar(value="Marque um destino no tabuleiro.")
        self.distance = tk.StringVar(value="—")
        self.progress = tk.StringVar(value="0 movimentos realizados")
        self.destination = tk.StringVar(value="Nenhum destino selecionado")
        self.hint = tk.StringVar(value="Clique em uma casa livre para marcar o destino.")
        self.map_name = tk.StringVar(value="Mini 12 × 18 · Tabuleiro didático")
        self.map_density = tk.StringVar(value="19,0% bloqueadas")
        self.map_info = tk.StringVar(value="12 × 18 · 175 casas livres · 41 obstáculos")
        self.search_time = tk.StringVar(value="Busca: —")
        self.search_details = tk.StringVar(value="")
        self.zoom_label = tk.StringVar(value="Visão geral")
        self.speed = tk.StringVar(value="1×")
        self.follow = tk.BooleanVar(value=False)
        self.show_exploration = tk.BooleanVar(value=False)
        self.explored = set()
        self.exploration_order = []
        self.exploration_index = 0
        self.exploration_job = None
        self.exploring = False
        self.after_exploration = None
        self.live_search = None
        self.attempt_drawn = None
        self.attempt_clock = 0.0
        self.exploration_front = []
        self.map_files = {p.name: p
            for pasta in (DATASET_DIR.parent / "testes", DATASET_DIR.parent / "didaticos", DATASET_DIR)
            for p in sorted(pasta.glob("*.map"), key=ordem_no_catalogo)}
        self.map_choice = tk.StringVar(value="random512-20-0.map")
        self.endpoints = tk.StringVar(value="Origem: linha 3, coluna 3")
        self._build_ui()
        self.set_editing(False)
        self.update_map_info()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _rounded_style(self, style):
        """Fundos arredondados (imagens esticadas pelo ttk), no estilo shadcn/ui."""
        C = COLORS
        self._imagens = {}

        def imagem(nome, raio, cor, contorno):
            self._imagens[nome] = tk.PhotoImage(
                master=self.root, data=png_arredondado(raio, cor, contorno))
            return self._imagens[nome]

        def elemento(nome, raio, normal, *estados, contorno=None):
            """estados: (estado, cor, contorno).

            Sem padding, a borda esticável não aumenta o botão; o espaçamento
            interno vem só do padding de cada estilo.
            """
            if nome in style.element_names():
                return
            mapa = [(estado, imagem(f"{nome}-{i}", raio, cor, borda))
                    for i, (estado, cor, borda) in enumerate(estados)]
            style.element_create(nome, "image", imagem(nome, raio, normal, contorno), *mapa,
                                 border=raio + 2, sticky="nsew", padding=0,
                                 width=2 * raio + 4, height=2 * raio + 4)

        # Botões: "outline" (borda fina), "secondary" (cinza) e "primary" (claro).
        elemento("Outline.bg", 6, C["bg"], ("pressed", C["secondary"], C["line"]),
                 ("active", C["accent"], C["line"]), contorno=C["line"])
        elemento("Secondary.bg", 6, C["secondary"], ("disabled", C["accent"], C["accent"]),
                 ("pressed", C["ring"], C["ring"]), ("active", C["secondary_hover"], C["secondary_hover"]))
        elemento("Primary.bg", 6, C["primary"], ("disabled", C["secondary"], C["secondary"]),
                 ("pressed", "#d4d4d8", "#d4d4d8"), ("active", C["primary_hover"], C["primary_hover"]))
        # Abas: lista cinza com a opção ativa na cor do fundo, como TabsList/TabsTrigger.
        elemento("Aba.bg", 5, C["secondary"], ("selected", C["bg"], C["bg"]))
        for nome_estilo, fundo in (("TButton", "Outline.bg"), ("Zoom.TButton", "Outline.bg"),
                                   ("Lateral.TButton", "Secondary.bg"),
                                   ("Play.TButton", "Primary.bg")):
            style.layout(nome_estilo, [(fundo, {"sticky": "nsew", "children": [
                ("Button.padding", {"sticky": "nsew", "children": [
                    ("Button.label", {"sticky": "nsew"})]})]})])
        style.layout("Segmento.Toolbutton", [("Aba.bg", {"sticky": "nsew", "children": [
            ("Toolbutton.padding", {"sticky": "nsew", "children": [
                ("Toolbutton.label", {"sticky": "nsew"})]})]})])
        # Interruptor (Switch): trilho amarelo quando ligado, como a cor da exploração.
        if "Switch.indicator" not in style.element_names():
            desligado = tk.PhotoImage(master=self.root, data=png_interruptor(C["ring"], C["ink"], False))
            ligado = tk.PhotoImage(master=self.root, data=png_interruptor(C["explored"], C["primary_fg"], True))
            self._imagens["switch-off"], self._imagens["switch-on"] = desligado, ligado
            style.element_create("Switch.indicator", "image", desligado, ("selected", ligado))
        style.layout("Switch.TCheckbutton", [("Checkbutton.padding", {"sticky": "nsew", "children": [
            ("Switch.indicator", {"side": "left", "sticky": ""}),
            ("Checkbutton.label", {"side": "left", "sticky": "w"})]})])
        style.configure("Switch.TCheckbutton", background=C["panel"], foreground=C["ink"],
                        font=("Segoe UI", 9), padding=(0, 3))
        style.map("Switch.TCheckbutton", background=[("active", C["panel"])],
                  foreground=[("disabled", C["muted"])])
        # Cartões com borda fina e cantos de 12 px; lista de abas com 8 px.
        elemento("Cartao.bg", 12, C["card"], contorno=C["line"])
        elemento("Trilho.bg", 8, C["secondary"])
        elemento("Badge.bg", 6, C["secondary"])
        elemento("Campo.bg", 6, C["bg"], ("focus", C["bg"], C["ring"]), contorno=C["line"])
        for estilo, fundo in (("Cartao.TFrame", "Cartao.bg"), ("Trilho.TFrame", "Trilho.bg"),
                              ("Painel.TFrame", "Cartao.bg"), ("Tabuleiro.TFrame", "Cartao.bg")):
            style.layout(estilo, [(fundo, {"sticky": "nsew"})])
        style.layout("Chip.TLabel", [("Badge.bg", {"sticky": "nsew", "children": [
            ("Label.padding", {"sticky": "nsew", "children": [("Label.label", {"sticky": "nsew"})]})]})])
        style.configure("Chip.TLabel", foreground=C["ink"], background=C["card"],
                        font=("Segoe UI Semibold", 9), padding=(8, 2))
        # Campo de seleção com borda fina; a seta fica dentro do mesmo contorno.
        style.layout("TCombobox", [("Campo.bg", {"sticky": "nsew", "children": [
            ("Combobox.downarrow", {"side": "right", "sticky": "ns"}),
            ("Combobox.padding", {"expand": "1", "sticky": "nsew", "children": [
                ("Combobox.textarea", {"sticky": "nsew"})]})]})])
        style.configure("TCombobox", arrowsize=12, padding=(10, 7))
        # O clam troca o fundo em hover, clique e desabilitado; nos cantos transparentes
        # isso apareceria como pontas claras. Cada estilo mantém o fundo do que está atrás.
        for estilo in ("TButton", "Zoom.TButton", "Lateral.TButton", "Play.TButton"):
            style.configure(estilo, background=C["bg"])
            style.map(estilo, background=[(e, C["bg"]) for e in
                                          ("disabled", "pressed", "active", "selected")])
        style.configure("Segmento.Toolbutton", background=C["secondary"])
        style.map("Segmento.Toolbutton", background=[(e, C["secondary"]) for e in
                                                      ("disabled", "pressed", "active", "selected")])

    def _build_ui(self):
        root = self.root
        root.title("Rota mínima — Mapas Random")
        root.configure(bg=COLORS["bg"])
        # Ocupa quase toda a tela: o tabuleiro recebe o espaço que sobra dos controles.
        width = max(920, root.winfo_screenwidth() - 60)
        height = max(660, root.winfo_screenheight() - 110)
        root.geometry(f"{width}x{height}+20+10")
        root.minsize(920, 660)
        root.option_add("*Font", ("Segoe UI", 10))
        for opcao, valor in (("background", COLORS["bg"]), ("foreground", COLORS["ink"]),
                             ("selectBackground", COLORS["secondary"]),
                             ("selectForeground", COLORS["ink"])):
            root.option_add(f"*TCombobox*Listbox.{opcao}", valor)
        C = COLORS
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure(".", background=C["bg"], foreground=C["ink"], bordercolor=C["line"],
                        lightcolor=C["line"], darkcolor=C["line"], troughcolor=C["bg"],
                        focuscolor=C["ring"], selectbackground=C["secondary"])
        # Botões compactos (32–36 px de altura), texto de 9 pt com peso médio, como no shadcn.
        fonte = ("Segoe UI Semibold", 9)
        style.configure("TButton", padding=(14, 7), font=fonte, foreground=C["ink"], anchor="center")
        style.map("TButton", foreground=[("disabled", C["muted"])])
        style.configure("Zoom.TButton", padding=(12, 6), font=fonte)
        style.configure("Lateral.TButton", padding=(14, 8), font=fonte)
        style.configure("Play.TButton", foreground=C["primary_fg"], padding=(14, 9),
                        font=("Segoe UI Semibold", 10))
        style.map("Play.TButton", foreground=[("disabled", C["muted"])])
        style.configure("Segmento.Toolbutton", foreground=C["muted"], padding=(14, 6),
                        font=fonte, anchor="center")
        style.map("Segmento.Toolbutton", foreground=[("selected", C["ink"]), ("active", C["ink"])])
        style.configure("Mode.TRadiobutton", background=C["bg"], foreground=C["ink"],
                        padding=(6, 4), font=("Segoe UI", 9),
                        indicatorbackground=C["bg"], indicatorforeground=C["ink"],
                        bordercolor=C["ring"])
        style.map("Mode.TRadiobutton", foreground=[("disabled", "#52525b")],
                  background=[("active", C["bg"])],
                  indicatorbackground=[("disabled", C["bg"]), ("selected", C["bg"])])
        style.configure("Side.TCheckbutton", background=C["panel"], foreground=C["muted"],
                        font=("Segoe UI", 9), indicatorbackground=C["bg"],
                        indicatorforeground=C["ink"])
        style.map("Side.TCheckbutton", background=[("active", C["panel"])])
        style.configure("TCombobox", fieldbackground=C["bg"], background=C["bg"],
                        foreground=C["ink"], arrowcolor=C["muted"],
                        bordercolor=C["bg"], selectbackground=C["bg"],
                        selectforeground=C["ink"], font=("Segoe UI", 9))
        style.map("TCombobox", fieldbackground=[("readonly", C["bg"])],
                  foreground=[("readonly", C["ink"])], background=[("active", C["bg"])])
        style.configure("TScrollbar", background=C["secondary"], troughcolor=C["bg"],
                        arrowcolor=C["muted"], bordercolor=C["bg"], gripcount=0, arrowsize=11)
        style.map("TScrollbar", background=[("active", C["ring"])])
        style.configure("TSeparator", background=C["line"])
        self._rounded_style(style)

        # Barra superior: título à esquerda, catálogo de mapas à direita.
        head = tk.Frame(root, bg=C["bg"])
        head.pack(fill="x", padx=24, pady=(14, 10))
        titulo = tk.Frame(head, bg=C["bg"])
        titulo.pack(side="left")
        tk.Label(titulo, text="Rota mínima", bg=C["bg"], fg=C["ink"],
                 font=("Segoe UI Semibold", 16)).pack(anchor="w")
        tk.Label(titulo, text="Caminhos mínimos em grades · 4 direções, custo 1",
                 bg=C["bg"], fg=C["muted"], font=("Segoe UI", 9)).pack(anchor="w")
        arquivos = tk.Frame(head, bg=C["bg"])
        arquivos.pack(side="right")
        self.map_combo = ttk.Combobox(arquivos, textvariable=self.map_choice,
                     values=tuple(self.map_files), width=24, state="readonly")
        self.map_combo.pack(side="left", padx=(0, 8))
        for texto, acao in [("Carregar mapa", self.load_selected),
                            ("Mini 12 × 18", self.load_example)]:
            ttk.Button(arquivos, text=texto, command=acao).pack(side="left", padx=(0, 6))

        # Mostra o mapa efetivamente carregado, antes da escolha do algoritmo.
        self.map_card = ttk.Frame(root, style="Cartao.TFrame", padding=(16, 9))
        self.map_card.pack(fill="x", padx=24, pady=(0, 12))
        self.map_card.columnconfigure(1, weight=1)
        self.map_name_label = tk.Label(self.map_card, textvariable=self.map_name,
            bg=C["card"], fg=C["ink"], font=("Segoe UI Semibold", 11),
            anchor="w", justify="left", wraplength=420)
        self.map_name_label.grid(row=0, column=0, sticky="w")
        self.map_info_label = tk.Label(self.map_card, textvariable=self.map_info,
            bg=C["card"], fg=C["muted"], font=("Segoe UI", 9), anchor="w",
            justify="left", wraplength=500)
        self.map_info_label.grid(row=0, column=1, sticky="ew", padx=(14, 12))
        ttk.Label(self.map_card, textvariable=self.map_density,
                  style="Chip.TLabel").grid(row=0, column=2, sticky="e")

        # Abas: uma linha de opções curtas e a descrição da escolhida.
        self.algorithm_section = tk.Frame(root, bg=C["bg"])
        self.algorithm_section.pack(fill="x", padx=24, pady=(0, 12))
        tk.Label(self.algorithm_section, text="Algoritmo", bg=C["bg"], fg=C["muted"],
                 font=("Segoe UI Semibold", 9)).grid(row=0, column=0, sticky="w", padx=(0, 12))
        trilho = ttk.Frame(self.algorithm_section, style="Trilho.TFrame", padding=3)
        trilho.grid(row=0, column=1, sticky="w")
        self.algorithm_options = {}
        for i, (valor, _) in enumerate(ALGORITMOS.items()):
            option = ttk.Radiobutton(trilho, text=ROTULOS_CURTOS[valor],
                value=valor, variable=self.algorithm, command=self.algorithm_changed,
                style="Segmento.Toolbutton")
            option.grid(row=0, column=i)
            self.algorithm_options[valor] = option
        tk.Label(self.algorithm_section, textvariable=self.algorithm_info, bg=C["bg"],
                 fg=C["muted"], font=("Segoe UI", 9), anchor="w").grid(
                     row=1, column=1, sticky="w", padx=2, pady=(5, 0))

        body = tk.Frame(root, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=24, pady=(0, 14))
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)
        left = tk.Frame(body, bg=C["bg"])
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 16))

        tools = tk.Frame(left, bg=C["bg"])
        tools.pack(fill="x", pady=(0, 6))
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

        zoom_tools = tk.Frame(left, bg=C["bg"])
        zoom_tools.pack(fill="x", pady=(0, 8))
        for texto, acao in [("−", lambda: self.change_zoom(1 / 1.5)),
                            ("+", lambda: self.change_zoom(1.5)), ("Ajustar mapa", self.fit_map),
                            ("Origem", lambda: self.focus_cell(self.start)),
                            ("Destino", lambda: self.focus_cell(self.target))]:
            largura = 2 if texto in ("−", "+") else None
            ttk.Button(zoom_tools, text=texto, command=acao, style="Zoom.TButton",
                       width=largura).pack(side="left", padx=(0, 6))
        tk.Label(zoom_tools, textvariable=self.zoom_label, bg=C["bg"],
                 fg=C["muted"], font=("Segoe UI", 9)).pack(side="left", padx=6)
        # O canvas fica dentro de um cartão com borda fina e cantos arredondados.
        board_area = ttk.Frame(left, style="Tabuleiro.TFrame", padding=8)
        board_area.pack(fill="both", expand=True)
        board_area.columnconfigure(0, weight=1)
        board_area.rowconfigure(0, weight=1)
        self.canvas = tk.Canvas(board_area, bg=C["board"], highlightthickness=0,
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

        rodape = tk.Frame(left, bg=C["bg"])
        rodape.pack(fill="x", pady=(8, 0))
        legend = tk.Frame(rodape, bg=C["bg"])
        legend.pack(side="right")
        for text, color in [("●  Personagem", C["blue"]), ("◎  Destino", C["target"]),
                            ("━  Rota", C["path"]), ("■  Casa livre", "#71717a")]:
            tk.Label(legend, text=text, bg=C["bg"], fg=color,
                     font=("Segoe UI", 9)).pack(side="left", padx=(12, 0))
        self.hint_label = tk.Label(rodape, textvariable=self.hint, bg=C["bg"],
                                  fg=C["muted"], anchor="w", justify="left",
                                  font=("Segoe UI", 9))
        self.hint_label.pack(side="left", fill="x", expand=True)

        # Painel lateral: cartão com borda; o conteúdo rola dentro dele em janelas baixas.
        P = C["panel"]
        painel = ttk.Frame(body, style="Painel.TFrame", padding=(4, 8))
        painel.grid(row=0, column=1, sticky="ns")
        painel.rowconfigure(0, weight=1)
        self.side_view = tk.Canvas(painel, bg=P, width=260, highlightthickness=0)
        self.side_view.grid(row=0, column=0, sticky="ns")
        side_scroll = ttk.Scrollbar(painel, orient="vertical", command=self.side_view.yview)
        side_scroll.grid(row=0, column=1, sticky="ns")
        self.side_view.configure(yscrollcommand=side_scroll.set)
        side = tk.Frame(self.side_view, bg=P, width=260, padx=16, pady=12)
        self.side = side
        self.side_window = self.side_view.create_window(0, 0, window=side, anchor="nw")
        side.columnconfigure(0, weight=1)
        tk.Label(side, text="Sua rota", bg=P, fg=C["muted"],
                 font=("Segoe UI Semibold", 9)).grid(row=0, column=0, sticky="w")
        tk.Label(side, textvariable=self.destination, wraplength=220, justify="left",
                 bg=P, fg=C["ink"], font=("Segoe UI", 11)).grid(
                     row=1, column=0, sticky="w", pady=(6, 16))
        self.play_button = ttk.Button(side, text="▶  Play", style="Play.TButton",
                                      command=self.play, state="disabled")
        self.play_button.grid(row=2, column=0, sticky="ew")
        percurso = tk.Frame(side, bg=P)
        percurso.grid(row=3, column=0, sticky="ew", pady=(8, 18))
        ttk.Button(percurso, text="Reiniciar percurso", command=self.restart,
                   style="Lateral.TButton").pack(fill="x")
        ttk.Button(percurso, text="Concluir animação", command=self.finish_route,
                   style="Lateral.TButton").pack(fill="x", pady=(6, 0))
        velocidades = tk.Frame(percurso, bg=P)
        velocidades.pack(fill="x", pady=(12, 0))
        tk.Label(velocidades, text="Velocidade", bg=P, fg=C["muted"],
                 font=("Segoe UI", 9)).pack(side="left")
        ttk.Combobox(velocidades, textvariable=self.speed,
                     values=("1×", "2×", "4×", "Instantânea"), state="readonly", width=11).pack(side="right")
        tk.Label(percurso, text="1×: percurso completo em até 8 s.\nA velocidade vale no próximo Play.",
                 bg=P, fg=C["muted"], font=("Segoe UI", 8), justify="left").pack(anchor="w", pady=(6, 0))
        ttk.Checkbutton(percurso, text="Mostrar exploração", variable=self.show_exploration,
                        style="Switch.TCheckbutton").pack(anchor="w", pady=(10, 0))
        tk.Label(percurso, text="Pinta de amarelo cada casa que o algoritmo examina, "
                 "na ordem, antes de mostrar a rota.", bg=P, fg=C["muted"], font=("Segoe UI", 8),
                 justify="left", anchor="w", wraplength=180).pack(anchor="w", padx=(42, 0))
        ttk.Checkbutton(percurso, text="Seguir personagem no zoom", variable=self.follow,
                        style="Switch.TCheckbutton").pack(anchor="w", pady=(6, 0))
        ttk.Separator(side).grid(row=4, column=0, sticky="ew")
        tk.Label(side, text="Menor caminho", bg=P, fg=C["muted"],
                 font=("Segoe UI Semibold", 9)).grid(row=5, column=0, sticky="w", pady=(16, 0))
        self.distance_label = tk.Label(side, textvariable=self.distance, bg=P,
                                       fg=C["ink"], font=("Segoe UI", 40, "bold"))
        self.distance_label.grid(row=6, column=0, sticky="w")
        tk.Label(side, text="movimentos", bg=P, fg=C["muted"], font=("Segoe UI", 9)).grid(
            row=7, column=0, sticky="w")
        metricas = tk.Frame(side, bg=P)
        metricas.grid(row=8, column=0, sticky="w", pady=(12, 14))
        for variavel in (self.endpoints, self.progress, self.search_time, self.search_details):
            tk.Label(metricas, textvariable=variavel, bg=P, fg=C["muted"],
                     font=("Segoe UI", 9)).pack(anchor="w")
        self.status_label = tk.Label(side, textvariable=self.status, wraplength=220,
                                     justify="left", bg=P, fg=C["ink"],
                                     font=("Segoe UI", 10), height=4, anchor="nw")
        self.status_label.grid(row=9, column=0, sticky="nw")
        side.rowconfigure(10, weight=1)
        tk.Label(side, text="Roda: zoom · Botão direito: mover\nEspaço: Play / Pausar · Ctrl+0: ajustar",
                 bg=P, fg=C["muted"], justify="left", font=("Segoe UI", 8)).grid(
                     row=11, column=0, sticky="w", pady=(16, 10))
        self.side_view.bind("<Configure>", self.resize_sidebar)
        side.bind("<Configure>", self.update_sidebar)
        root.bind("<Configure>", self.resize_map_info, add="+")

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

    def cancel_search(self):
        self.search_started = self.search_progress = None
        self.canvas.delete("tentativa")
        # Future.cancel() sozinho não interrompe uma tarefa já em execução.
        if self.search_cancel is not None:
            self.search_cancel.set()
            self.search_cancel = None
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

    def cancel_exploration(self):
        if self.exploration_job is not None:
            self.root.after_cancel(self.exploration_job)
            self.exploration_job = None
        self.exploring = False
        self.after_exploration = None
        self.live_search = None

    def clear_route(self):
        self.cancel_search()
        self.cancel_animation()
        self.cancel_exploration()
        if self.explored:
            self.explored = set()
            self.exploration_order = []
            self.exploration_front = []
            self.redraw_map()
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
        self.search_details.set("")
        self.status_label.configure(fg=COLORS["ink"])
        self.play_button.configure(text="▶  Play", state="normal" if self.target else "disabled")

    def resize_map_info(self, event):
        if event.widget is not self.root:
            return
        # Nome e informações dividem a mesma linha do cartão do mapa.
        name_width = max(300, (event.width - 260) // 3)
        info_width = max(300, event.width - name_width - 260)
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

    def algorithm_changed(self):
        """Repete a entrada desde a mesma origem ao trocar a implementação."""
        self.restart()
        nome = ALGORITMOS[self.algorithm.get()][0]
        self.algorithm_info.set(DESCRICOES[self.algorithm.get()])
        self.status.set(f"{nome} selecionado. Aperte Play para buscar desde a origem."
                        if self.target is not None else f"{nome} selecionado. Marque um destino.")

    def play(self):
        if self.search_future is not None:
            self.stop_search()
            return
        if self.exploring:
            self.finish_exploration()
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
        # Uma nova busca sempre reinicia o percurso: o personagem volta à origem.
        self.player = self.start
        self.visual_player = tuple(map(float, self.start))
        self.clear_route()
        # Uma cópia da entrada impede que edições alterem uma busca em andamento.
        self.draw_overlay()
        grade = self.current_grid()
        algoritmo = self.algorithm.get()
        if self.show_exploration.get():
            self.start_live_search(grade, algoritmo)
            return
        if algoritmo == "forca_bruta":
            self.start_process_search(grade, algoritmo)
            return
        # Mapas grandes e a varredura do livro rodam em segundo plano, canceláveis.
        if self.rows * self.cols > 6000 or algoritmo == "dijkstra_simples":
            self.status.set("Calculando a rota… Reiniciar percurso cancela a busca.")
            self.play_button.configure(state="normal", text="■  Cancelar busca")
            self.search_cancel = Event()
            self.search_started = perf_counter()
            self.search_progress = None
            self.search_future = self.executor.submit(
                calcular_rota, grade, self.player, self.target, algoritmo,
                self.search_cancel.is_set)
            self.search_job = self.root.after(40, self.poll_search)
        else:
            self.apply_result(calcular_rota(grade, self.player, self.target, algoritmo,
                                            explorar=self.show_exploration.get()))

    def start_process_search(self, grade, algoritmo):
        """Força bruta em outro processo: a janela nunca disputa o interpretador com ela.

        Uma única execução, medida, envia o progresso e a rota em teste (laranja).
        Cancelar encerra o processo na hora, mesmo no meio da enumeração.
        """
        self.status.set("Enumerando todas as rotas; em laranja, a que está sendo testada. "
                        "Para testes rápidos, use os mapas 3×3 e 4×4.")
        self.play_button.configure(state="normal", text="■  Cancelar busca")
        self.search_cancel = Event()
        self.search_started = perf_counter()
        busca = BuscaAoVivo(grade, self.player, self.target, algoritmo, explorar=False)
        self.search_future = busca
        self.search_progress = busca.progresso
        self.search_job = self.root.after(40, self.poll_search)

    def start_live_search(self, grade, algoritmo):
        """Busca em outro processo; as casas aparecem em amarelo enquanto ela explora."""
        nome = ALGORITMOS[algoritmo][0]
        self.status.set(f"{nome} explorando ao vivo… O tempo é medido depois, sem registro."
                        + (" Laranja: a rota que ela está testando agora." if algoritmo == "forca_bruta" else ""))
        self.play_button.configure(state="normal", text="■  Cancelar busca")
        self.search_cancel = Event()
        self.search_started = perf_counter()
        busca = BuscaAoVivo(grade, self.player, self.target, algoritmo)
        self.live_search = self.search_future = busca
        self.search_progress = busca.progresso if algoritmo == "forca_bruta" else None
        # A animação começa já; ela nunca mostra uma casa antes de o algoritmo examiná-la.
        self.exploration_order = []
        self.exploration_index = 0
        self.explored = set()
        self.exploration_front = []
        self.after_exploration = None
        self.exploring = True
        self.exploration_clock = perf_counter()
        self.exploration_job = self.root.after(20, self.tick_exploration)
        self.search_job = self.root.after(40, self.poll_search)

    def drain_live(self):
        """Move para a ordem de exploração os lotes que o processo já enviou."""
        if self.live_search is None:
            return
        for _ in range(self.live_search.casas.qsize()):
            try:
                self.exploration_order.extend(self.live_search.casas.get_nowait())
            except Empty:
                break

    def update_search_feedback(self):
        """Exibe atividade sem apresentar o melhor custo parcial como ótimo."""
        if self.search_started is not None:
            decorrido = perf_counter() - self.search_started
            self.search_time.set(f"Decorrido: {decorrido:.1f} s")
            self.play_button.configure(text=f"■  Cancelar · {decorrido:.1f} s")
        self.draw_attempt()
        if self.search_progress is None:
            return
        ultimo = None
        # Lê só o que já estava na fila: se a busca publica tão rápido quanto a
        # janela lê, esvaziar "até acabar" nunca terminaria.
        for _ in range(self.search_progress.qsize()):
            try:
                ultimo = self.search_progress.get_nowait()
            except Empty:
                break
        if ultimo is not None:
            estados, rotas = ultimo
            self.search_details.set(
                f"Estados explorados: {estados:,}\nRotas completas: {rotas:,}".replace(",", "."))

    def current_attempt(self):
        """Rota que a força bruta está testando agora, se houver (vem do processo auxiliar)."""
        busca = self.search_future
        return busca.tentativa if isinstance(busca, BuscaAoVivo) else None

    def draw_attempt(self):
        """Linha laranja da rota em teste, com um ponto na casa da ponta.

        A rota da força bruta pode ter milhares de casas e muda o tempo todo.
        Para não travar a janela: só os cantos, três linhas finas deslocadas em
        vez de uma grossa (o Tk desenha linhas finas muito mais rápido) e, no
        máximo, um redesenho a cada 120 ms, só quando a rota muda.
        """
        cv = self.canvas
        rota = self.current_attempt()
        if not rota or len(rota) < 2:
            cv.delete("tentativa")
            self.attempt_drawn = None
            return
        agora = perf_counter()
        itens = cv.find_withtag("tentativa")
        if len(itens) == 4 and (rota is self.attempt_drawn or agora - self.attempt_clock < .12):
            return
        self.attempt_drawn, self.attempt_clock = rota, agora
        pontos = [xy for casa in cantos_da_rota(rota) for xy in self.center(casa)]
        deslocamentos = ((0, 0), (1, 1), (-1, -1))
        x, y = pontos[-2], pontos[-1]
        raio = max(4, self.cell_size * .22)
        if len(itens) == 4:
            *linhas, ponta = itens
            for linha, (dx, dy) in zip(linhas, deslocamentos):
                cv.coords(linha, *[v + (dx if i % 2 == 0 else dy) for i, v in enumerate(pontos)])
            cv.coords(ponta, x - raio, y - raio, x + raio, y + raio)
            return
        cv.delete("tentativa")
        for dx, dy in deslocamentos:
            cv.create_line(*[v + (dx if i % 2 == 0 else dy) for i, v in enumerate(pontos)],
                           fill=COLORS["attempt"], width=1, tags=("overlay", "tentativa"))
        cv.create_oval(x - raio, y - raio, x + raio, y + raio, fill=COLORS["attempt"],
                       outline=COLORS["board"], width=2, tags=("overlay", "tentativa"))

    def stop_search(self):
        """Cancela pelo botão principal e mantém visível o trabalho já realizado."""
        self.update_search_feedback()
        tempo, detalhes = self.search_time.get(), self.search_details.get()
        self.clear_route()
        self.search_time.set(tempo)
        self.search_details.set(detalhes)
        self.progress.set("Busca interrompida")
        self.status.set("Busca cancelada. Nenhum custo mínimo foi confirmado.")
        self.draw_overlay()

    def poll_search(self):
        """Consulta a tarefa sem esperar por ela na thread da janela."""
        self.search_job = None
        future = self.search_future
        if future is None:
            return
        self.update_search_feedback()
        if not future.done():
            self.search_job = self.root.after(40, self.poll_search)
            return
        # A publicação final pode ocorrer entre a leitura acima e future.done().
        self.update_search_feedback()
        self.search_future = None
        self.canvas.delete("tentativa")
        self.search_cancel = None
        self.search_started = self.search_progress = None
        try:
            resultado = future.result()
        except Exception as erro:
            self.cancel_exploration()
            self.play_button.configure(text="▶  Play", state="normal")
            self.status.set(f"Não foi possível calcular: {erro}")
            return
        if future is self.live_search:
            self.finish_live_search(resultado)
            return
        self.apply_result(resultado)

    def finish_live_search(self, resultado):
        """A busca acabou; a rota aparece quando a exploração terminar de ser pintada."""
        self.drain_live()
        total = len(self.exploration_order)
        detalhes = self.search_details.get()
        self.search_details.set((detalhes + "\n" if detalhes else "")
                                + f"Casas examinadas: {total:,}".replace(",", "."))
        if not self.exploring:
            self.apply_result(resultado)
            return
        self.after_exploration = lambda: self.apply_result(resultado)
        self.play_button.configure(text="⏭  Pular exploração")
        self.search_time.set(f"Busca: {resultado[2] * 1000:.2f} ms")
        self.status.set("Busca concluída. Terminando de mostrar a exploração; Play pula para a rota.")

    def apply_result(self, resultado):
        """Recebe (custo, caminho, tempo) ou, com exploração, também a ordem das casas."""
        cost, self.path, tempo = resultado[:3]
        ordem = resultado[3] if len(resultado) > 3 else None
        self.search_time.set(f"Busca: {tempo * 1000:.2f} ms"
                             + (" · com registro" if ordem is not None else ""))
        self.play_button.configure(state="normal", text="▶  Play")
        if ordem:
            detalhes = self.search_details.get()
            self.search_details.set((detalhes + "\n" if detalhes else "")
                                    + f"Casas examinadas: {len(ordem):,}".replace(",", "."))
            self.start_exploration(ordem, lambda: self.show_route(cost))
            return
        self.show_route(cost)

    def start_exploration(self, ordem, depois):
        """Anima, em amarelo, uma exploração já completa (sem processo auxiliar)."""
        self.exploration_order = ordem
        self.exploration_index = 0
        self.explored = set()
        self.after_exploration = depois
        self.exploring = True
        self.exploration_clock = perf_counter()
        nome = ALGORITMOS[self.algorithm.get()][0]
        self.status.set(f"Exploração de {nome}: casas examinadas, na ordem. Play pula para a rota.")
        self.play_button.configure(text="⏭  Pular exploração")
        if duracao_exploracao(len(ordem), self.speed.get()) == 0:
            self.finish_exploration()
        else:
            self.exploration_job = self.root.after(20, self.tick_exploration)

    def exploration_received(self):
        """Verdadeiro quando já chegaram todas as casas da exploração."""
        busca = self.live_search
        return busca is None or (busca.exploracao_completa and busca.casas.empty())

    def tick_exploration(self):
        self.exploration_job = None
        if not self.exploring:
            return
        self.drain_live()
        recebidas = len(self.exploration_order)
        completa = self.exploration_received()
        # O ritmo usa o total recebido até agora; em Instantânea, mostra tudo o que chegou.
        duracao = duracao_exploracao(recebidas, self.speed.get()) if recebidas else 0
        if duracao == 0:
            alvo = recebidas
        else:
            fracao = (perf_counter() - self.exploration_clock) / duracao
            alvo = min(recebidas, max(self.exploration_index + 1, round(fracao * recebidas)))
        self.paint_explored(self.exploration_order[self.exploration_index:alvo])
        self.exploration_index = alvo
        if completa:
            self.progress.set(f"Explorando: {alvo:,} de {recebidas:,} casas".replace(",", "."))
        else:
            self.progress.set(f"Explorando ao vivo: {alvo:,} casas".replace(",", "."))
        if completa and alvo >= recebidas and self.after_exploration is not None:
            self.finish_exploration()
        else:
            self.exploration_job = self.root.after(20, self.tick_exploration)

    def finish_exploration(self):
        """Pinta o que falta e segue para a rota (só depois de a busca terminar)."""
        if not self.exploring or self.search_future is not None:
            return
        self.drain_live()
        depois = self.after_exploration
        restantes = self.exploration_order[self.exploration_index:]
        self.cancel_exploration()
        self.play_button.configure(text="▶  Play")
        self.exploration_index = len(self.exploration_order)
        if len(restantes) > 2000:
            self.explored.update(restantes)
            self.exploration_front = []
            self.redraw_map()
        else:
            self.paint_explored(restantes)
            self.paint_explored([])
        if depois is not None:
            depois()

    def paint_explored(self, casas):
        """Pinta casas novas em amarelo claro (frente) e assenta o lote anterior."""
        anteriores, self.exploration_front = self.exploration_front, list(casas)
        self._paint_cells(anteriores, COLORS["explored"])
        if casas:
            self.explored.update(casas)
            self._paint_cells(casas, COLORS["explored_front"])

    def _paint_cells(self, casas, cor):
        """Pinta casas nos blocos já desenhados; os demais leem self.explored ao surgir."""
        if not casas or not self.tiles:
            return
        s = self.cell_size
        ox, oy = self.offset
        # O primeiro pixel de cada casa é a linha da grade quando ela aparece.
        recuo = .5 if s >= 6 else -.5
        retangulos = {}
        for r, c in casas:
            x0, x1 = ceil(ox + c * s + recuo), ceil(ox + (c + 1) * s - .5)
            y0, y1 = ceil(oy + r * s + recuo), ceil(oy + (r + 1) * s - .5)
            if x1 <= x0 or y1 <= y0:
                continue
            for i in range(x0 // BLOCO, (x1 - 1) // BLOCO + 1):
                for j in range(y0 // BLOCO, (y1 - 1) // BLOCO + 1):
                    if (i, j) in self.tiles:
                        bx, by = i * BLOCO, j * BLOCO
                        retangulos.setdefault((i, j), set()).add(
                            (max(x0, bx) - bx, max(y0, by) - by,
                             min(x1, bx + BLOCO) - bx, min(y1, by + BLOCO) - by))
        for chave, lista in retangulos.items():
            imagem = self.tiles[chave][0]
            for retangulo in lista:
                imagem.put(cor, to=retangulo)

    def show_route(self, cost):
        """Mostra o custo e anima o personagem pela rota."""
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
            self.follow_camera()

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
        if self.search_future is not None:
            return
        if self.exploring:
            self.finish_exploration()
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

    def load_example(self):
        """Carrega o tabuleiro didático fixo do botão Mini 12 × 18."""
        self.clear_route()
        self.rows, self.cols = ROWS, COLS
        self.loaded_map = None
        self.map_edited = False
        self.walls = default_walls()
        self.region = None
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
        self.map_edited = False
        self.rows, self.cols = mapa.linhas, mapa.colunas
        self.walls = mapa.paredes
        self.region = regiao_jogavel(mapa.grade)
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
        self.mode_changed()
        self.update_map_info()
        # Enquadra a região com casas livres; bordas bloqueadas ficam de fora.
        self.fit_map()

    def load_selected(self):
        try:
            arquivo = self.map_files[self.map_choice.get()]
            # Datasets com manifesto definem origem e destino; os demais usam os cantos.
            self.load_board(ler_mapa(arquivo), *(pontos_definidos(arquivo) or ()))
        except (OSError, ValueError, UnicodeError, KeyError) as erro:
            messagebox.showerror("Mapa não carregado", str(erro), parent=self.root)

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
                                     outline="#9cc3ff", width=2, tags="hover")

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
        self.draw_board(desenhar_mapa=False)
        left = self.offset[0] + cx * self.cell_size - anchor[0]
        top = self.offset[1] + cy * self.cell_size - anchor[1]
        cv.xview_moveto(max(0, left) / self.world_size[0])
        cv.yview_moveto(max(0, top) / self.world_size[1])
        self.draw_background()

    def fit_map(self):
        """Mostra a região com casas livres o maior possível; sem região, a grade inteira."""
        cv = self.canvas
        self.zoom = 1.0
        cv.xview_moveto(0)
        cv.yview_moveto(0)
        width, height = cv.winfo_width(), cv.winfo_height()
        if width < 20 or height < 20:
            # A janela ainda não tem tamanho; o ajuste acontece no primeiro desenho.
            self.pending_fit = True
            return "break"
        self.pending_fit = False
        self.draw_board(desenhar_mapa=False)
        if self.region is None:
            self.draw_background()
            return "break"
        r0, c0, r1, c1 = self.region
        celula = min((width - 32) / (c1 - c0), (height - 32) / (r1 - r0))
        zoom = min(celula / self.fit_size, max(1.0, 64 / self.fit_size))
        if zoom < 1.05:
            self.draw_background()
            return "break"
        self.zoom = zoom
        self.draw_board(desenhar_mapa=False)
        s, (ox, oy) = self.cell_size, self.offset
        x = ox + (c0 + c1) / 2 * s
        y = oy + (r0 + r1) / 2 * s
        cv.xview_moveto(max(0, x - width / 2) / self.world_size[0])
        cv.yview_moveto(max(0, y - height / 2) / self.world_size[1])
        self.draw_background()
        return "break"

    def follow_camera(self):
        """Centraliza a visão no personagem. Rolar só move blocos prontos; os novos
        são desenhados aos poucos, sem travar a animação."""
        cv = self.canvas
        x, y = self.center(self.visual_player)
        w, h = cv.winfo_width(), cv.winfo_height()
        cv.xview_moveto(max(0, x - w / 2) / self.world_size[0])
        cv.yview_moveto(max(0, y - h / 2) / self.world_size[1])
        self.ensure_tiles(limite=2)

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

    def draw_board(self, desenhar_mapa=True):
        """Recalcula a projeção apenas em mudanças do mapa, tamanho ou zoom."""
        cv = self.canvas
        width, height = cv.winfo_width(), cv.winfo_height()
        if width < 20 or height < 20:
            return
        # A legenda ocupa o lado direito do rodapé; a dica quebra linha antes dela.
        self.hint_label.configure(wraplength=max(180, width - 420))
        self.fit_size = max(.01, min((width - 32) / self.cols, (height - 32) / self.rows))
        self.zoom = max(1.0, min(self.zoom, max(1.0, 64 / self.fit_size)))
        self.cell_size = self.fit_size * self.zoom
        mw, mh = self.cell_size * self.cols, self.cell_size * self.rows
        self.offset = (max(16, (width - mw) / 2), max(16, (height - mh) / 2))
        self.world_size = (max(width, ceil(mw + 32)), max(height, ceil(mh + 32)))
        cv.configure(scrollregion=(0, 0, *self.world_size))
        self.zoom_label.set("Visão geral" if self.zoom == 1 else f"{self.zoom:.1f}×")
        cv.delete("all")
        self.tiles = {}
        self.player_item = self.player_text = None
        if desenhar_mapa:
            self.draw_background()
        self.draw_overlay()
        if self.pending_fit:
            self.pending_fit = False
            self.root.after_idle(self.fit_map)

    def redraw_map(self):
        """Descarta os blocos (mudou parede ou exploração) e desenha a visão de novo."""
        for _, item in self.tiles.values():
            self.canvas.delete(item)
        self.tiles = {}
        self.draw_background()

    def draw_background(self):
        """Garante os blocos da região visível e os rótulos de linha e coluna."""
        cv, s = self.canvas, self.cell_size
        if cv.winfo_width() < 20 or cv.winfo_height() < 20:
            return
        if self.world_size is None:
            # Ainda sem projeção (a janela acabou de ganhar tamanho): desenho completo.
            self.draw_board()
            return
        self.map_image = None
        cv.delete("rotulo")
        if s >= 6:
            ox, oy = self.offset
            vx, vy = cv.canvasx(0), cv.canvasy(0)
            vw, vh = cv.winfo_width(), cv.winfo_height()
            c0, r0 = max(0, floor((vx - ox) / s)), max(0, floor((vy - oy) / s))
            c1 = min(self.cols, ceil((vx + vw - ox) / s))
            r1 = min(self.rows, ceil((vy + vh - oy) / s))
            intervalo = max(1, ceil(22 / s))
            for c in range(c0 - c0 % intervalo, c1, intervalo):
                cv.create_text(ox + (c + .5) * s, oy - 8, text=str(c + 1), fill="#6f809c",
                               font=("Segoe UI", 8), tags=("map", "rotulo"))
            for r in range(r0 - r0 % intervalo, r1, intervalo):
                cv.create_text(ox - 9, oy + (r + .5) * s, text=str(r + 1), fill="#6f809c",
                               font=("Segoe UI", 8), tags=("map", "rotulo"))
        self.ensure_tiles()

    def ensure_tiles(self, limite=None):
        """Desenha os blocos visíveis que faltam e descarta os distantes.

        Com `limite`, desenha no máximo esse número agora e agenda o resto, para
        que a câmera em movimento não espere por blocos novos.
        """
        cv = self.canvas
        vx, vy = cv.canvasx(0), cv.canvasy(0)
        vw, vh = cv.winfo_width(), cv.winfo_height()
        mw, mh = self.world_size
        i0, j0 = max(0, int(vx // BLOCO)), max(0, int(vy // BLOCO))
        i1 = min((mw - 1) // BLOCO, int((vx + vw) // BLOCO))
        j1 = min((mh - 1) // BLOCO, int((vy + vh) // BLOCO))
        # Descarta blocos a mais de dois blocos da visão para limitar a memória.
        for chave in [k for k in self.tiles if not (i0 - 2 <= k[0] <= i1 + 2 and j0 - 2 <= k[1] <= j1 + 2)]:
            cv.delete(self.tiles.pop(chave)[1])
        # Primeiro os visíveis, do centro para fora; depois uma margem de um bloco.
        ci, cj = (i0 + i1) / 2, (j0 + j1) / 2
        visiveis = sorted(((i, j) for i in range(i0, i1 + 1) for j in range(j0, j1 + 1)),
                          key=lambda k: (k[0] - ci) ** 2 + (k[1] - cj) ** 2)
        margem = [(i, j) for i in range(max(0, i0 - 1), min((mw - 1) // BLOCO, i1 + 1) + 1)
                  for j in range(max(0, j0 - 1), min((mh - 1) // BLOCO, j1 + 1) + 1)
                  if not (i0 <= i <= i1 and j0 <= j <= j1)]
        pendentes = [k for k in visiveis + margem if k not in self.tiles]
        desenhar = pendentes if limite is None else pendentes[:limite]
        for chave in desenhar:
            self.render_tile(*chave)
        if len(desenhar) < len(pendentes) and self.tile_job is None:
            self.tile_job = self.root.after(15, self._continue_tiles)

    def _continue_tiles(self):
        self.tile_job = None
        if self.canvas.winfo_exists():
            self.ensure_tiles(limite=2)

    def render_tile(self, i, j):
        """Rasteriza um bloco BLOCO × BLOCO: casas, paredes, grade e exploração."""
        cv, s = self.canvas, self.cell_size
        ox, oy = self.offset
        x0, y0 = i * BLOCO, j * BLOCO
        largura = min(BLOCO, self.world_size[0] - x0)
        altura = min(BLOCO, self.world_size[1] - y0)
        if largura <= 0 or altura <= 0:
            return
        grade, topo = s >= 6, s >= 12
        cor = {nome: bytes.fromhex(COLORS[nome][1:]) for nome in
               ("board", "cell", "wall", "grid", "explored", "explored_grid", "wall_top")}

        def eixo(inicio, tamanho, deslocamento, limite):
            """Para cada pixel: (índice da casa ou None, é linha da grade, faixa do topo)."""
            saida = []
            for p in range(inicio, inicio + tamanho):
                pos = p + .5 - deslocamento
                k = floor(pos / s)
                if not 0 <= k < limite:
                    saida.append((None, False, False))
                    continue
                dentro = pos - k * s
                saida.append((k, grade and dentro < 1, topo and 2 <= dentro < 4))
            return saida

        colunas = eixo(x0, largura, ox, self.cols)
        linhas = eixo(y0, altura, oy, self.rows)
        # Faixa horizontal do realce do topo das paredes (como no desenho anterior).
        faixa = [topo and k is not None and 2 <= (x0 + n + .5 - ox) - k * s < s - 2
                 for n, (k, _, _) in enumerate(colunas)]
        paredes, explorados = self.walls, self.explored
        fundo = cor["board"] * largura
        cache, pixels = {}, bytearray()
        for r, borda_r, topo_r in linhas:
            if r is None:
                pixels += fundo
                continue
            chave = (r, borda_r, topo_r)
            linha = cache.get(chave)
            if linha is None:
                partes = []
                for n, (c, borda_c, _) in enumerate(colunas):
                    if c is None:
                        partes.append(cor["board"])
                    elif (r, c) in paredes:
                        partes.append(cor["wall_top"] if topo_r and faixa[n] else
                                      cor["grid"] if borda_r or borda_c else cor["wall"])
                    elif (r, c) in explorados:
                        partes.append(cor["explored_grid"] if borda_r or borda_c else cor["explored"])
                    else:
                        partes.append(cor["grid"] if borda_r or borda_c else cor["cell"])
                linha = cache[chave] = b"".join(partes)
            pixels += linha
        dados = f"P6\n{largura} {altura}\n255\n".encode() + pixels
        imagem = tk.PhotoImage(master=self.root, data=bytes(dados), format="PPM")
        item = cv.create_image(x0, y0, image=imagem, anchor="nw", tags=("map", "tile"))
        cv.tag_lower(item)
        self.tiles[(i, j)] = (imagem, item)

    def draw_overlay(self):
        """A rota é uma única linha. Objetos do personagem ficam separados."""
        cv, s = self.canvas, self.cell_size
        cv.delete("overlay")
        if len(self.path) > 1:
            points = [xy for cell in cantos_da_rota(self.path) for xy in self.center(cell)]
            largura = max(1.5, min(6, s * .12))
            # Contorno escuro: a rota continua legível sobre as casas exploradas.
            cv.create_line(*points, fill=COLORS["board"], width=largura + 3,
                           capstyle="round", joinstyle="round", tags="overlay")
            cv.create_line(*points, fill=COLORS["path"], width=largura,
                           capstyle="round", joinstyle="round", tags=("overlay", "route"))
        x, y = self.center(self.start)
        radius = max(6, s * .27)
        cv.create_oval(x-radius, y-radius, x+radius, y+radius,
                       outline="#7fb0ff", dash=(3,2), width=2, tags="overlay")
        if self.target is not None:
            x, y = self.center(self.target)
            radius = max(7, s * .36)
            cv.create_oval(x-radius, y-radius, x+radius, y+radius,
                           fill=COLORS["board"], outline=COLORS["target"], width=2, tags="overlay")
            if s >= 12:
                cv.create_text(x, y, text="D", fill=COLORS["target"],
                               font=("Segoe UI", max(8,int(s*.25)), "bold"), tags="overlay")
        self.player_item = cv.create_oval(0,0,0,0, fill=COLORS["blue"],
                                          outline="#dbe8ff", width=2, tags=("overlay", "player"))
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
        radius = max(6, self.cell_size * .27)
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
