"""Leitura dos mapas Moving AI usados no catálogo do tabuleiro.

Política do estudo: . G S são livres; @ O T W são bloqueados.
Movimentos ortogonais e custo 1 são definidos em roteamento.py.
"""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

MAX_CELULAS = 1_048_576
LIVRES = frozenset(".GS")
BLOQUEADOS = frozenset("@OTW")


@dataclass(frozen=True)
class Mapa:
    grade: tuple[str, ...]
    nome: str
    sha256_original: str = ""

    @property
    def linhas(self):
        return len(self.grade)

    @property
    def colunas(self):
        return len(self.grade[0])

    @property
    def paredes(self):
        return {(r, c) for r, linha in enumerate(self.grade)
                for c, simbolo in enumerate(linha) if simbolo == "#"}

    def livre(self, ponto):
        r, c = ponto
        return 0 <= r < self.linhas and 0 <= c < self.colunas and self.grade[r][c] == "."


def ler_mapa(caminho):
    """Valida e converte um .map, preservando dimensões e posições originais."""
    caminho = Path(caminho)
    if caminho.stat().st_size > 8_000_000:
        raise ValueError("Arquivo de mapa maior que o limite de 8 MB.")
    dados = caminho.read_bytes()
    texto = dados.decode("utf-8-sig").splitlines()
    if len(texto) < 5 or texto[0].strip().lower() != "type octile" or texto[3].strip() != "map":
        raise ValueError("Esperado: type octile, height, width, map e as linhas da grade.")
    try:
        h, altura = texto[1].split()
        w, largura = texto[2].split()
        linhas, colunas = int(altura), int(largura)
    except ValueError as erro:
        raise ValueError("Cabeçalho de dimensões inválido.") from erro
    if h != "height" or w != "width":
        raise ValueError("As dimensões devem usar height e width, nessa ordem.")
    if linhas <= 0 or colunas <= 0 or linhas * colunas > MAX_CELULAS:
        raise ValueError(f"Use uma grade não vazia com até {MAX_CELULAS:,} células.")
    bruto = texto[4:]
    if len(bruto) != linhas or any(len(linha) != colunas for linha in bruto):
        raise ValueError("A grade não corresponde às dimensões declaradas.")
    desconhecidos = set("".join(bruto)) - LIVRES - BLOQUEADOS
    if desconhecidos:
        raise ValueError(f"Símbolos não suportados: {sorted(desconhecidos)}.")
    grade = tuple("".join("." if celula in LIVRES else "#" for celula in linha) for linha in bruto)
    if not any("." in linha for linha in grade):
        raise ValueError("O mapa não tem nenhuma casa livre.")
    return Mapa(grade, caminho.name, sha256(dados).hexdigest())
