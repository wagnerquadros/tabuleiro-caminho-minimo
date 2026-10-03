"""Verifica mapas reais, zoom, animação longa e permanência dos objetos do Canvas.
Execute na raiz: python -B testes/verificar_zoom_animacao.py
"""
from pathlib import Path
import sys, json
from math import inf
from time import perf_counter
import tkinter as tk
from concurrent.futures import Future

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from mapas_movingai import Mapa, ler_mapa
from roteamento import grafo_da_grade, dijkstra_heap
from apoio import bfs_unitario
from tabuleiro import RouteBoard, duracao_animacao, livre_mais_proxima

DATA = BASE / "datasets/artificial_random"
manifesto = json.loads((DATA / "manifesto_random_zip.json").read_text(encoding="utf-8"))
assert manifesto["total_mapas"] == 70
for registro in manifesto["mapas"]:
    mapa = ler_mapa(DATA / registro["arquivo"])
    assert mapa.sha256_original == registro["sha256"]
    assert (mapa.linhas, mapa.colunas) == (512, 512)
    assert sum(l.count(".") for l in mapa.grade) == registro["livres"]
    for canto in ((0,0), (511,511)):
        ponto = livre_mais_proxima(mapa, canto)
        assert mapa.livre(ponto)
        if mapa.livre(canto):
            assert ponto == canto
        else:
            distancia = abs(ponto[0]-canto[0]) + abs(ponto[1]-canto[1])
            assert all(abs(r-canto[0]) + abs(c-canto[1]) >= distancia
                       for r,linha in enumerate(mapa.grade) for c,s in enumerate(linha) if s == ".")
print("OK: 70 mapas, hashes, dimensões, conversão e células livres mais próximas dos cantos.")

for serie in (10,20,40):
    mapa = ler_mapa(DATA / f"random512-{serie}-0.map")
    origem = livre_mais_proxima(mapa,(0,0))
    destino = livre_mais_proxima(mapa,(511,511))
    grafo = grafo_da_grade(mapa.grade)
    custo, caminho = dijkstra_heap(grafo,origem,destino)
    referencia, _ = bfs_unitario(grafo,origem,destino)
    assert custo == referencia
    if custo != inf:
        assert len(caminho)-1 == custo and caminho[0]==origem and caminho[-1]==destino
        assert all(mapa.livre(p) for p in caminho)
        assert all(abs(a[0]-b[0])+abs(a[1]-b[1])==1 for a,b in zip(caminho,caminho[1:]))
    print(f"OK: mapa completo série {serie}, custo Dijkstra/BFS = {custo}, pontos {origem} → {destino}.")

assert duracao_animacao(0)==0
assert duracao_animacao(10)==1.2
assert duracao_animacao(10_000)==8
assert duracao_animacao(10_000,"2×")==4
assert duracao_animacao(10_000,"4×")==2
assert duracao_animacao(10_000,"Instantânea")==0
root = tk.Tk()
app = RouteBoard(root)
root.update()

def descartar_callback():
    if app.job is not None:
        root.after_cancel(app.job)
        app.job=None

def ponto_na_tela(ponto):
    x,y=app.center(ponto)
    return x-app.canvas.canvasx(0), y-app.canvas.canvasy(0)

