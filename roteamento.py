"""Algoritmos de caminho mínimo usados pelo tabuleiro.

Grafo: dicionário de listas de pares (vizinho, custo), com todas as chaves.
Dijkstra por varredura adapta Skiena, 2ª ed., seção 6.3.1, pp. 206–209.
A versão min-heap muda a seleção do vértice; força bruta enumera caminhos simples.
BFS usa fila FIFO para movimentos de custo 1 (Skiena, seção 5.6, pp. 162–165).
BMSSP segue Duan, Mao, Mao, Shu e Yin (2025), "Breaking the Sorting Barrier".
"""

from collections import deque
from heapq import heappop, heappush
from itertools import count
from math import ceil, floor, inf, isfinite, log2


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


def dijkstra_heap(grafo, origem, destino, cancelar=None, parar_no_destino=True,
                  estatisticas=None):
    """Dijkstra com min-heap binário e descarte de entradas desatualizadas.

    Tempo geral O(V + E log(E + 2)); auxiliar O(V + E), além do grafo.
    Em grafos simples: O((V + E) log(V + 1)). Na grade E = O(V), portanto
    tempo O(V log(V + 1)) e memória auxiliar O(V).
    heapq não oferece decrease-key: uma melhora insere uma nova entrada.
    parar_no_destino=False calcula todas as casas, como o BMSSP, para comparação.
    estatisticas, se for um dict, recebe o esforço da busca:
    retiradas (total de heappop), descartadas (entradas desatualizadas) e
    expandidas (vértices cujos vizinhos foram examinados). Quando a busca para
    ao retirar o destino, essa última retirada não é uma expansão.
    """
    validar(grafo, origem, destino, cancelar)
    distancia = {v: inf for v in grafo}
    anterior = {v: None for v in grafo}
    distancia[origem] = 0

    # Desempata custos sem precisar comparar os nomes dos vértices.
    ordem = count()
    fila = [(0, next(ordem), origem)]
    retiradas = descartadas = 0
    parou_no_destino = False
    while fila:
        _verificar_cancelamento(cancelar)
        custo, _, u = heappop(fila)
        retiradas += 1
        # Pode haver uma entrada antiga para uma distância já melhorada.
        if custo != distancia[u]:
            descartadas += 1
            continue
        if u == destino and parar_no_destino:
            parou_no_destino = True
            break

        for v, peso in grafo[u]:
            novo_custo = custo + peso
            if novo_custo < distancia[v]:
                distancia[v] = novo_custo
                anterior[v] = u
                heappush(fila, (novo_custo, next(ordem), v))

    if estatisticas is not None:
        # As expandidas saem por diferença, sem um contador a mais no laço.
        estatisticas.update(retiradas=retiradas, descartadas=descartadas,
                            expandidas=retiradas - descartadas - parou_no_destino)
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


