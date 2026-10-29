import json
from math import inf
import sys
from time import perf_counter

from roteamento import bfs, bmssp, dijkstra_heap, dijkstra_simples, forca_bruta, grafo_da_grade

ALGORITMOS = {
    "dijkstra_simples": dijkstra_simples, "dijkstra": dijkstra_heap,
    "bfs": bfs, "bmssp": bmssp, "forca_bruta": forca_bruta,
}


def enviar(linha):
    sys.stdout.write(linha + "\n")
    sys.stdout.flush()


class GrafoAoVivo(dict):
    """Grafo que envia, em lotes, cada casa cujos vizinhos o algoritmo consulta.

    Um lote sai a cada 512 casas novas ou 15 ms, o que vier primeiro.
    """

    def __init__(self, grafo):
        super().__init__(grafo)
        self.vistos = set()
        self.lote = []
        self.ultimo = perf_counter()

    def __getitem__(self, vertice):
        if vertice not in self.vistos:
            self.vistos.add(vertice)
            self.lote.append(vertice)
            if len(self.lote) >= 512 or perf_counter() - self.ultimo > .015:
                self.descarregar()
        return dict.__getitem__(self, vertice)

    def descarregar(self):
        if self.lote:
            enviar("C " + " ".join(f"{r},{c}" for r, c in self.lote))
            self.lote = []
        self.ultimo = perf_counter()


class RotaAtual:
    """Envia a rota em construção da força bruta, no máximo a cada 60 ms."""

    def __init__(self):
        self.ultimo = 0.0

    def __call__(self, caminho):
        agora = perf_counter()
        if agora - self.ultimo >= .06:
            self.ultimo = agora
            enviar("A " + " ".join(f"{r},{c}" for r, c in caminho))


def executar(busca, grafo, origem, destino, algoritmo, progresso=None, rota_atual=None):
    if algoritmo == "forca_bruta":
        return busca(grafo, origem, destino, None, progresso, rota_atual)
    return busca(grafo, origem, destino)


def main():
    entrada = json.load(sys.stdin)
    grade = tuple(entrada["grade"])
    origem, destino = tuple(entrada["origem"]), tuple(entrada["destino"])
    algoritmo = entrada["algoritmo"]
    busca = ALGORITMOS[algoritmo]

    if not entrada.get("explorar", True):
        # Execução única: progresso e rota em teste, sem registro de casas.
        grafo = grafo_da_grade(grade)
        inicio = perf_counter()
        custo, caminho = executar(busca, grafo, origem, destino, algoritmo,
                                  lambda p: enviar(f"P {p[0]} {p[1]}"), RotaAtual())
        enviar_resultado(custo, caminho, perf_counter() - inicio)
        return

    # 1. Exploração: com registro, enviada enquanto acontece.
    vivo = GrafoAoVivo(grafo_da_grade(grade))
    executar(busca, vivo, origem, destino, algoritmo,
             lambda p: enviar(f"P {p[0]} {p[1]}"), RotaAtual())
    vivo.descarregar()
    enviar("F")

    # 2. Medição: a mesma busca, sem registro; só a chamada do algoritmo é medida.
    grafo = grafo_da_grade(grade)
    inicio = perf_counter()
    custo, caminho = executar(busca, grafo, origem, destino, algoritmo)
    enviar_resultado(custo, caminho, perf_counter() - inicio)


def enviar_resultado(custo, caminho, tempo):
    enviar("R " + json.dumps({"custo": None if custo == inf else custo,
                              "caminho": [list(p) for p in caminho], "tempo": tempo}))


if __name__ == "__main__":
    try:
        main()
    except Exception as erro:  # O tabuleiro mostra a mensagem no status.
        enviar(f"E {type(erro).__name__}: {erro}")
