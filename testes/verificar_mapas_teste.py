"""Verifica as dez instâncias fixas de benchmark e seu carregamento na interface."""
import hashlib
import json
from math import inf
from pathlib import Path
import sys
from time import monotonic, sleep
import tkinter as tk

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from mapas_movingai import ler_mapa
from roteamento import bfs, dijkstra_heap, dijkstra_simples, forca_bruta, grafo_da_grade
from apoio import bfs_unitario, conferir_rota
from tabuleiro import ALGORITMOS, RouteBoard

PASTA = BASE / "datasets/testes"
manifesto = json.loads((PASTA / "manifesto.json").read_text(encoding="utf-8"))
nomes = tuple(f"teste{i}.map" for i in range(1, 11))
assert manifesto["total_mapas"] == 10
assert (manifesto["linhas"], manifesto["colunas"]) == (6, 10)
assert manifesto["origem"] == [1, 1] and manifesto["destino"] == [6, 10]
assert tuple(r["arquivo"] for r in manifesto["mapas"]) == nomes
assert {p.name for p in PASTA.glob("*.map")} == set(nomes)
mapas = []
for registro in manifesto["mapas"]:
    arquivo = PASTA / registro["arquivo"]
    dados = arquivo.read_bytes()
    assert hashlib.sha256(dados).hexdigest() == registro["sha256"]
    mapa = ler_mapa(arquivo)
    assert (mapa.linhas, mapa.colunas) == (6, 10)
    assert mapa.livre((0, 0)) and mapa.livre((5, 9))
    assert len(mapa.paredes) == registro["bloqueadas"]
    assert registro["livres"] + registro["bloqueadas"] == 60
    assert round(100 * len(mapa.paredes) / 60, 4) == registro["percentual_bloqueadas"]
    grafo = grafo_da_grade(mapa.grade)
    assert registro["alcancavel"] is True and registro["rotas_simples"] > 0
    esperado = registro["custo_minimo"]
    assert isinstance(esperado, int) and esperado >= 14
    assert grafo[(5, 9)], "O destino está isolado"
    assert bfs_unitario(grafo, (0, 0), (5, 9))[0] != inf
    assert bfs_unitario(grafo, (0, 0), (5, 9))[0] == esperado
    for algoritmo in (bfs, dijkstra_heap, dijkstra_simples, forca_bruta):
        estatisticas = []
        inicio = monotonic()
        cancelar = lambda: monotonic() - inicio > 10
        if algoritmo is forca_bruta:
            custo, rota = algoritmo(grafo, (0, 0), (5, 9), cancelar, estatisticas.append)
            assert estatisticas[-1] == (registro["estados_forca_bruta"], registro["rotas_simples"])
        else:
            custo, rota = algoritmo(grafo, (0, 0), (5, 9), cancelar)
        assert custo == esperado, (registro["arquivo"], algoritmo.__name__)
        conferir_rota(grafo, (0, 0), (5, 9), custo, rota)
    mapas.append(mapa.grade)
assert len(set(mapas)) == 10, "Existem mapas duplicados"
assert manifesto["todos_alcancaveis"] is True
assert all(r["alcancavel"] for r in manifesto["mapas"])
print("OK: dez mapas distintos 6x10, hashes, todos os destinos alcançáveis e 40 buscas; custos e rotas simples conferidos.")

root = tk.Tk()
root.withdraw()
app = RouteBoard(root)
root.update_idletasks()
app.speed.set("Instantânea")

def esperar_busca():
    prazo = monotonic() + 10
    while app.search_future is not None:
        assert monotonic() < prazo, "Busca não terminou na interface"
        root.update()
        sleep(.005)

try:
    assert tuple(app.map_files)[:10] == nomes, "Mapas de teste fora da ordem numérica"
    for registro in manifesto["mapas"]:
        app.map_choice.set(registro["arquivo"])
        app.load_selected()
        assert (app.rows, app.cols) == (6, 10)
        assert app.start == (0, 0) and app.target == (5, 9)
        assert app.loaded_map.nome == registro["arquivo"]
        assert app.current_grid() == ler_mapa(PASTA / registro["arquivo"]).grade
        assert not app.editing_enabled
        esperado = str(registro["custo_minimo"])
        for chave in ALGORITMOS:
            app.algorithm_options[chave].invoke()
            assert app.player == app.start and app.target == (5, 9)
            app.play()
            esperar_busca()
            assert app.distance.get() == esperado, (registro["arquivo"], chave, app.distance.get())
            assert app.player == app.target and app.path
            assert app.path[0] == (0, 0) and app.path[-1] == (5, 9)
            if chave == "forca_bruta":
                rotas = f"{registro['rotas_simples']:,}".replace(",", ".")
                assert f"Rotas completas: {rotas}" in app.search_details.get()
finally:
    app.close()
print("OK: catálogo ordenado, carregamento dos dez mapas e 40 consultas pelos quatro algoritmos da interface.")