def forca_bruta(grafo, origem, destino, cancelar=None, progresso=None, rota_atual=None):
    """Enumera todos os caminhos simples com busca em profundidade e retrocesso.

    Não encerra na primeira solução e não descarta ramos pelo custo.
    Visitados contém apenas vértices da rota atual, não de toda a busca.
    Uma pilha explícita substitui as chamadas recursivas: auxiliar O(V).
    Na grade de quatro vizinhos, O(V * 3**V) é um limite superior conservador
    de tempo, além da validação O(V + E). O pior caso é exponencial.
    Cancelamento lança BuscaCancelada, sem retornar um ótimo não comprovado.
    progresso recebe (estados explorados, rotas completas) periodicamente.
    rota_atual, se dada, recebe no mesmo ritmo a lista da rota em construção;
    ela é a própria lista da busca: copie-a se precisar guardá-la.
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
        if iteracoes % 4096 == 0:
            if progresso is not None:
                progresso((estados, rotas))
            if rota_atual is not None:
                rota_atual(caminho)
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


class _FilaDeBlocos:
    """Estrutura D do BMSSP (Lema 3.3), simplificada com min-heap.

    Insert guarda o menor valor de cada vértice; BatchPrepend recebe valores
    menores que todos os presentes; Pull devolve até M vértices de menor valor
    e um limite que os separa dos restantes. O artigo usa listas de blocos para
    atingir o limite teórico; aqui cada operação custa O(log N).
    """

    def __init__(self, m, limite):
        self.m = m
        self.limite = limite
        self.valor = {}
        self.heap = []

    def __bool__(self):
        return bool(self.valor)

    def inserir(self, v, chave):
        if chave < self.valor.get(v, self.limite):
            self.valor[v] = chave
            heappush(self.heap, (chave, v))

    def inserir_lote(self, itens):
        # Com o heap, prepend é uma sequência de inserções; o resultado é o mesmo.
        for v, chave in itens:
            self.inserir(v, chave)

    def _descartar_antigos(self):
        while self.heap and self.valor.get(self.heap[0][1]) != self.heap[0][0]:
            heappop(self.heap)

    def retirar(self):
        """Pull: (limite B_i, até M vértices com chave < B_i)."""
        conjunto = []
        while len(conjunto) < self.m:
            self._descartar_antigos()
            if not self.heap:
                break
            _, v = heappop(self.heap)
            del self.valor[v]
            conjunto.append(v)
        self._descartar_antigos()
        return (self.heap[0][0] if self.heap else self.limite), conjunto


def distancias_bmssp(grafo, origem, cancelar=None, estatisticas=None):
    """BMSSP: distâncias da origem a todos os vértices, sem fila global ordenada.

    Implementa os Algoritmos 1 (FindPivots), 2 (BaseCase) e 3 (BMSSP) de
    Duan et al. (2025), com k = ⌊log^(1/3) n⌋, t = ⌊log^(2/3) n⌋ e
    l = ⌈log n / t⌉ níveis. O artigo supõe comprimentos de caminho distintos;
    aqui a ordem total é (distância, arestas, índice do vértice), o que separa
    empates da grade e também aceita arestas de custo zero.
    Retorna (distancia, anterior). estatisticas, se for um dict, recebe
    k, t, níveis, chamadas recursivas e casos-base executados.
    Cancelamento lança BuscaCancelada.
    """
    n = len(grafo)
    indice = {v: i for i, v in enumerate(grafo)}
    distancia = {v: inf for v in grafo}
    arestas = {v: inf for v in grafo}
    anterior = {v: None for v in grafo}
    distancia[origem] = 0
    arestas[origem] = 0

    logn = log2(max(n, 2))
    k = max(1, floor(logn ** (1 / 3)))
    t = max(1, floor(logn ** (2 / 3)))
    niveis = ceil(logn / t)
    # Maior que qualquer chave finita e menor que a de um vértice não alcançado.
    sem_limite = (inf, -1, -1)
    contagem = {"k": k, "t": t, "niveis": niveis, "chamadas": 0, "casos_base": 0}

    def chave(v):
        return distancia[v], arestas[v], indice[v]

    def relaxar(u, v, peso):
        """Relaxa com ≤, como no artigo; devolve a nova chave de v ou None."""
        candidato = (distancia[u] + peso, arestas[u] + 1)
        if candidato <= (distancia[v], arestas[v]):
            distancia[v], arestas[v] = candidato
            anterior[v] = u
            return candidato + (indice[v],)
        return None

    def encontrar_pivos(limite, fronteira):
        """Algoritmo 1: k rodadas de relaxamento estilo Bellman-Ford."""
        trabalho = set(fronteira)
        camada = fronteira
        for _ in range(k):
            proxima = set()
            for u in camada:
                _verificar_cancelamento(cancelar)
                for v, peso in grafo[u]:
                    nova = relaxar(u, v, peso)
                    if nova is not None and nova < limite:
                        proxima.add(v)
            trabalho |= proxima
            if len(trabalho) > k * len(fronteira):
                return list(fronteira), trabalho
            camada = proxima

        # Floresta F: aresta predecessor → vértice, dentro de W, ainda justa.
        def justa(u, v):
            return u in trabalho and any(
                x == v and (distancia[u] + peso, arestas[u] + 1) == (distancia[v], arestas[v])
                for x, peso in grafo[u])

        filhos = {}
        for v in trabalho:
            if justa(anterior[v], v):
                filhos.setdefault(anterior[v], []).append(v)
        pivos = []
        for raiz in fronteira:
            if justa(anterior[raiz], raiz):
                continue  # Não é raiz em F.
            tamanho, pilha = 0, [raiz]
            while pilha and tamanho < k:
                tamanho += 1
                pilha.extend(filhos.get(pilha.pop(), ()))
            if tamanho >= k:
                pivos.append(raiz)
        return pivos, trabalho

    def caso_base(limite, fronteira):
        """Algoritmo 2: Dijkstra limitado que finaliza até k + 1 vértices."""
        contagem["casos_base"] += 1
        heap = [(chave(x), x) for x in fronteira if chave(x) < limite]
        heap.sort()
        concluidos, vistos = [], set()
        while heap and len(concluidos) < k + 1:
            _verificar_cancelamento(cancelar)
            c, u = heappop(heap)
            if u in vistos or c != chave(u):
                continue
            vistos.add(u)
            concluidos.append(u)
            for v, peso in grafo[u]:
                nova = relaxar(u, v, peso)
                if nova is not None and nova < limite:
                    heappush(heap, (nova, v))
        if len(concluidos) <= k:
            return limite, set(concluidos)
        novo_limite = max(chave(v) for v in concluidos)
        return novo_limite, {v for v in concluidos if chave(v) < novo_limite}

    def resolver(nivel, limite, fronteira):
        """Algoritmo 3: divide a faixa [.., limite) em blocos e resolve cada um."""
        contagem["chamadas"] += 1
        if nivel == 0:
            return caso_base(limite, fronteira)
        pivos, trabalho = encontrar_pivos(limite, fronteira)
        fila = _FilaDeBlocos(2 ** ((nivel - 1) * t), limite)
        for x in pivos:
            fila.inserir(x, chave(x))
        ultimo_limite = min((chave(x) for x in pivos), default=limite)
        concluidos = set()
        capacidade = k * 2 ** (nivel * t)
        while len(concluidos) < capacidade and fila:
            limite_i, conjunto = fila.retirar()
            ultimo_limite, concluidos_i = resolver(nivel - 1, limite_i, conjunto)
            concluidos |= concluidos_i
            antecipados = []
            for u in concluidos_i:
                _verificar_cancelamento(cancelar)
                for v, peso in grafo[u]:
                    nova = relaxar(u, v, peso)
                    if nova is None:
                        continue
                    if limite_i <= nova < limite:
                        fila.inserir(v, nova)
                    elif ultimo_limite <= nova < limite_i:
                        antecipados.append((v, nova))
            antecipados.extend((x, chave(x)) for x in conjunto
                               if ultimo_limite <= chave(x) < limite_i)
            fila.inserir_lote(antecipados)
        ultimo_limite = min(ultimo_limite, limite)
        concluidos.update(x for x in trabalho if chave(x) < ultimo_limite)
        return ultimo_limite, concluidos

    resolver(niveis, sem_limite, [origem])
    if estatisticas is not None:
        estatisticas.update(contagem)
    return distancia, anterior


def bmssp(grafo, origem, destino, cancelar=None, estatisticas=None):
    """Caminho mínimo pelo BMSSP de Duan et al. (2025), sem ordenar todos os vértices.

    Tempo teórico O(m log^(2/3) n) com a estrutura de blocos do artigo; esta
    versão usa heap na estrutura D, o que preserva a correção, mas não esse
    limite. Calcula distâncias para todos os vértices alcançáveis, sem parar
    no destino. Memória auxiliar O(V + E). Sem rota, retorna (inf, []).
    """
    validar(grafo, origem, destino, cancelar)
    distancia, anterior = distancias_bmssp(grafo, origem, cancelar, estatisticas)
    return reconstruir(distancia, anterior, destino)


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
