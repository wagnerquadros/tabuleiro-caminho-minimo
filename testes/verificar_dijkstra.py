"""Correção em grafos ponderados, grades e cancelamento de buscas longas."""
from concurrent.futures import ThreadPoolExecutor
from math import inf
from pathlib import Path
from random import Random
import sys
from threading import Event

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from roteamento import BuscaCancelada, dijkstra_simples, dijkstra_heap, grafo_da_grade
from apoio import bfs_unitario, conferir_rota

ALGORITMOS = (dijkstra_simples, dijkstra_heap)


def referencia_ponderada(grafo, origem, destino):
    # Bellman-Ford, usado só como referência independente das escolhas de Dijkstra.
    d = {v: inf for v in grafo}
    d[origem] = 0
    for _ in range(len(grafo) - 1):
        mudou = False
        for u, vizinhos in grafo.items():
            for v, peso in vizinhos:
                if d[u] + peso < d[v]:
                    d[v] = d[u] + peso
                    mudou = True
        if not mudou:
            break
    return d[destino]


def conferir(grafo, a, b, esperado):
    for algoritmo in ALGORITMOS:
        custo, rota = algoritmo(grafo, a, b)
        assert custo == esperado, (algoritmo.__name__, a, b, custo, esperado)
        conferir_rota(grafo, a, b, custo, rota)


# A primeira estimativa de A e do destino é ruim e precisa ser relaxada.
grafo = {"S": [("A", 10), ("B", 1)], "A": [("T", 15)],
         "B": [("A", 1), ("T", 40)], "T": [], "isolado": []}
conferir(grafo, "S", "T", 17)
conferir(grafo, "S", "isolado", inf)
conferir(grafo, "S", "S", 0)
# Empates com vértices que não podem ser ordenados entre si e arestas de custo zero.
misto = {"S": [((1, 2), 0), (7, 0)], (1, 2): [(7, 0), ("T", 2)],
         7: [((1, 2), 0), ("T", 1)], "T": []}
conferir(misto, "S", "T", 1)
conferir({0: [(1, 9), (1, 2)], 1: []}, 0, 1, 2)

rng = Random(20261003)
consultas = 0
for _ in range(120):
    n = rng.randint(2, 14)
    grafo = {u: [(v, rng.randint(0, 25)) for v in range(n)
                 if v != u and rng.random() < .2] for u in range(n)}
    for _ in range(8):
        a, b = rng.randrange(n), rng.randrange(n)
        conferir(grafo, a, b, referencia_ponderada(grafo, a, b))
        consultas += 1

# Todas as 512 disposições de obstáculos em uma grade 3 × 3.
for mascara in range(512):
    grade = tuple("".join("#" if mascara & (1 << (r * 3 + c)) else "."
                          for c in range(3)) for r in range(3))
    grafo = grafo_da_grade(grade)
    if grafo:
        a, b = next(iter(grafo)), next(reversed(grafo))
        esperado, _ = bfs_unitario(grafo, a, b)
        conferir(grafo, a, b, esperado)
        consultas += 1

for algoritmo in ALGORITMOS:
    for grafo, a, b in (({0: [(1, -1)], 1: []}, 0, 1),
                         ({0: [(1, inf)], 1: []}, 0, 1),
                         ({0: [(1, float("nan"))], 1: []}, 0, 1),
                         ({0: [(1, 1)]}, 0, 0), ({0: []}, 0, 3)):
        try:
            algoritmo(grafo, a, b)
        except ValueError:
            pass
        else:
            raise AssertionError("Entrada inválida aceita")

# O cancelamento também funciona depois de a tarefa ter começado, não só na fila.
grafo = grafo_da_grade(tuple("." * 100 for _ in range(100)))
for algoritmo in ALGORITMOS:
    cancelar = Event()
    iniciado = Event()
    chamadas = [0]
    def verificar():
        chamadas[0] += 1
        if chamadas[0] >= len(grafo) + 3:
            iniciado.set()
        return cancelar.is_set()
    with ThreadPoolExecutor(max_workers=1) as executor:
        futuro = executor.submit(algoritmo, grafo, (0, 0), (99, 99), verificar)
        assert iniciado.wait(5), "A busca não iniciou"
        cancelar.set()
        try:
            futuro.result(timeout=3)
        except BuscaCancelada:
            pass
        else:
            raise AssertionError("A tarefa em execução não foi cancelada")
print(f"OK: {consultas} consultas aleatórias/exaustivas, casos ponderados, entradas inválidas e cancelamento.")
