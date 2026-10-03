"""Validação dos arquivos reais, conversão e integração com a janela."""
import json
from math import inf
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from time import monotonic, sleep
import tkinter as tk
from concurrent.futures import Future

RAIZ = Path(__file__).resolve().parents[1]
BASE = RAIZ if (RAIZ / "tabuleiro.py").exists() else RAIZ / "outputs"
sys.path.insert(0, str(BASE))
from mapas_movingai import (ler_mapa, recortar, ler_cenarios, pontos_locais,
                           ler_instancia, salvar_instancia)
from roteamento import grafo_da_grade, dijkstra_heap, bfs_unitario
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
for densidade in (10, 20, 40):
    mapa = ler_mapa(DATA / f"random512-{densidade}-0.map")
    assert mapa.linhas == mapa.colunas == 512
    assert mapa.sha256_original == hashes[mapa.nome]
    bruto = (DATA / mapa.nome).read_text().splitlines()[4:]
    assert len(mapa.paredes) == sum(sum(linha.count(s) for s in "@OTW") for linha in bruto)
    cenarios = ler_cenarios(DATA / f"{mapa.nome}.scen", mapa)
    assert len(cenarios) > 100
    for altura, largura in [(3, 3), (4, 4), (5, 5), (12, 18)]:
        r0, c0 = (512-altura)//2, (512-largura)//2
        pequeno = recortar(mapa, r0, c0, altura, largura)
        assert pequeno.grade == tuple("".join("." if s in ".GS" else "#" for s in l[c0:c0+largura])
                                      for l in bruto[r0:r0+altura])
        grafo = grafo_da_grade(pequeno.grade)
        vertices = list(grafo)
        for a in vertices[:4]:
            for b in vertices[-4:]:
                custo, rota = dijkstra_heap(grafo, a, b)
                esperado, _ = bfs_unitario(grafo, a, b)
                assert custo == esperado
                if custo != inf:
                    assert rota[0] == a and rota[-1] == b and len(rota) == custo + 1
                    assert all(pequeno.livre(p) for p in rota)
                    assert all(abs(a[0]-b[0])+abs(a[1]-b[1]) == 1 for a,b in zip(rota,rota[1:]))
                consultas += 1
    print(f"Random {densidade}%: {512*512-len(mapa.paredes)} livres; {len(cenarios)} cenários.")

with TemporaryDirectory() as pasta:
    pasta = Path(pasta)
    pequeno = recortar(ler_mapa(DATA / "random512-20-0.map"), 7, 11, 12, 18)
    pequeno2 = recortar(pequeno, 1, 2, 5, 6)
    assert pequeno2.deslocamento == (8, 13)
    pontos = [(r,c) for r in range(pequeno2.linhas) for c in range(pequeno2.colunas) if pequeno2.livre((r,c))]
    arquivo = pasta / "instancia.json"
    salvar_instancia(arquivo, pequeno2, pequeno2.grade, pontos[0], pontos[-1])
    lido, a, b = ler_instancia(arquivo)
    assert (lido, a, b) == (pequeno2, pontos[0], pontos[-1])
    assert not json.loads(arquivo.read_text(encoding="utf-8"))["editado"]
    modificado = list(pequeno2.grade)
    modificado[0] = "#" + modificado[0][1:]
    # Escolhe pontos que não coincidem com a edição.
    outros = [p for p in pontos if p != (0,0)]
    salvar_instancia(arquivo, pequeno2, modificado, outros[0], outros[-1])
    mod, _, _ = ler_instancia(arquivo)
    assert mod.alterado == (tuple(modificado) != pequeno2.grade)
    rejeita(lambda: recortar(pequeno, -1, 0, 2, 2))
    rejeita(lambda: recortar(pequeno, 10, 10, 12, 12))
    ruim = pasta / "ruim.map"
    for texto in ["type octile\nheight 2\nwidth 3\nmap\n...\n..\n",
                  "type octile\nheight 1\nwidth 1\nmap\nX\n",
                  "type octile\nheight 1\nwidth 1\nmap\n@\n"]:
        ruim.write_text(texto)
        rejeita(lambda: ler_mapa(ruim))
    ruim.write_text("type octile\nheight 1\nwidth 7\nmap\n.GS@OTW\n")
    assert ler_mapa(ruim).grade == ("...####",)
    ruim.write_text("type octile\nheight 1\nwidth 1\nmap\n.\n")
    um = ler_mapa(ruim)
    rejeita(lambda: recortar(um, 0, 0, 2, 2))
    salvar_instancia(arquivo, um, um.grade, (0,0), None)
    assert ler_instancia(arquivo)[2] is None
    obj = json.loads(arquivo.read_text(encoding="utf-8"))
    obj["origem"] = [2,2]
    arquivo.write_text(json.dumps(obj))
    rejeita(lambda: ler_instancia(arquivo))

root = tk.Tk()
root.withdraw()
app = RouteBoard(root)
root.update_idletasks()
try:
    app.load_example()
    assert (app.rows, app.cols) == (12,18) and app.loaded_map is None
    assert app.walls == default_walls() and app.start == (2,2)
    assert app.target is None and app.player not in app.walls
    mapa = ler_mapa(DATA / "random512-20-0.map")
    cenario = ler_cenarios(DATA / f"{mapa.nome}.scen", mapa)[1]
    app.load_board(mapa)
    assert len(app.canvas.find_all()) < 20  # Mapa completo é uma imagem, não 262.144 quadrados.
    app.apply_scenario(cenario)
    assert app.start == cenario.origem and app.target == cenario.destino
    # Neste caso real, o custo octile é 2,414... e o ortogonal é 3.
    assert cenario.custo_octile < 3
    app.play()
    assert app.search_future is not None
    prazo = monotonic() + 30
    while app.search_future is not None:
        assert monotonic() < prazo
        root.update()
        sleep(.01)
    assert app.distance.get() == "3" and app.path[-1] == cenario.destino
    app.restart()
    app.load_board(recortar(mapa, 0, 0, 12, 18))
    rejeita(lambda: app.apply_scenario(cenario))
    origem = app.player
    # Uma tarefa antiga não pode reposicionar os pontos depois de outro mapa ser carregado.
    future = Future()
    future.set_running_or_notify_cancel()
    app.search_future = future
    app.search_job = root.after(100, app.poll_search)
    app.restore()
    future.set_result((0,[origem],.01))
    root.update()
    assert app.search_future is None and app.search_job is None and app.target is None
    assert app.player == (2,2) and app.loaded_map is None
    root.deiconify()
    for largura, altura in [(1160,830),(920,660)]:
        root.geometry(f"{largura}x{altura}")
        root.update()
        app.load_example()
        root.update()
        for ponto in ((0,0),(11,17)):
            assert app.cell_at(*app.center(ponto)) == ponto
        controles = [w for w in root.winfo_children() if isinstance(w,tk.Frame)][1]
        assert max(w.winfo_x()+w.winfo_width() for w in controles.winfo_children()) <= controles.winfo_width(), "Barra de arquivos cortada"
finally:
    app.close()
print(f"OK: {consultas} consultas em recortes reais; conversão, validação, cenários, exportação, imagem e busca assíncrona.")
