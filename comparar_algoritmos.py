import argparse
import csv
import gc
import json
import os
import platform
import statistics
import sys
import tracemalloc
from datetime import datetime
from math import inf
from pathlib import Path
from time import perf_counter

from mapas_movingai import ler_mapa
from roteamento import BuscaCancelada, bfs, bmssp, dijkstra_heap, forca_bruta, grafo_da_grade

BASE = Path(__file__).resolve().parent


def dijkstra_completo(grafo, origem, destino, estatisticas=None):
    return dijkstra_heap(grafo, origem, destino, parar_no_destino=False,
                         estatisticas=estatisticas)


class LimiteExcedido(Exception):
    """A força bruta passou do limite de tempo sem concluir a enumeração."""

    def __init__(self, estados, rotas, decorrido):
        super().__init__(f"limite de tempo após {decorrido:.1f} s")
        self.estados, self.rotas, self.decorrido = estados, rotas, decorrido


class Prazo:
    """Função de cancelamento barata: consulta o relógio só a cada 4.096 chamadas."""

    def __init__(self, segundos):
        self.fim = perf_counter() + segundos
        self.chamadas = 0

    def __call__(self):
        self.chamadas += 1
        return not self.chamadas & 4095 and perf_counter() > self.fim


class ForcaBrutaLimitada:
    """Força bruta com limite de tempo, na mesma assinatura dos outros algoritmos."""

    __name__ = "forca_bruta"

    def __init__(self, limite):
        self.limite = limite

    def __call__(self, grafo, origem, destino, estatisticas=None):
        contagem = [(0, 0)]
        inicio = perf_counter()
        try:
            resultado = forca_bruta(grafo, origem, destino, Prazo(self.limite), contagem.append)
        except BuscaCancelada:
            estados, rotas = contagem[-1]
            raise LimiteExcedido(estados, rotas, perf_counter() - inicio) from None
        if estatisticas is not None:
            estatisticas["estados"], estatisticas["rotas"] = contagem[-1]
        return resultado

ALGORITMOS = {
    "dijkstra_heap": (dijkstra_heap, False),
    "dijkstra_completo": (dijkstra_completo, True),
    "bmssp": (bmssp, True),
    "bfs": (bfs, False),
    "forca_bruta": (None, False),
}
COM_ESTATISTICAS = ("bmssp", "dijkstra_heap", "dijkstra_completo", "forca_bruta")


class GrafoContado(dict):
    """Conta cada consulta à lista de adjacência: grafo[u]."""

    consultas = 0

    def __getitem__(self, vertice):
        self.consultas += 1
        return dict.__getitem__(self, vertice)


def livre_mais_proxima(grade, canto):
    """Mesma regra da interface: Manhattan, depois linha e coluna."""
    livres = ((abs(r - canto[0]) + abs(c - canto[1]), r, c)
              for r, linha in enumerate(grade) for c, x in enumerate(linha) if x == ".")
    _, r, c = min(livres)
    return r, c


def instancias(tamanhos, series):
    pasta = BASE / "datasets/testes"
    for i in range(1, 11):
        grade = ler_mapa(pasta / f"teste{i}.map").grade
        yield "testes", f"teste{i}", grade, (0, 0), (5, 9), None
    for n in tamanhos:
        yield ("aberta", f"aberta-{n}x{n}", tuple("." * n for _ in range(n)),
               (0, 0), (n - 1, n - 1), None)
    for serie in series:
        mapa = ler_mapa(BASE / f"datasets/artificial_random/random512-{serie}-0.map")
        for n in tamanhos:
            grade = tuple(linha[:n] for linha in mapa.grade[:n])
            if not any("." in linha for linha in grade):
                continue
            origem = livre_mais_proxima(grade, (0, 0))
            destino = livre_mais_proxima(grade, (n - 1, n - 1))
            yield f"random-{serie}", f"random512-{serie}-0[{n}x{n}]", grade, origem, destino, None

def medir(funcao, grafo, origem, destino, repeticoes):
    """Mede as repetições. Se o limite de tempo for atingido, para e devolve o erro."""
    tempos = []
    for _ in range(repeticoes):
        gc.collect()
        inicio = perf_counter()
        try:
            resultado = funcao(grafo, origem, destino)
        except LimiteExcedido as limite:
            # As repetições seguintes também estourariam: não vale esperar por elas.
            tempos.append(perf_counter() - inicio)
            return None, tempos, limite
        tempos.append(perf_counter() - inicio)
    return resultado, tempos, None


def quartis(tempos):
    """Q1 e Q3 por interpolação dentro dos dados; com uma repetição, não há quartis."""
    if len(tempos) < 2:
        return None, None
    q1, _, q3 = statistics.quantiles(tempos, n=4, method="inclusive")
    return q1, q3


