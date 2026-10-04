"""BFS: caminhos mínimos unitários, ordem FIFO e integração com o tabuleiro."""
from concurrent.futures import CancelledError
from math import inf
from pathlib import Path
from random import Random
import sys
from threading import Event
from time import monotonic, sleep
import tkinter as tk

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from mapas_movingai import Mapa, ler_mapa
from roteamento import BuscaCancelada, bfs, dijkstra_heap, grafo_da_grade
from apoio import conferir_rota
from tabuleiro import ALGORITMOS, RouteBoard, livre_mais_proxima


def comparar(grafo, origem, destino):
    esperado, _ = dijkstra_heap(grafo, origem, destino)
    custo, caminho = bfs(grafo, origem, destino)
    assert custo == esperado, (origem, destino, custo, esperado)
    conferir_rota(grafo, origem, destino, custo, caminho)


# A ordem dos vizinhos oferece uma rota longa antes da rota direta.
grafo = {"S": [("A", 1), ("T", 1)], "A": [("B", 1)],
         "B": [("T", 1)], "T": []}
assert bfs(grafo, "S", "T") == (1, ["S", "T"])
assert bfs(grafo, "S", "S") == (0, ["S"])
assert bfs({0: [], 1: []}, 0, 1) == (inf, [])
# Vértices de tipos diferentes, laços e arestas repetidas são aceitos.
comparar({"S": [("S", 1), (7, 1), (7, 1), ((1, 2), 1)],
          7: [("T", 1)], (1, 2): [("T", 1)], "T": []}, "S", "T")

# Observa a ordem de expansão, incluindo ciclos e duas descobertas possíveis de C.
expansoes = []
class VizinhosObservados(list):
    def __init__(self, nome, valores):
        super().__init__(valores)
        self.nome = nome

    def __iter__(self):
        expansoes.append(self.nome)
        return super().__iter__()

bruto = {"S": [("A", 1), ("B", 1)], "A": [("C", 1), ("D", 1)],
         "B": [("C", 1)], "C": [("A", 1), ("T", 1)],
         "D": [("T", 1)], "T": [], "isolado": []}
grafo = {u: VizinhosObservados(u, vizinhos) for u, vizinhos in bruto.items()}
assert bfs(grafo, "S", "isolado") == (inf, [])
# A validação lê cada lista uma vez; em seguida começa a expansão da busca.
assert expansoes[len(grafo):] == ["S", "A", "B", "C", "D", "T"]
print("OK: FIFO por níveis, marcação na descoberta, ciclos, empates e rota direta.")

consultas = 0
for mascara in range(512):
    grade = tuple("".join("#" if mascara & (1 << (r * 3 + c)) else "."
                          for c in range(3)) for r in range(3))
    grafo = grafo_da_grade(grade)
    for origem in grafo:
        for destino in grafo:
            comparar(grafo, origem, destino)
            consultas += 1

rng = Random(20261004)
for _ in range(80):
    n = rng.randint(2, 30)
    grafo = {u: [(v, 1) for v in range(n) if rng.random() < .15] for u in range(n)}
    for _ in range(5):
        comparar(grafo, rng.randrange(n), rng.randrange(n))
        consultas += 1
print(f"OK: {consultas} consultas, todas as grades 3x3 e grafos unitários dirigidos.")

for peso in (0, 2, 1.5, -1, inf, float("nan")):
    try:
        bfs({0: [(1, peso)], 1: []}, 0, 1)
    except ValueError:
        pass
    else:
        raise AssertionError(f"Custo incompatível aceito: {peso}")
for grafo, origem, destino in (({0: [(1, 1)]}, 0, 0), ({0: []}, 0, 1),
                               ({None: []}, None, None), ({}, 0, 0)):
    try:
        bfs(grafo, origem, destino)
    except ValueError:
        pass
    else:
        raise AssertionError("Grafo ou pontos inválidos aceitos")

grafo = grafo_da_grade(tuple("." * 20 for _ in range(20)))
chamadas = [0]
def cancelar_durante_busca():
    chamadas[0] += 1
    return chamadas[0] >= len(grafo) + 3
for cancelar in (lambda: True, cancelar_durante_busca):
    try:
        bfs(grafo, (0, 0), (19, 19), cancelar)
    except BuscaCancelada:
        pass
    else:
        raise AssertionError("Cancelamento não interrompeu a busca")
