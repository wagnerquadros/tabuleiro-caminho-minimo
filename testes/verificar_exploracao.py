"""Verifica o registro e a animação da exploração (casas examinadas, em amarelo)."""
from math import inf
from pathlib import Path
import sys
from time import monotonic, sleep
import tkinter as tk

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from mapas_movingai import ler_mapa
from tabuleiro import ALGORITMOS, BuscaAoVivo, RouteBoard, calcular_rota

consultas = 0
for nome in ("teste1.map", "teste5.map", "teste9.map"):
    grade = ler_mapa(BASE / "datasets/testes" / nome).grade
    for algoritmo in ALGORITMOS:
        if algoritmo == "forca_bruta" and nome != "teste5.map":
            continue 
        sem = calcular_rota(grade, (0, 0), (5, 9), algoritmo)
        com = calcular_rota(grade, (0, 0), (5, 9), algoritmo, explorar=True)
        assert len(sem) == 3 and len(com) == 4
        assert com[0] == sem[0], (nome, algoritmo)
        ordem = com[3]
        assert ordem[0] == (0, 0), "A origem é a primeira casa examinada"
        assert len(ordem) == len(set(ordem))
        assert all(grade[r][c] == "." for r, c in ordem)
        assert set(com[1][:-1]) <= set(ordem), (nome, algoritmo)
        consultas += 1

aberta = tuple("." * 30 for _ in range(30))
dijkstra = calcular_rota(aberta, (0, 0), (2, 2), "dijkstra", explorar=True)[3]
bmssp = calcular_rota(aberta, (0, 0), (2, 2), "bmssp", explorar=True)[3]
assert len(dijkstra) < 30 and len(bmssp) == 900
fechada = ("..#..", "..#..", "###..", ".....")
custo, _, _, ordem = calcular_rota(fechada, (0, 0), (3, 4), "bfs", explorar=True)
assert custo == inf and set(ordem) == {(0, 0), (0, 1), (1, 0), (1, 1)}
print(f"OK: registro da exploração em {consultas} buscas; resultado igual, sem repetições, BMSSP cobre tudo.")

root = tk.Tk()
root.withdraw()
app = RouteBoard(root)
root.update_idletasks()


def esperar():
    prazo = monotonic() + 20
    while app.search_future is not None or app.exploring or app.running:
        assert monotonic() < prazo, "A exploração ou a rota não terminou"
        root.update()
        sleep(.005)


try:
    app.show_exploration.set(True)
    app.speed.set("4×")
    app.map_choice.set("teste1.map")
    app.load_selected()
    app.algorithm_options["dijkstra"].invoke()
    app.play()
   
    busca = app.search_future
    assert isinstance(busca, BuscaAoVivo) and app.exploring
    assert "Cancelar" in app.play_button.cget("text")
    esperar()
    assert busca.processo.poll() is not None, "O processo auxiliar terminou"
    assert app.distance.get() == "14" and app.explored and app.player == app.target
    assert "Casas examinadas: 37" in app.search_details.get()
   
    assert app.search_time.get().startswith("Busca:") and "registro" not in app.search_time.get()
   
    app.show_exploration.set(False)
    app.play()
    assert app.path[0] == app.start and app.path[-1] == app.target
    esperar()
    assert app.distance.get() == "14" and app.player == app.target
    app.show_exploration.set(True)
   
    app.restart()
    assert not app.explored, "Reiniciar limpa as casas exploradas"
    custo, rota, tempo, ordem = calcular_rota(app.current_grid(), app.start, app.target,
                                               "dijkstra", explorar=True)
    app.apply_result((custo, rota, tempo, ordem))
    assert app.exploring and "Pular" in app.play_button.cget("text")
    app.play()
    assert not app.exploring and app.distance.get() == "14"
    esperar()
   
    app.restart()
    app.speed.set("Instantânea")
    app.algorithm_options["bmssp"].invoke()
    app.play()
    esperar()
    assert len(app.explored) == 46 and app.distance.get() == "14"

    app.restart()
    app.show_exploration.set(False)
    app.play()
    assert not isinstance(app.search_future, BuscaAoVivo)
    esperar()
    assert not app.explored and app.distance.get() == "14"

    app.load_example()
    app.show_exploration.set(True)
    app.target = (9, 2) 
    app.play()
    esperar()
    assert app.distance.get() == "Sem rota" and app.explored
    assert "Play" in app.play_button.cget("text")
  
    app.target = (10, 17)
    app.algorithm_options["forca_bruta"].invoke()
    app.play()
    busca = app.search_future
    prazo = monotonic() + 10
    while not app.explored:
        assert monotonic() < prazo, "Nenhuma casa chegou do processo auxiliar"
        root.update()
        sleep(.01)
    app.play()  # Cancela.
    assert app.search_future is None and not app.exploring
    busca.processo.wait(timeout=5)
    assert "cancelada" in app.status.get()
finally:
    app.close()
print("OK: exploração ao vivo em outro processo, tempo sem registro, pular, instantânea, desligado, sem rota e cancelamento.")