def esforco(funcao, grafo, origem, destino):
    """Consultas à adjacência e pico de memória Python, em execuções à parte.

    Devolve ("", "") se uma dessas execuções estourar o limite de tempo.
    """
    contado = GrafoContado(grafo)
    try:
        funcao(contado, origem, destino)
        gc.collect()
        tracemalloc.start()
        funcao(grafo, origem, destino)
        _, pico = tracemalloc.get_traced_memory()
    except LimiteExcedido:
        return "", ""
    finally:
        tracemalloc.stop()
    return contado.consultas, round(pico / 1024, 1)


def situacao_de(custo, limite):
    if limite is not None:
        return "limite_de_tempo"
    return "sem_caminho" if custo == inf else "otimo"


def ambiente(args, saida, inicio):
    """Registro do ambiente para reproduzir a coleta."""
    return {
        "csv": saida.name,
        "inicio": inicio.isoformat(timespec="seconds"),
        "fim": None,
        "python": platform.python_version(),
        "implementacao": platform.python_implementation(),
        "sistema": platform.platform(),
        "processador": platform.processor(),
        "arquitetura": platform.machine(),
        "nucleos_logicos": os.cpu_count(),
        "repeticoes": args.repeticoes,
        "algoritmos": args.algoritmos,
        "tamanhos": args.tamanhos,
        "series": args.series,
        "limite_forca_bruta_s": args.limite_forca_bruta if "forca_bruta" in args.algoritmos else None,
        "comando": " ".join(sys.argv),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repeticoes", type=int, default=5)
    parser.add_argument("--tamanhos", type=int, nargs="+", default=[16, 32, 64, 128, 256, 512])
    parser.add_argument("--series", type=int, nargs="+", default=[10, 20, 30, 40])
    parser.add_argument("--algoritmos", nargs="+", choices=list(ALGORITMOS),
                        default=["dijkstra_heap", "dijkstra_completo", "bmssp"])
    parser.add_argument("--limite-forca-bruta", type=float, default=60.0,
                        help="segundos por execução da força bruta (padrão: 60)")
    parser.add_argument("--saida", type=Path, default=None)
    args = parser.parse_args()

    # Execução medida com o limite; execuções de esforço (contagem e memória,
    # mais lentas) com folga, para não perder a medida por pouco.
    funcoes = {nome: funcao for nome, (funcao, _) in ALGORITMOS.items()}
    funcoes_esforco = dict(funcoes)
    funcoes["forca_bruta"] = ForcaBrutaLimitada(args.limite_forca_bruta)
    funcoes_esforco["forca_bruta"] = ForcaBrutaLimitada(3 * args.limite_forca_bruta)

    inicio = datetime.now()
    saida = args.saida or BASE / "outputs" / f"comparacao_{inicio:%Y%m%d-%H%M%S}.csv"
    saida.parent.mkdir(parents=True, exist_ok=True)
    registro_ambiente = ambiente(args, saida, inicio)
    arquivo_ambiente = saida.with_suffix(".json")
    arquivo_ambiente.write_text(json.dumps(registro_ambiente, ensure_ascii=False, indent=2),
                                encoding="utf-8")
    print(f"Python {platform.python_version()} · {platform.platform()} · {platform.processor()}")
    print(f"Repetições por medida: {args.repeticoes}; tempo = mediana."
          + (f" Força bruta: limite de {args.limite_forca_bruta:g} s." if "forca_bruta" in args.algoritmos else "")
          + "\n")

    colunas = ["familia", "instancia", "linhas", "colunas", "livres", "bloqueadas_pct",
               "arestas", "origem", "destino", "algoritmo", "todas_as_casas", "situacao", "custo",
               "custo_esperado", "movimentos_rota", "repeticoes_concluidas",
               "tempo_mediano_ms", "tempo_q1_ms", "tempo_q3_ms", "tempo_iqr_ms",
               "tempo_min_ms", "tempo_max_ms", "consultas_adjacencia", "pico_memoria_kib",
               "dijkstra_retiradas", "dijkstra_descartadas", "dijkstra_expandidas",
               "bmssp_k", "bmssp_t", "bmssp_niveis", "bmssp_chamadas", "bmssp_casos_base",
               "forca_estados", "forca_rotas"]
    print(f"{'instância':<26}{'V':>8}  " + "".join(f"{nome:>20}" for nome in args.algoritmos)
          + f"{'BMSSP/Dij.':>12}")
    divergencias = incompletas = total = 0
    with saida.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas)
        escritor.writeheader()
        for familia, nome, grade, origem, destino, esperado in instancias(
                args.tamanhos, args.series):
            total += 1
            grafo = grafo_da_grade(grade)
            celulas = len(grade) * len(grade[0])
            arestas = sum(map(len, grafo.values()))
            custos, medianas = set(), {}
            for algoritmo in args.algoritmos:
                funcao, todas = funcoes[algoritmo], ALGORITMOS[algoritmo][1]
                resultado, tempos, limite = medir(funcao, grafo, origem, destino, args.repeticoes)
                custo, rota = resultado if resultado is not None else (None, [])
                situacao = situacao_de(custo, limite)
                estatisticas, consultas, pico = {}, "", ""
                if limite is None:
                    consultas, pico = esforco(funcoes_esforco[algoritmo], grafo, origem, destino)
                    # Contadores próprios de cada algoritmo, em uma execução à parte.
                    if algoritmo in COM_ESTATISTICAS:
                        try:
                            funcoes_esforco[algoritmo](grafo, origem, destino, estatisticas=estatisticas)
                        except LimiteExcedido:
                            pass
                    custos.add(custo)
                else:
                    incompletas += 1
                    estatisticas = {"estados": limite.estados, "rotas": limite.rotas}
                medianas[algoritmo] = statistics.median(tempos) if limite is None else None
                q1, q3 = quartis(tempos) if limite is None else (None, None)
                ms = lambda valor: "" if valor is None else round(1000 * valor, 4)
                escritor.writerow({
                    "familia": familia, "instancia": nome, "linhas": len(grade),
                    "colunas": len(grade[0]), "livres": len(grafo),
                    "bloqueadas_pct": round(100 * (celulas - len(grafo)) / celulas, 2),
                    "arestas": arestas, "origem": origem, "destino": destino,
                    "algoritmo": algoritmo, "todas_as_casas": todas, "situacao": situacao,
                    "custo": "" if custo is None else ("inf" if custo == inf else custo),
                    "custo_esperado": "" if esperado is None else esperado,
                    "movimentos_rota": max(len(rota) - 1, 0) if rota else "",
                    "repeticoes_concluidas": len(tempos) - (limite is not None),
                    "tempo_mediano_ms": ms(medianas[algoritmo]),
                    "tempo_q1_ms": ms(q1), "tempo_q3_ms": ms(q3),
                    "tempo_iqr_ms": "" if q1 is None else round(1000 * (q3 - q1), 4),
                    # Com limite, o "tempo" é quanto durou até a interrupção.
                    "tempo_min_ms": ms(min(tempos)), "tempo_max_ms": ms(max(tempos)),
                    "consultas_adjacencia": consultas, "pico_memoria_kib": pico,
                    "dijkstra_retiradas": estatisticas.get("retiradas", ""),
                    "dijkstra_descartadas": estatisticas.get("descartadas", ""),
                    "dijkstra_expandidas": estatisticas.get("expandidas", ""),
                    "bmssp_k": estatisticas.get("k", ""), "bmssp_t": estatisticas.get("t", ""),
                    "bmssp_niveis": estatisticas.get("niveis", ""),
                    "bmssp_chamadas": estatisticas.get("chamadas", ""),
                    "bmssp_casos_base": estatisticas.get("casos_base", ""),
                    "forca_estados": estatisticas.get("estados", ""),
                    "forca_rotas": estatisticas.get("rotas", ""),
                })
            # Só execuções concluídas entram na conferência de custos iguais.
            if esperado is not None and custos:
                custos.add(esperado)
            if len(custos) > 1:
                divergencias += 1
            razao = ""
            if medianas.get("bmssp") and medianas.get("dijkstra_completo"):
                razao = f"{medianas['bmssp'] / max(medianas['dijkstra_completo'], 1e-9):>11.2f}×"
            celulas_texto = "".join(
                f"{'> ' + format(args.limite_forca_bruta, 'g') + ' s (limite)':>20}"
                if medianas[a] is None else f"{1000 * medianas[a]:>17.3f} ms"
                for a in args.algoritmos)
            print(f"{nome:<26}{len(grafo):>8}  " + celulas_texto + f"{razao:>12}"
                  + ("  CUSTOS DIFERENTES (ou ≠ esperado)" if len(custos) > 1 else ""),
                  flush=True)

    registro_ambiente.update(fim=datetime.now().isoformat(timespec="seconds"),
                             instancias=total, execucoes_incompletas=incompletas,
                             divergencias=divergencias)
    arquivo_ambiente.write_text(json.dumps(registro_ambiente, ensure_ascii=False, indent=2),
                                encoding="utf-8")
    print(f"\nResultados: {saida}\nAmbiente: {arquivo_ambiente}")
    if incompletas:
        print(f"{incompletas} execuções atingiram o limite de tempo e ficaram incompletas.")
    if divergencias:
        print(f"ATENÇÃO: {divergencias} instâncias com custos diferentes entre algoritmos.")
        sys.exit(1)
    print("Todas as execuções concluídas obtiveram o mesmo custo em cada instância.")


if __name__ == "__main__":
    main()
