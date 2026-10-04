"""Algoritmos de caminho mínimo usados pelo tabuleiro.

Grafo: dicionário de listas de pares (vizinho, custo), com todas as chaves.
Dijkstra por varredura adapta Skiena, 2ª ed., seção 6.3.1, pp. 206–209.
A versão min-heap muda a seleção do vértice; força bruta enumera caminhos simples.
BFS usa fila FIFO para movimentos de custo 1 (Skiena, seção 5.6, pp. 162–165).
"""

from collections import deque
from heapq import heappop, heappush
from itertools import count
from math import inf, isfinite


class BuscaCancelada(Exception):
    """A entrada mudou ou a janela foi fechada durante uma busca."""


def _verificar_cancelamento(cancelar):
    if cancelar is not None and cancelar():
        raise BuscaCancelada()


def validar(grafo, origem, destino, cancelar=None, *, custo_unitario=False):
    """Confere os pesos em O(V + E); a BFS também exige custo 1."""
    _verificar_cancelamento(cancelar)
    if None in grafo:
        raise ValueError("None é reservado para indicar ausência de predecessor.")
    if origem not in grafo or destino not in grafo:
        raise ValueError("Origem e destino precisam pertencer ao grafo.")
    for vizinhos in grafo.values():
        _verificar_cancelamento(cancelar)
        for vizinho, peso in vizinhos:
            if vizinho not in grafo:
                raise ValueError("Todo vizinho também deve ser uma chave do grafo.")
            if not isfinite(peso) or peso < 0:
                raise ValueError("O peso precisa ser finito e não negativo.")
            if custo_unitario and peso != 1:
                raise ValueError("BFS exige custo 1 em todas as arestas.")


def reconstruir(distancia, anterior, destino):
    """Segue os predecessores até a origem e inverte a rota em O(V)."""
    if distancia[destino] == inf:
        return inf, []
    caminho = []
    atual = destino
    while atual is not None:
        caminho.append(atual)
        atual = anterior[atual]
    caminho.reverse()
    return distancia[destino], caminho


def dijkstra_simples(grafo, origem, destino, cancelar=None):
    """Versão do livro com seleção linear: tempo O(V² + E), auxiliar O(V).

    Usa distâncias, predecessores e o conjunto de vértices finalizados.
    Adaptação para o tabuleiro: encerra ao finalizar o destino, em vez de
    calcular distâncias para todas as casas. Sem rota, retorna (inf, []).
    """
    validar(grafo, origem, destino, cancelar)
    distancia = {v: inf for v in grafo}
    anterior = {v: None for v in grafo}
    finalizados = set()
    distancia[origem] = 0
    u = origem

    while u is not None:
        _verificar_cancelamento(cancelar)
        finalizados.add(u)
        # O destino só pode encerrar a busca quando seu custo é definitivo.
        if u == destino:
            break

        for v, peso in grafo[u]:
            novo_custo = distancia[u] + peso
            if v not in finalizados and novo_custo < distancia[v]:
                distancia[v] = novo_custo
                anterior[v] = u

        # Equivale à varredura dos vetores intree e distance no código em C.
        # O livro não usa fila de prioridade nesta implementação.
        u = None
        menor = inf
        for v in grafo:
            if v not in finalizados and distancia[v] < menor:
                menor = distancia[v]
                u = v
        # Se não há candidato com distância finita, o destino é inalcançável.

    return reconstruir(distancia, anterior, destino)


def dijkstra_heap(grafo, origem, destino, cancelar=None):
    """Dijkstra com min-heap binário e descarte de entradas desatualizadas.

    Tempo geral O(V + E log(E + 2)); auxiliar O(V + E), além do grafo.
    Em grafos simples: O((V + E) log(V + 1)). Na grade E = O(V), portanto
    tempo O(V log(V + 1)) e memória auxiliar O(V).
    heapq não oferece decrease-key: uma melhora insere uma nova entrada.
    """
    validar(grafo, origem, destino, cancelar)
    distancia = {v: inf for v in grafo}
    anterior = {v: None for v in grafo}
    distancia[origem] = 0

    # Desempata custos sem precisar comparar os nomes dos vértices.
    ordem = count()
    fila = [(0, next(ordem), origem)]
    while fila:
        _verificar_cancelamento(cancelar)
        custo, _, u = heappop(fila)
        # Pode haver uma entrada antiga para uma distância já melhorada.
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