assert chamadas[0] == len(grafo) + 3
print("OK: custos incompatíveis rejeitados e cancelamento antes/durante a busca.")

for serie in (10, 20, 40):
    mapa = ler_mapa(BASE / "datasets/artificial_random" / f"random512-{serie}-0.map")
    origem = livre_mais_proxima(mapa, (0, 0))
    destino = livre_mais_proxima(mapa, (511, 511))
    grafo = grafo_da_grade(mapa.grade)
    comparar(grafo, origem, destino)
    print(f"OK: BFS e Dijkstra concordam no mapa completo random512-{serie}-0.map.")
del grafo

root = tk.Tk()
root.withdraw()
app = RouteBoard(root)
root.update_idletasks()
original = ALGORITMOS["bfs"]
liberar = Event()

def esperar_busca():
    prazo = monotonic() + 10
    while app.search_future is not None:
        assert monotonic() < prazo, "A busca na interface não terminou"
        root.update()
        sleep(.005)

try:
    assert app.algorithm.get() == "dijkstra"
    assert app.algorithm_options["bfs"].cget("text") == "BFS — fila FIFO"
    assert not app.algorithm_options["bfs"].instate(["disabled"])
    app.speed.set("Instantânea")
    app.load_board(Mapa(("...", ".#.", "..."), "obstáculo"))
    origem, destino = app.start, app.target
    app.algorithm_options["bfs"].invoke()
    app.play()
    assert app.distance.get() == "4" and app.player == destino
    conferir_rota(grafo_da_grade(app.current_grid()), origem, destino, 4, app.path)
    assert app.search_time.get().startswith("Busca:")
    app.algorithm_options["dijkstra"].invoke()
    assert app.player == origem and app.target == destino
    app.play()
    assert app.distance.get() == "4"

    app.load_board(Mapa((".#.", "###", ".#."), "sem rota"))
    app.algorithm_options["bfs"].invoke()
    app.play()
    assert app.distance.get() == "Sem rota" and not app.path
    app.load_board(Mapa((".",), "mesmo ponto"))
    app.play()
    assert app.distance.get() == "0" and app.player == app.target

    # Mapa público completo: a busca real usa a tarefa de segundo plano.
    mapa = ler_mapa(BASE / "datasets/artificial_random/random512-20-0.map")
    app.load_board(mapa)
    app.play()
    assert app.search_future is not None
    esperar_busca()
    assert app.distance.get() == "1022" and app.player == app.target

    # Pausa controlada para verificar troca de algoritmo enquanto a tarefa existe.
    iniciado = Event()
    def bfs_com_pausa(grafo, origem, destino, cancelar=None):
        iniciado.set()
        assert liberar.wait(5), "A tarefa não foi liberada"
        return bfs(grafo, origem, destino, cancelar)
    ALGORITMOS["bfs"] = (original[0], bfs_com_pausa)
    app.load_board(Mapa(tuple("." * 80 for _ in range(80)), "cancelamento"))
    app.play()
    assert iniciado.wait(5)
    tarefa, sinal = app.search_future, app.search_cancel
    assert not app.play_button.instate(["disabled"])
    app.algorithm_options["dijkstra"].invoke()
    assert sinal.is_set() and app.search_future is None
    assert app.player == app.start and app.distance.get() == "—"
    liberar.set()
    try:
        tarefa.result(timeout=5)
    except (BuscaCancelada, CancelledError):
        pass
    else:
        raise AssertionError("A tarefa antiga não foi cancelada")
    root.update()
    assert app.distance.get() == "—"
    ALGORITMOS["bfs"] = original

    # Todos os seletores precisam continuar visíveis na largura mínima.
    root.deiconify()
    root.geometry("920x660")
    root.update()
    for option in app.algorithm_options.values():
        assert option.winfo_width() >= option.winfo_reqwidth(), "Opção de algoritmo cortada"
        assert option.winfo_x() + option.winfo_width() <= app.algorithm_section.winfo_width()
finally:
    liberar.set()
    ALGORITMOS["bfs"] = original
    app.close()
print("OK: opção BFS habilitada, animação, mesma origem, sem rota, custo zero e mapa grande; troca cancela a busca.")
