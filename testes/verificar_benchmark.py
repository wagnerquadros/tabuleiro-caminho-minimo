"""Verifica o CSV e o registro de ambiente de comparar_algoritmos.py em uma execução curta."""
import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile

BASE = Path(__file__).resolve().parents[1]
manifesto = json.loads((BASE / "datasets/testes/manifesto.json").read_text(encoding="utf-8"))
esperado = {r["arquivo"][:-4]: r for r in manifesto["mapas"]}

with tempfile.TemporaryDirectory() as pasta:
    saida = Path(pasta) / "resultado.csv"
    processo = subprocess.run(
        [sys.executable, "-B", str(BASE / "comparar_algoritmos.py"), "--repeticoes", "3",
         "--tamanhos", "4", "8", "--series", "20",
         "--algoritmos", "dijkstra_heap", "dijkstra_completo", "bmssp", "forca_bruta",
         "--limite-forca-bruta", "2", "--saida", str(saida)],
        cwd=BASE, capture_output=True, text=True, encoding="utf-8", timeout=300)
    assert processo.returncode == 0, processo.stdout + processo.stderr
    linhas = list(csv.DictReader(saida.open(encoding="utf-8")))
    ambiente = json.loads(saida.with_suffix(".json").read_text(encoding="utf-8"))

por_chave = {(l["instancia"], l["algoritmo"]): l for l in linhas}
assert len(linhas) == 14 * 4

for (instancia, algoritmo), linha in por_chave.items():
    if (instancia, algoritmo) == ("aberta-8x8", "forca_bruta"):
        continue
    assert linha["situacao"] == "otimo", (instancia, algoritmo, linha["situacao"])
    assert linha["repeticoes_concluidas"] == "3"

    q1, q3 = float(linha["tempo_q1_ms"]), float(linha["tempo_q3_ms"])
    assert float(linha["tempo_min_ms"]) <= q1 <= float(linha["tempo_mediano_ms"]) <= q3 <= float(linha["tempo_max_ms"])
    assert abs(float(linha["tempo_iqr_ms"]) - (q3 - q1)) < 1e-3
limite = por_chave[("aberta-8x8", "forca_bruta")]
assert limite["situacao"] == "limite_de_tempo" and limite["custo"] == ""
assert limite["repeticoes_concluidas"] == "0" and limite["tempo_mediano_ms"] == ""
assert float(limite["tempo_max_ms"]) >= 2000 and int(limite["forca_estados"]) > 0

for (instancia, algoritmo), linha in por_chave.items():
    if algoritmo.startswith("dijkstra"):
        assert linha["dijkstra_expandidas"] == linha["consultas_adjacencia"]
        assert linha["dijkstra_descartadas"] == "0", "Grades de custo 1 não geram descartes"
    if algoritmo == "forca_bruta" and instancia in esperado:
        assert int(linha["forca_estados"]) == esperado[instancia]["estados_forca_bruta"]
        assert int(linha["forca_rotas"]) == esperado[instancia]["rotas_simples"]
        assert int(linha["custo"]) == esperado[instancia]["custo_minimo"]

for chave in ("python", "sistema", "processador", "nucleos_logicos", "repeticoes", "inicio", "fim"):
    assert ambiente[chave] not in (None, ""), chave
assert ambiente["limite_forca_bruta_s"] == 2 and ambiente["execucoes_incompletas"] == 1
assert ambiente["divergencias"] == 0 and ambiente["instancias"] == 14
print("OK: CSV com situação, quartis e contadores; limite de tempo da força bruta; registro do ambiente.")
