"""Correção do BMSSP: distâncias de todos os vértices, rotas, empates e cancelamento."""
from concurrent.futures import ThreadPoolExecutor
from heapq import heappop, heappush
import json
from math import inf
from pathlib import Path
from random import Random
import sys
from threading import Event

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from mapas_movingai import ler_mapa
from roteamento import BuscaCancelada, bmssp, distancias_bmssp, grafo_da_grade
from apoio import bfs_unitario, conferir_rota


def referencia(grafo, origem):
    d = {v: inf for v in grafo}
    d[origem] = 0
    fila, ordem = [(0, 0, origem)], 0
    while fila:
        custo, _, u = heappop(fila)
        if custo > d[u]:
            continue
        for v, peso in grafo[u]:
            if custo + peso < d[v]:
                d[v] = custo + peso
                ordem += 1
                heappush(fila, (d[v], ordem, v))
    return d


def conferir_todos(grafo, origem):
    estatisticas = {}
    distancia, _ = distancias_bmssp(grafo, origem, estatisticas=estatisticas)
    esperado = referencia(grafo, origem)
    for v in grafo:
        assert abs(distancia[v] - esperado[v]) < 1e-9 if esperado[v] < inf \
            else distancia[v] == inf, (origem, v, distancia[v], esperado[v])
    return estatisticas


consultas = 0
grafo = {"S": [("A", 10), ("B", 1)], "A": [("T", 15)],
         "B": [("A", 1), ("T", 40)], "T": [], "isolado": []}
for destino, custo in (("T", 17), ("isolado", inf), ("S", 0)):
    resultado = bmssp(grafo, "S", destino)
    assert resultado[0] == custo, resultado
    conferir_rota(grafo, "S", destino, *resultado)
misto = {"S": [((1, 2), 0), (7, 0)], (1, 2): [(7, 0), ("T", 2)],
         7: [((1, 2), 0), ("T", 1)], "T": []}
assert bmssp(misto, "S", "T")[0] == 1
assert bmssp({0: [(1, 9), (1, 2)], 1: []}, 0, 1) == (2, [0, 1])

rng = Random(20251015)
niveis = set()
for _ in range(250):
    n = rng.choice((2, 6, 30, 200, 1200))
    grafo = {u: [(v, rng.choice((0, 1, 1, 2, 7, rng.random() * 10)))
                 for v in rng.sample(range(n), min(n, rng.randint(0, 4))) if v != u]
             for u in range(n)}
    niveis.add(conferir_todos(grafo, rng.randrange(n))["niveis"])
    consultas += 1
assert max(niveis) >= 3, niveis

for mascara in range(512):
    grade = tuple("".join("#" if mascara & (1 << (r * 3 + c)) else "."
                          for c in range(3)) for r in range(3))
    grafo = grafo_da_grade(grade)
    for a in grafo:
        for b in grafo:
            custo, rota = bmssp(grafo, a, b)
            assert custo == bfs_unitario(grafo, a, b)[0], (grade, a, b)
            conferir_rota(grafo, a, b, custo, rota)
            consultas += 1

for _ in range(40):
    linhas, colunas = rng.choice(((6, 10), (25, 40), (64, 64)))
    densidade = rng.random() * .45
    grade = tuple("".join("#" if rng.random() < densidade else "." for _ in range(colunas))
                  for _ in range(linhas))
    grafo = grafo_da_grade(grade)
    if grafo:
        conferir_todos(grafo, rng.choice(list(grafo)))
        consultas += 1

PASTA = BASE / "datasets/testes"
manifesto = json.loads((PASTA / "manifesto.json").read_text(encoding="utf-8"))
for registro in manifesto["mapas"]:
    grafo = grafo_da_grade(ler_mapa(PASTA / registro["arquivo"]).grade)
    custo, rota = bmssp(grafo, (0, 0), (5, 9))
    assert custo == registro["custo_minimo"], (registro["arquivo"], custo)
    conferir_rota(grafo, (0, 0), (5, 9), custo, rota)
    consultas += 1

mapa = ler_mapa(BASE / "datasets/artificial_random/random512-20-0.map")
grafo = grafo_da_grade(mapa.grade)
estatisticas = conferir_todos(grafo, next(iter(grafo)))
assert estatisticas["niveis"] == 3 and estatisticas["casos_base"] > 0
consultas += 1

for grafo, a, b in (({0: [(1, -1)], 1: []}, 0, 1), ({0: [(1, inf)], 1: []}, 0, 1),
                     ({0: [(1, float("nan"))], 1: []}, 0, 1), ({0: [(1, 1)]}, 0, 0),
                     ({0: []}, 0, 3)):
    try:
        bmssp(grafo, a, b)
    except ValueError:
        pass
    else:
        raise AssertionError("Entrada inválida aceita")

grafo = grafo_da_grade(tuple("." * 150 for _ in range(150)))
cancelar, iniciado, chamadas = Event(), Event(), [0]
def verificar():
    chamadas[0] += 1
    if chamadas[0] >= len(grafo) + 50:
        iniciado.set()
    return cancelar.is_set()
with ThreadPoolExecutor(max_workers=1) as executor:
    futuro = executor.submit(bmssp, grafo, (0, 0), (149, 149), verificar)
    assert iniciado.wait(10), "A busca não iniciou"
    cancelar.set()
    try:
        futuro.result(timeout=5)
    except BuscaCancelada:
        pass
    else:
        raise AssertionError("A tarefa em execução não foi cancelada")
print(f"OK: {consultas} consultas do BMSSP (aleatórias, 3 × 3 exaustivas, mapas de teste "
      f"e 512 × 512), entradas inválidas e cancelamento.")