def bfs(grafo, origem, destino, cancelar=None):
    """Busca em largura com fila FIFO: tempo O(V + E), auxiliar O(V).

    Cada aresta deve custar 1. A fila explora os vértices por distância
    crescente em movimentos; a primeira descoberta fixa a distância mínima.
    Adapta Skiena, seção 5.6, e reconstrói a rota com predecessores.
    Sem rota, retorna (inf, []); cancelamento lança BuscaCancelada.
    """
    validar(grafo, origem, destino, cancelar, custo_unitario=True)
    distancia = {v: inf for v in grafo}
    anterior = {v: None for v in grafo}
    distancia[origem] = 0
    fila = deque([origem])

    while fila:
        _verificar_cancelamento(cancelar)
        # FIFO: o primeiro vértice inserido é o primeiro a ser retirado.
        u = fila.popleft()
        if u == destino:
            break
        for v, _ in grafo[u]:
            if distancia[v] == inf:
                # Marca na inserção para não enfileirar a mesma célula novamente.
                distancia[v] = distancia[u] + 1
                anterior[v] = u
                fila.append(v)

    return reconstruir(distancia, anterior, destino)


def forca_bruta(grafo, origem, destino, cancelar=None, progresso=None):
    """Enumera todos os caminhos simples com busca em profundidade e retrocesso.

    Não encerra na primeira solução e não descarta ramos pelo custo.
    Visitados contém apenas vértices da rota atual, não de toda a busca.
    Uma pilha explícita substitui as chamadas recursivas: auxiliar O(V).
    Na grade de quatro vizinhos, O(V * 3**V) é um limite superior conservador
    de tempo, além da validação O(V + E). O pior caso é exponencial.
    Cancelamento lança BuscaCancelada, sem retornar um ótimo não comprovado.
    progresso recebe (estados explorados, rotas completas) periodicamente.
    """
    validar(grafo, origem, destino, cancelar)
    melhor_custo = inf
    melhor_caminho = []
    caminho = [origem]
    visitados = {origem}
    custos = [0]
    # Cada iterador lembra o próximo vizinho a tentar ao retornar a uma célula.
    pilha = [iter(grafo[origem])]
    estados, rotas, iteracoes = 1, 0, 0
    if progresso is not None:
        progresso((estados, rotas))

    while pilha:
        _verificar_cancelamento(cancelar)
        iteracoes += 1
        # Agrupa as notificações; não altera as escolhas nem corta ramos.
        if progresso is not None and iteracoes % 4096 == 0:
            progresso((estados, rotas))
        u = caminho[-1]
        if u == destino:
            rotas += 1
            # Chegar ao destino termina só este ramo, não a enumeração inteira.
            if custos[-1] < melhor_custo:
                melhor_custo = custos[-1]
                melhor_caminho = caminho.copy()
        else:
            vizinho = next(pilha[-1], None)
            if vizinho is not None:
                v, peso = vizinho
                if v not in visitados:
                    caminho.append(v)
                    visitados.add(v)
                    custos.append(custos[-1] + peso)
                    pilha.append(iter(grafo[v]))
                    estados += 1
                # Tenta o próximo vizinho, mesmo se o custo já supera o melhor.
                continue

        # Destino alcançado ou vizinhos esgotados: desfaz a última escolha.
        pilha.pop()
        visitados.remove(caminho.pop())
        custos.pop()

    if progresso is not None:
        progresso((estados, rotas))
    return melhor_custo, melhor_caminho


def grafo_da_grade(grade):
    """Constrói em O(linhas × colunas) o grafo de movimentos ortogonais.

    '#' é obstáculo; '.' é célula livre. Cada aresta tem custo 1.
    A grade tem no máximo quatro arestas de saída por vértice.
    """
    if not grade or not grade[0] or any(len(l) != len(grade[0]) for l in grade):
        raise ValueError("A grade deve ser retangular e não vazia.")
    if any(set(linha) - {".", "#"} for linha in grade):
        raise ValueError("A grade aceita apenas '.' e '#'.")
    grafo = {
        (r, c): []
        for r, linha in enumerate(grade)
        for c, celula in enumerate(linha)
        if celula == "."
    }
    for r, c in grafo:
        for dr, dc in ((-1, 0), (0, 1), (1, 0), (0, -1)):
            vizinho = (r + dr, c + dc)
            if vizinho in grafo:
                grafo[(r, c)].append((vizinho, 1))
    return grafo
