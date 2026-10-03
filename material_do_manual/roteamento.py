from heapq import heappop, heappush
from itertools import count
from math import inf, isfinite


def validar(grafo, origem=None, destino=None):
    """Confere o contrato da entrada em O(V + E). Pesos são não negativos."""
    if None in grafo:
        raise ValueError("None é reservado para indicar ausência de predecessor.")
    if origem is not None and origem not in grafo:
        raise ValueError("A origem não está no grafo.")
    if destino is not None and destino not in grafo:
        raise ValueError("O destino não está no grafo.")
    for vizinhos in grafo.values():
        for vizinho, peso in vizinhos:
            if vizinho not in grafo:
                raise ValueError("Todo vizinho também deve ser uma chave do grafo.")
            if not isfinite(peso) or peso < 0:
                raise ValueError("O peso precisa ser finito e não negativo.")


def reconstruir(distancia, anterior, destino):
    """Segue os predecessores de trás para frente; depois inverte a rota."""
    if distancia[destino] == inf:
        return inf, []
    caminho = []
    atual = destino
    while atual is not None:
        caminho.append(atual)
        atual = anterior[atual]
    caminho.reverse()
    return distancia[destino], caminho


def dijkstra_heap(grafo, origem, destino):
    """Fila de prioridade binária; entradas antigas são descartadas.

    Limite geral de tempo: O(V + E log(E + 2)); auxiliar: O(V + E).
    Em grafos simples, também vale O((V + E) log(V + 1)).
    A fila pode guardar várias entradas do mesmo vértice: não usamos decrease-key.
    """
    validar(grafo, origem, destino)
    distancia = {v: inf for v in grafo}
    anterior = {v: None for v in grafo}
    distancia[origem] = 0

    # O contador desempata custos sem precisar comparar os nomes dos vértices.
    ordem = count()
    fila = [(0, next(ordem), origem)]
    while fila:
        custo, _, u = heappop(fila)

        # Já encontramos uma rota melhor depois de inserir esta entrada.
        if custo != distancia[u]:
            continue
        if u == destino:
            break

        for v, peso in grafo[u]:
            novo_custo = custo + peso
            if novo_custo < distancia[v]:
                distancia[v] = novo_custo
                anterior[v] = u
                heappush(fila, (novo_custo, next(ordem), v))

    return reconstruir(distancia, anterior, destino)


def grafo_da_grade(grade):
    """Cada célula livre vira vértice; movimentos ortogonais custam 1.

    '#' é obstáculo; os demais caracteres representam células livres.
    Custo de construção: O(linhas * colunas), incluindo ler os obstáculos.
    Só há arestas entre células livres vizinhas: nenhuma atravessa uma parede.
    """
    if not grade or not grade[0] or any(len(l) != len(grade[0]) for l in grade):
        raise ValueError("A grade deve ser retangular e não vazia.")
    linhas, colunas = len(grade), len(grade[0])
    grafo = {
        (i, j): []
        for i in range(linhas)
        for j in range(colunas)
        if grade[i][j] != "#"
    }
    for i, j in grafo:
        for di, dj in [(-1, 0), (0, 1), (1, 0), (0, -1)]:
            vizinho = (i + di, j + dj)
            if vizinho in grafo:
                grafo[(i, j)].append((vizinho, 1))
    return grafo
