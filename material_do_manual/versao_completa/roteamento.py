"""Caminho mínimo: exemplos didáticos baseados no capítulo 6 de Skiena.

Execute com Python 3.10 ou mais recente: python roteamento.py
Não requer bibliotecas externas.

Representação: grafo[u] é uma lista de pares (vizinho, custo).
Todos os vértices devem aparecer como chaves, inclusive os sem saídas.
Os exemplos usam strings ou pares (linha, coluna) como vértices.
"""

from collections import deque
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


def dijkstra_simples(grafo, origem, destino):
    """Varredura para escolher o próximo vértice: O(V² + E) de tempo.

    Memória auxiliar: O(V), além dos O(V + E) do grafo.
    Ao parar no destino, não prometemos distâncias finais para outros vértices.
    """
    validar(grafo, origem, destino)
    distancia = {v: inf for v in grafo}
    anterior = {v: None for v in grafo}
    finalizados = set()
    distancia[origem] = 0

    while len(finalizados) < len(grafo):
        # Busca linear: examina os vértices ainda não finalizados.
        candidatos = (v for v in grafo if v not in finalizados)
        u = min(candidatos, key=distancia.get)

        # Se o menor custo é infinito, os restantes são inalcançáveis.
        if distancia[u] == inf:
            break
        finalizados.add(u)

        # Agora o custo do destino é definitivo: podemos encerrar.
        if u == destino:
            break

        for v, peso in grafo[u]:
            novo_custo = distancia[u] + peso
            # Relaxamento: substitui uma estimativa por uma rota melhor.
            if v not in finalizados and novo_custo < distancia[v]:
                distancia[v] = novo_custo
                anterior[v] = u

    return reconstruir(distancia, anterior, destino)


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


def bfs_unitario(grafo, origem, destino):
    """Busca em largura para arestas de custo 1: O(V + E), auxiliar O(V)."""
    validar(grafo, origem, destino)
    if any(peso != 1 for vizinhos in grafo.values() for _, peso in vizinhos):
        raise ValueError("Esta BFS exige que todas as arestas tenham custo 1.")
    distancia = {v: inf for v in grafo}
    anterior = {v: None for v in grafo}
    distancia[origem] = 0
    fila = deque([origem])
    while fila:
        u = fila.popleft()
        if u == destino:
            break
        for v, _ in grafo[u]:
            if distancia[v] == inf:
                distancia[v] = distancia[u] + 1
                anterior[v] = u
                fila.append(v)
    return reconstruir(distancia, anterior, destino)


def floyd_warshall(grafo):
    """Distâncias entre todos os pares; O(V³ + E), memória O(V²).

    Em grafos simples, o tempo se reduz a O(V³).

    Esta implementação mantém o contrato não negativo dos demais exemplos.
    O algoritmo geral aceita pesos negativos se não houver ciclos negativos.
    A matriz retornada contém custos, não as rotas reconstruídas.
    """
    validar(grafo)
    vertices = list(grafo)
    distancia = {
        u: {v: (0 if u == v else inf) for v in vertices}
        for u in vertices
    }
    for u, vizinhos in grafo.items():
        for v, peso in vizinhos:
            distancia[u][v] = min(distancia[u][v], peso)

    # k precisa ser o laço externo: libera um novo intermediário por etapa.
    for k in vertices:
        for u in vertices:
            for v in vertices:
                distancia[u][v] = min(
                    distancia[u][v], distancia[u][k] + distancia[k][v]
                )
    return distancia


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


def instancias_rodoviarias():
    """Quatro cenários artificiais; todos os pesos estão em minutos."""
    base = {
        "S": [("A", 4), ("B", 1)],
        "A": [("C", 1), ("D", 7)],
        "B": [("A", 2), ("C", 5)],
        "C": [("D", 3), ("T", 9)],
        "D": [("T", 2)],
        "T": [],
    }
    transito = {u: list(vizinhos) for u, vizinhos in base.items()}
    transito["B"] = [("A", 8), ("C", 5)]
    bloqueio = {u: list(vizinhos) for u, vizinhos in base.items()}
    bloqueio["C"] = [("T", 9)]
    isolado = {
        u: [(v, peso) for v, peso in vizinhos if v != "T"]
        for u, vizinhos in base.items()
    }
    return [
        ("Original", base, 9),
        ("Trânsito: B -> A passa a custar 8", transito, 10),
        ("Bloqueio: remove C -> D", bloqueio, 12),
        ("Sem acesso a T", isolado, inf),
    ]


def gerar_grade_com_barreira(tamanho):
    """Instância escalável: parede vertical com passagem na última linha.

    Origem: (0, 0). Destino: (0, tamanho - 1).
    Para tamanho >= 3, o custo ótimo é 3 * (tamanho - 1).
    """
    if tamanho < 3:
        raise ValueError("Use tamanho >= 3.")
    meio = tamanho // 2
    return [
        "".join("#" if j == meio and i < tamanho - 1 else "."
                for j in range(tamanho))
        for i in range(tamanho)
    ]


def demonstrar():
    for nome, grafo, esperado in instancias_rodoviarias():
        print(f"\n{nome}")
        for algoritmo in [dijkstra_simples, dijkstra_heap]:
            custo, caminho = algoritmo(grafo, "S", "T")
            assert custo == esperado
            rota = " -> ".join(caminho) if caminho else "Não existe rota"
            print(f"  {algoritmo.__name__}: custo={custo}; {rota}")
        assert floyd_warshall(grafo)["S"]["T"] == esperado

    grade = ["S.#.T", "..#..", ".....", ".###.", "....."]
    grafo = grafo_da_grade(grade)
    print("\nJogo: movimentos ortogonais, todos com custo 1")
    print("\n".join(grade))
    for algoritmo in [bfs_unitario, dijkstra_simples, dijkstra_heap]:
        custo, caminho = algoritmo(grafo, (0, 0), (0, 4))
        assert custo == 8
        print(f"  {algoritmo.__name__}: {custo} movimentos; {caminho}")

    print("\nInstâncias maiores com barreira; cada direção conta como um arco")
    for tamanho in [5, 10, 20]:
        grafo = grafo_da_grade(gerar_grade_com_barreira(tamanho))
        custo, _ = dijkstra_heap(grafo, (0, 0), (0, tamanho - 1))
        assert custo == 3 * (tamanho - 1)
        print(f"  Grade {tamanho}x{tamanho}: V={len(grafo)}, "
              f"E={sum(map(len, grafo.values()))}, custo={custo}")


if __name__ == "__main__":
    demonstrar()