try:
    mapa=ler_mapa(DATA/"random512-20-0.map")
    app.load_board(mapa)
    root.update()
    assert app.start==livre_mais_proxima(mapa,(0,0))
    assert app.target==livre_mais_proxima(mapa,(511,511))
    assert app.canvas.find_withtag("map") and len(app.canvas.find_withtag("map"))==1
    assert sum(nome.startswith("random512-") for nome in app.map_files)==70
    assert {"didatico-3x3.map", "didatico-4x4.map"} <= app.map_files.keys()
    origem,destino=app.start,app.target
    original=app.current_grid()
    for tamanho in ((1160,830),(920,660)):
        root.geometry(f"{tamanho[0]}x{tamanho[1]}")
        root.update()
        app.fit_map()
        assert app.cell_at(*ponto_na_tela(origem))==origem
        assert app.cell_at(*ponto_na_tela(destino))==destino
        for factor in (1.5,1.5,4,4):
            app.change_zoom(factor)
            root.update_idletasks()
        assert app.zoom>1 and app.cell_size<=64.0001
        app.focus_cell((256,256))
        root.update_idletasks()
        assert app.cell_at(*ponto_na_tela((256,256)))==(256,256)
        assert app.canvas.canvasx(0)>0 and app.canvas.canvasy(0)>0
        assert len(app.canvas.find_withtag("map"))<12_500
        if app.map_image is not None:
            assert app.map_image.width()<=app.canvas.winfo_width()+1
            assert app.map_image.height()<=app.canvas.winfo_height()+1
        # Clique após zoom e rolagem precisa selecionar a célula correta.
        livre=next((r,c) for r in range(245,266) for c in range(245,266) if mapa.livre((r,c)))
        app.focus_cell(livre)
        root.update_idletasks()
        x,y=ponto_na_tela(livre)
        from types import SimpleNamespace
        app.set_editing(True)
        app.on_click(SimpleNamespace(x=x,y=y))
        assert app.target==livre
        assert app.current_grid()==original
        app.load_board(mapa)
        root.update()
        zoom_bar = app.canvas.master.master.winfo_children()[1]
        assert max(w.winfo_x()+w.winfo_width() for w in zoom_bar.winfo_children()) <= zoom_bar.winfo_width(), "Controles de zoom cortados"
        # Barras de arquivos e controles de zoom cabem na largura mínima.
        for frame in [w for w in root.winfo_children() if isinstance(w,tk.Frame)][:3]:
            assert max((w.winfo_x()+w.winfo_width() for w in frame.winfo_children()),default=0)<=frame.winfo_width()
    print("OK: zoom/rolagem, seleção correta, limites de imagem e janelas 1160×830 e 920×660.")

    # Rota longa verdadeira, em grade vazia de 512×512, sem aguardar oito segundos.
    aberto=Mapa(tuple("."*512 for _ in range(512)),"teste-aberto")
    app.load_board(aberto)
    caminho=[(0,c) for c in range(512)]+[(r,511) for r in range(1,512)]
    app.apply_result((1022,caminho,.001))
    descartar_callback()
    ids=app.canvas.find_all()
    linha=app.canvas.find_withtag("route")
    coords=app.canvas.coords(linha[0])
    personagem=app.player_item
    inicio=perf_counter()
    for _ in range(400):
        app.advance_animation(.01)
    tempo_quadros=perf_counter()-inicio
    assert app.canvas.find_all()==ids and app.player_item==personagem
    assert app.canvas.coords(linha[0])==coords
    assert abs(app.path_index-511)<=1 and app.player==caminho[app.path_index]
    # Pausar preserva o ponto exato e a duração restante.
    app.animation_clock=perf_counter()
    app.play()
    assert app.paused and not app.running
    pos=app.visual_player
    root.update()
    assert app.visual_player==pos
    app.play()
    assert app.running and not app.paused
    descartar_callback()
    app.change_zoom(4)
    assert app.running and app.path==caminho and app.distance.get()=="1022"
    app.advance_animation(4)
    assert app.player==app.target and not app.running
    assert app.progress.get()=="1022 de 1022 movimentos"
    print(f"OK: 1.022 movimentos em 8 s programados; 400 atualizações em {tempo_quadros*1000:.1f} ms; objetos estáveis.")
    app.restart()
    assert app.player==app.start and not app.path
    app.speed.set("Instantânea")
    app.apply_result((1022,caminho,.001))
    assert app.player==app.target and not app.running
    app.restart()
    app.speed.set("1×")
    app.apply_result((1022,caminho,.001))
    app.play()
    assert app.paused
    app.finish_route()
    assert app.player==app.target and not app.paused and app.job is None
    print("OK: pausa, continuação, zoom durante o percurso, reinício, instantânea e concluir animação.")

    fechado=Mapa(("#..",".#.","..#"),"cantos-bloqueados")
    app.load_board(fechado)
    assert app.start==(0,1) and app.target==(1,2)
    assert app.current_grid()==fechado.grade and not app.map_edited
    assert "bloqueada" in app.status.get() and "bloqueado" in app.status.get()
    app.load_board(fechado,(2,0),(0,2))
    assert app.start==(2,0) and app.target==(0,2)
    isolado=Mapa((".#.","###",".#."),"sem-rota")
    app.load_board(isolado)
    app.play()
    assert app.distance.get()=="Sem rota" and not app.running
    unico=Mapa((".",),"um-ponto")
    app.load_board(unico)
    app.play()
    assert app.distance.get()=="0" and app.player==app.target
    futuro=Future()
    futuro.set_running_or_notify_cancel()
    app.search_future=futuro
    app.search_job=root.after(100,app.poll_search)
    app.load_board(aberto)
    futuro.set_result((0,[(0,0)],.001))
    root.update()
    assert app.search_future is None and app.target==(511,511)
    print("OK: cantos bloqueados sem alterar mapa, pontos explícitos, sem rota, custo zero e busca obsoleta.")
finally:
    app.close()
print("Todos os testes de zoom e animação passaram.")
