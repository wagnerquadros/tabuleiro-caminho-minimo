"""Demonstração: executa as instâncias de teste no tabuleiro, com animação.

Execute: python -B demonstrar_testes.py [--algoritmos dijkstra bmssp]
         [--velocidade 2×] [--pausa 1.5] [--explorar]

Para cada mapa e algoritmo, a janela carrega o mapa com a origem e o destino
da instância, aperta Play, espera a busca e a animação terminarem e compara
o custo exibido com o custo esperado do manifesto. O título da janela mostra
o andamento; o terminal recebe uma linha por execução e o resumo final.
Fechar a janela encerra a demonstração.
"""

import argparse
import json
from pathlib import Path
import tkinter as tk

from tabuleiro import ALGORITMOS, RouteBoard

BASE = Path(__file__).resolve().parent


def instancias():
    """(arquivo .map, custo esperado) dos mapas de teste, na ordem em que serão exibidos."""
    manifesto = json.loads((BASE / "datasets/testes/manifesto.json").read_text(encoding="utf-8"))
    for registro in manifesto["mapas"]:
        yield registro["arquivo"], registro["custo_minimo"]


class Demonstracao:
    def __init__(self, root, app, roteiro, pausa):
        self.root, self.app = root, app
        self.roteiro = roteiro
        self.pausa_ms = int(pausa * 1000)
        self.indice = -1
        self.resultados = []

    def proximo(self):
        """Carrega o próximo par (mapa, algoritmo) e aperta Play."""
        self.indice += 1
        if self.indice == len(self.roteiro):
            self.encerrar()
            return
        arquivo, algoritmo, _ = self.roteiro[self.indice]
        app = self.app
        if app.loaded_map is None or app.loaded_map.nome != arquivo:
            app.map_choice.set(arquivo)
            app.load_selected()
        # Trocar o algoritmo devolve o personagem à origem da instância.
        app.algorithm.set(algoritmo)
        app.algorithm_changed()
        self.atualizar_titulo()
        app.play()
        self.root.after(100, self.esperar)

    def esperar(self):
        app = self.app
        if app.search_future is not None or app.running or app.exploring:
            self.root.after(100, self.esperar)
            return
        arquivo, algoritmo, esperado = self.roteiro[self.indice]
        obtido = app.distance.get()
        certo = obtido == str(esperado)
        self.resultados.append(certo)
        nome = ALGORITMOS[algoritmo][0]
        print(f"{'OK ' if certo else 'ERRO'} {arquivo:<18} {nome:<28} esperado {esperado:>5}  "
              f"obtido {obtido:>5}  {app.search_time.get()}", flush=True)
        app.status.set(f"{nome}: custo {obtido} ({'confere' if certo else 'DIFERENTE'} "
                       f"do esperado {esperado}). {app.search_time.get()}.")
        self.atualizar_titulo(certo)
        self.root.after(self.pausa_ms, self.proximo)

    def atualizar_titulo(self, certo=None):
        arquivo, algoritmo, esperado = self.roteiro[self.indice]
        marca = "" if certo is None else (" ✓" if certo else " ✗")
        self.root.title(f"Demonstração {self.indice + 1}/{len(self.roteiro)} · {arquivo} · "
                        f"{ALGORITMOS[algoritmo][0]} · esperado {esperado}{marca}")

    def encerrar(self):
        acertos = sum(self.resultados)
        texto = f"Demonstração concluída: {acertos} de {len(self.resultados)} custos conferem."
        print("\n" + texto, flush=True)
        self.root.title(texto)
        self.app.status.set(texto)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--algoritmos", nargs="+", choices=list(ALGORITMOS),
                        default=["dijkstra", "bmssp"])
    parser.add_argument("--velocidade", choices=("1×", "2×", "4×", "Instantânea"), default="2×")
    parser.add_argument("--explorar", action="store_true",
                        help="mostra a exploração de cada algoritmo, em amarelo, antes da rota")
    parser.add_argument("--pausa", type=float, default=1.5,
                        help="segundos entre uma execução e a próxima")
    args = parser.parse_args()

    roteiro = [(arquivo, algoritmo, esperado)
               for arquivo, esperado in instancias()
               for algoritmo in args.algoritmos]
    root = tk.Tk()
    app = RouteBoard(root)
    app.speed.set(args.velocidade)
    app.show_exploration.set(args.explorar)
    demonstracao = Demonstracao(root, app, roteiro, args.pausa)
    print(f"{len(roteiro)} execuções: mapas de teste, algoritmos {', '.join(args.algoritmos)}.\n")
    root.after(500, demonstracao.proximo)
    root.mainloop()


if __name__ == "__main__":
    main()
