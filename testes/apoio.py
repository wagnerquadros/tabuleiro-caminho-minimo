"""Referências de correção usadas somente pelas verificações."""
from collections import deque
from math import inf


def bfs_unitario(grafo, origem, destino):
    """Oráculo independente para grades de custo 1."""
    fila = deque([origem])
    anterior = {origem: None}
    while fila:
        u = fila.popleft()
        if u == destino:
            caminho = []
            while u is not None:
                caminho.append(u)
                u = anterior[u]
            caminho.reverse()
            return len(caminho) - 1, caminho
        for v, peso in grafo[u]:
            assert peso == 1
            if v not in anterior:
                anterior[v] = u
                fila.append(v)
    return inf, []


def conferir_rota(grafo, origem, destino, custo, caminho):
    if custo == inf:
        assert caminho == []
        return
    assert caminho[0] == origem and caminho[-1] == destino
    assert len(caminho) == len(set(caminho)), "A rota repete vértices"
    total = 0
    for a, b in zip(caminho, caminho[1:]):
        pesos = [peso for v, peso in grafo[a] if v == b]
        assert pesos, "A rota contém uma aresta inexistente"
        total += min(pesos)
    assert total == custo
