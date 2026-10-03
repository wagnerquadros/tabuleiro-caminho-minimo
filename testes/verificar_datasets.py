"""Validação dos mapas reais, das duas buscas e dos controles ativos."""
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from time import monotonic, sleep
import tkinter as tk
from concurrent.futures import Future, CancelledError

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from mapas_movingai import ler_mapa
from roteamento import BuscaCancelada, grafo_da_grade, dijkstra_heap, dijkstra_simples
from apoio import bfs_unitario, conferir_rota
from tabuleiro import RouteBoard, default_walls

DATA = BASE / "datasets/artificial_random"


def rejeita(acao):
    try:
        acao()
    except ValueError:
        return
    raise AssertionError("Entrada inválida foi aceita")


manifesto = json.loads((DATA / "manifesto.json").read_text(encoding="utf-8"))
hashes = {a["arquivo"]: a["sha256"] for a in manifesto["arquivos_originais_sem_alteracao"]}
consultas = 0
for serie in (10, 20, 40):
    mapa = ler_mapa(DATA / f"random512-{serie}-0.map")
    assert mapa.linhas == mapa.colunas == 512
    assert mapa.sha256_original == hashes[mapa.nome]
    bruto = (DATA / mapa.nome).read_text().splitlines()[4:]
    assert len(mapa.paredes) == sum(sum(linha.count(s) for s in "@OTW") for linha in bruto)
    # Regiões pequenas servem só aos testes: o aplicativo carrega mapas completos.
    for altura, largura in ((3, 3), (4, 4), (5, 5), (12, 18)):
        r0, c0 = (512 - altura) // 2, (512 - largura) // 2
        grade = tuple(l[c0:c0 + largura] for l in mapa.grade[r0:r0 + altura])
        grafo = grafo_da_grade(grade)
        vertices = list(grafo)
        for a in vertices[:4]:
            for b in vertices[-4:]:
                esperado, _ = bfs_unitario(grafo, a, b)
                for algoritmo in (dijkstra_simples, dijkstra_heap):
                    custo, rota = algoritmo(grafo, a, b)
                    assert custo == esperado
                    conferir_rota(grafo, a, b, custo, rota)
                consultas += 1
    print(f"Random série {serie}: {512 * 512 - len(mapa.paredes)} livres.")

with TemporaryDirectory() as pasta:
    ruim = Path(pasta) / "ruim.map"
    textos = (
        "type octile\nheight 2\nwidth 3\nmap\n...\n..\n",
        "type octile\nheight 1\nwidth 1\nmap\nX\n",
        "type octile\nheight 1\nwidth 1\nmap\n@\n",
        "type octile\nheight 0\nwidth 1\nmap\n.\n",
        "type octile\nheight 1\nwidth 1048577\nmap\n.\n",
        "type octile\nwidth 1\nheight 1\nmap\n.\n",
    )
    for texto in textos:
        ruim.write_text(texto, encoding="utf-8")
        rejeita(lambda: ler_mapa(ruim))
    ruim.write_text("type octile\nheight 1\nwidth 7\nmap\n.GS@OTW\n", encoding="utf-8")
    assert ler_mapa(ruim).grade == ("...####",)

root = tk.Tk()
root.withdraw()
app = RouteBoard(root)
root.update_idletasks()
try:
    app.load_example()
    assert (app.rows, app.cols) == (12, 18) and app.loaded_map is None
    assert app.walls == default_walls() and app.start == (2, 2)
    assert app.target is None and not app.editing_enabled
    assert all(not option.instate(["disabled"]) for option in app.algorithm_options.values())
    destino = (11, 17)
    app.select_cell(destino)
    assert app.target is None
    app.set_editing(True)
    app.select_cell(destino)
    assert app.target == destino
    app.set_editing(False)
    app.speed.set("Instantânea")
    app.play()
    assert app.distance.get() == "24" and app.player == destino
    app.algorithm_options["dijkstra_simples"].invoke()
    assert app.algorithm.get() == "dijkstra_simples" and app.player == app.start
    app.play()
    assert app.search_future is not None
    prazo = monotonic() + 10
    while app.search_future is not None:
        assert monotonic() < prazo
        root.update()
        sleep(.005)
    assert app.distance.get() == "24" and app.player == destino
    app.algorithm_options["dijkstra"].invoke()
    assert app.algorithm.get() == "dijkstra" and app.player == app.start
    print("OK: opções de algoritmo, mesma origem, edição bloqueada e Mini com custo 24.")

    mapa = ler_mapa(DATA / "random512-20-0.map")
    app.load_board(mapa)
    assert len(app.canvas.find_all()) < 20
    # Trocar de algoritmo interrompe também uma busca real em mapa completo.
    app.algorithm_options["dijkstra_simples"].invoke()
    app.play()
    tarefa = app.search_future
    sinal = app.search_cancel
    prazo = monotonic() + 5
    while not tarefa.running():
        assert monotonic() < prazo
        root.update()
        sleep(.005)
    app.algorithm_options["dijkstra"].invoke()
    assert sinal.is_set() and app.search_future is None
    try:
        tarefa.result(timeout=5)
    except (BuscaCancelada, CancelledError):
        pass
    else:
        raise AssertionError("A busca antiga continuou após a troca de algoritmo")
    assert app.player == app.start and app.distance.get() == "—"
    print("OK: busca real por varredura cancelada ao trocar de algoritmo.")
    origem = app.player
    futuro = Future()
    futuro.set_running_or_notify_cancel()
    app.search_future = futuro
    app.search_job = root.after(100, app.poll_search)
    app.load_example()
    futuro.set_result((0, [origem], .01))
    root.update()
    assert app.search_future is None and app.search_job is None and app.target is None
    assert app.player == (2, 2) and app.loaded_map is None

    root.deiconify()
    for largura, altura in ((1160, 830), (920, 660)):
        root.geometry(f"{largura}x{altura}")
        root.update()
        app.load_example()
        root.update()
        for ponto in ((0, 0), (11, 17)):
            assert app.cell_at(*app.center(ponto)) == ponto
        for frame in (app.algorithm_section,):
            assert max(w.winfo_x() + w.winfo_width() for w in frame.winfo_children()) <= frame.winfo_width()
        controles = [w for w in root.winfo_children() if isinstance(w, tk.Frame)][1]
        assert max(w.winfo_x() + w.winfo_width() for w in controles.winfo_children()) <= controles.winfo_width()
finally:
    app.close()
print(f"OK: {consultas} consultas em regiões reais, ambas as versões corretas; conversão, Mini e interface.")
