"""Força bruta: correção, enumeração completa, retrocesso e cancelamento."""
from concurrent.futures import CancelledError
from math import inf
from pathlib import Path
from random import Random
import sys
from time import monotonic, sleep
import tkinter as tk

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from mapas_movingai import Mapa
from roteamento import BuscaCancelada, dijkstra_heap, dijkstra_simples, forca_bruta, grafo_da_grade
from apoio import bfs_unitario, conferir_rota
from tabuleiro import RouteBoard


class VizinhosObservados(list):
    """Observa entradas em cada vértice sem alterar o algoritmo de produção."""
    def __init__(self, valores=()):
        super().__init__(valores)
        self.entradas = 0

    def __iter__(self):
        self.entradas += 1
        return super().__iter__()


# A primeira solução tem custo 3; o algoritmo precisa continuar até achar custo 1.
grafo = {"S": [("A", 1), ("T", 1)], "A": [("B", 1)],
         "B": [("T", 1)], "T": []}
assert forca_bruta(grafo, "S", "T") == (1, ["S", "T"])

# Depois da solução de custo 1, os quatro caminhos mais caros também são visitados.
grafo = {"S": VizinhosObservados([("T", 1), ("A", 2), ("B", 2)]),
         "A": VizinhosObservados([("B", 2), ("T", 2)]),
         "B": VizinhosObservados([("A", 2), ("T", 2)]),
         "T": VizinhosObservados()}
assert forca_bruta(grafo, "S", "T") == (1, ["S", "T"])
# Uma leitura na validação mais cinco chegadas ao destino durante a enumeração.
assert grafo["T"].entradas == 6
# A e B podem ser reutilizados em outras rotas depois do retrocesso.
assert grafo["A"].entradas == grafo["B"].entradas == 3

# Grades abertas: 12 rotas simples no 3x3 e 184 no 4x4, todas enumeradas.
for tamanho, total in ((3, 12), (4, 184)):
    bruto = grafo_da_grade(tuple("." * tamanho for _ in range(tamanho)))
    grafo = {u: VizinhosObservados(vizinhos) for u, vizinhos in bruto.items()}
    destino = (tamanho - 1, tamanho - 1)
    notificacoes = []
    custo, caminho = forca_bruta(grafo, (0, 0), destino, progresso=notificacoes.append)
    assert notificacoes[0] == (1, 0) and notificacoes[-1][1] == total
    assert custo == 2 * (tamanho - 1)
    conferir_rota(bruto, (0, 0), destino, custo, caminho)
    assert grafo[destino].entradas == total + 1
print("OK: continua após a primeira solução, sem podas por custo; 12 e 184 rotas enumeradas.")

consultas = 0
# Todas as disposições de obstáculos em 3x3 e todos os pares de casas livres.
for mascara in range(512):
    grade = tuple("".join("#" if mascara & (1 << (r * 3 + c)) else "."
                          for c in range(3)) for r in range(3))
    grafo = grafo_da_grade(grade)
    for a in grafo:
        for b in grafo:
            esperado, _ = bfs_unitario(grafo, a, b)
            for algoritmo in (forca_bruta, dijkstra_heap, dijkstra_simples):
                custo, rota = algoritmo(grafo, a, b)
                assert custo == esperado
                conferir_rota(grafo, a, b, custo, rota)
            consultas += 1

rng = Random(20261003)
for _ in range(100):
    n = rng.randint(2, 7)
    grafo = {u: [(v, rng.randint(0, 9)) for v in range(n)
                 if v != u and rng.random() < .35] for u in range(n)}
    for _ in range(4):
        a, b = rng.randrange(n), rng.randrange(n)
        custo, caminho = forca_bruta(grafo, a, b)
        assert custo == dijkstra_heap(grafo, a, b)[0]
        conferir_rota(grafo, a, b, custo, caminho)
        consultas += 1

# Rota mais profunda que o limite padrão de recursão do Python.
grafo = {u: [(v, 1) for v in (u - 1, u + 1) if 0 <= v < 1500] for u in range(1500)}
custo, caminho = forca_bruta(grafo, 0, 1499)
assert custo == 1499 and caminho == list(range(1500))
assert forca_bruta({0: [(0, 0)]}, 0, 0) == (0, [0])
assert forca_bruta({0: [], 1: []}, 0, 1) == (inf, [])
for invalido in ({0: [(1, -1)], 1: []}, {0: [(1, inf)], 1: []},
                 {0: [(1, float("nan"))], 1: []}, {0: [(1, 1)]}):
    try:
        forca_bruta(invalido, 0, 0)
    except ValueError:
        pass
    else:
        raise AssertionError("Entrada inválida aceita")

# Interromper depois de já encontrar uma rota não pode retornar um ótimo parcial.
grafo = grafo_da_grade(tuple("." * 6 for _ in range(6)))
grafo[(0, 0)].insert(0, ((5, 5), 1))
chamadas = [0]
def cancelar():
    chamadas[0] += 1
    return chamadas[0] > len(grafo) + 50
try:
    forca_bruta(grafo, (0, 0), (5, 5), cancelar)
except BuscaCancelada:
    pass
else:
    raise AssertionError("Busca interrompida retornou um resultado parcial")
print(f"OK: {consultas} consultas comparadas, custo zero, sem rota, 1.500 vértices e cancelamento.")

root = tk.Tk()
root.withdraw()
app = RouteBoard(root)
root.update_idletasks()

def esperar_busca():
    prazo = monotonic() + 5
    while app.search_future is not None:
        assert monotonic() < prazo
        root.update()
        sleep(.005)


def conferir_cancelamento(tarefa):
    try:
        tarefa.result(timeout=5)
    except (BuscaCancelada, CancelledError):
        return
    raise AssertionError("Busca em execução não foi cancelada")


try:
    assert set(app.algorithm_options) == {"dijkstra", "dijkstra_simples", "bfs", "forca_bruta"}
    assert all(not w.instate(["disabled"]) for w in app.algorithm_options.values())
    app.speed.set("Instantânea")
    for tamanho in (3, 4):
        app.map_choice.set(f"didatico-{tamanho}x{tamanho}.map")
        app.load_selected()
        assert (app.rows, app.cols) == (tamanho, tamanho)
        for chave, option in app.algorithm_options.items():
            option.invoke()
            assert app.algorithm.get() == chave and app.player == app.start
            app.play()
            esperar_busca()
            assert app.distance.get() == str(2 * (tamanho - 1))
            assert app.player == app.target
    # Regressão do relato: origem e destino lado a lado nos dois mapas pequenos.
    for tamanho in (3, 4):
        app.map_choice.set(f"didatico-{tamanho}x{tamanho}.map")
        app.load_selected()
        app.algorithm_options["forca_bruta"].invoke()
        app.set_editing(True)
        app.select_cell((0, 1))
        app.set_editing(False)
        app.play()
        esperar_busca()
        assert app.distance.get() == "1" and app.player == app.target
        assert "Rotas completas:" in app.search_details.get()
        assert app.search_progress is None
    print("OK: destino vizinho nos mapas 3x3/4x4; custo 1 e contadores finais.")

    # No Mini, a busca exaustiva continua; precisa mostrar atividade e ser cancelável.
    app.load_example()
    app.set_editing(True)
    app.select_cell((2, 3))
    app.set_editing(False)
    app.play()
    tarefa = app.search_future
    assert app.play_button.instate(["!disabled"])
    assert "Cancelar busca" in app.play_button.cget("text")
    prazo = monotonic() + 5
    while True:
        root.update()
        detalhe = app.search_details.get()
        estados = int(detalhe.splitlines()[0].split(": ")[1].replace(".", "")) if detalhe else 0
        if estados > 1:
            break
        assert monotonic() < prazo, "A enumeração não exibiu atividade"
        sleep(.01)
    assert app.search_future is tarefa and not tarefa.done()
    assert app.search_time.get().startswith("Decorrido:")
    assert app.distance.get() == "—" and not app.path
    # O mesmo botão usado para iniciar agora cancela a busca em andamento.
    app.play()
    conferir_cancelamento(tarefa)
    assert app.search_future is None and "cancelada" in app.status.get()
    assert app.progress.get() == "Busca interrompida"
    preservado = app.search_details.get()
    estados_cancelados = int(preservado.splitlines()[0].split(": ")[1].replace(".", ""))
    assert estados_cancelados >= estados
    root.update()
    assert app.search_details.get() == preservado  # Não recebe mais mensagens da tarefa antiga.
    assert app.distance.get() == "—" and not app.path
    print(f"OK: Mini com destino vizinho continua enumerando; {estados} estados exibidos; botão principal cancela.")

    app.algorithm_options["forca_bruta"].invoke()
    for grade, custo in (((".#.", "###", ".#."), "Sem rota"), ((".",), "0")):
        app.load_board(Mapa(grade, "caso-limite"))
        app.play()
        esperar_busca()
        assert app.distance.get() == custo and not app.running

    # A enumeração do 6x6 é longa: a janela processa eventos e permite reiniciar.
    mapa = Mapa(tuple("." * 6 for _ in range(6)), "cancelamento")
    app.load_board(mapa)
    app.play()
    tarefa, sinal = app.search_future, app.search_cancel
    prazo = monotonic() + 2
    while not tarefa.running():
        assert monotonic() < prazo
        root.update()
        sleep(.005)
    assert not tarefa.done()
    root.update()
    assert app.search_future is tarefa
    app.restart()
    assert sinal.is_set() and app.search_future is None
    assert app.distance.get() == "—" and app.player == app.start and not app.path
    conferir_cancelamento(tarefa)
    # Trocar de algoritmo cancela e não mistura o resultado da entrada anterior.
    app.play()
    tarefa, sinal = app.search_future, app.search_cancel
    app.algorithm_options["dijkstra"].invoke()
    assert sinal.is_set() and app.algorithm.get() == "dijkstra"
    conferir_cancelamento(tarefa)
    app.play()
    esperar_busca()
    assert app.distance.get() == "10" and app.player == app.target
    print("OK: quatro opções habilitadas, mapas didáticos, animação, sem rota, custo zero e cancelamento na interface.")
finally:
    app.close()
