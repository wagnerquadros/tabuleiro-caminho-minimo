"""Importação de Moving AI e instâncias locais, sem dependências externas.

Política do estudo: . G S são livres; @ O T W são bloqueados.
Todo movimento permitido é ortogonal e custa 1. Não copiamos custos octile.
"""
from dataclasses import dataclass
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path

MAX_CELULAS = 1_048_576
LIVRES = frozenset(".GS")
BLOQUEADOS = frozenset("@OTW")


@dataclass(frozen=True)
class Mapa:
    grade: tuple[str, ...]
    nome: str
    fonte: str
    sha256_original: str
    linhas_originais: int
    colunas_originais: int
    deslocamento: tuple[int, int] = (0, 0)
    alterado: bool = False

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

    def metadados(self):
        return {"nome": self.nome, "fonte": self.fonte,
                "sha256_original": self.sha256_original,
                "dimensoes_originais": [self.linhas_originais, self.colunas_originais],
                "deslocamento_linha_coluna": list(self.deslocamento),
                "livres": ".GS", "bloqueados": "@OTW"}


@dataclass(frozen=True)
class Cenario:
    mapa: str
    linhas: int
    colunas: int
    origem: tuple[int, int]
    destino: tuple[int, int]
    custo_octile: float  # Apenas procedência: não é o ótimo do nosso modelo.


def _dimensoes(linhas, colunas):
    if not isinstance(linhas, int) or not isinstance(colunas, int):
        raise ValueError("As dimensões precisam ser inteiras.")
    if linhas <= 0 or colunas <= 0 or linhas * colunas > MAX_CELULAS:
        raise ValueError(f"Use uma grade não vazia com até {MAX_CELULAS:,} células.")


def _validar_grade(grade):
    if not isinstance(grade, (list, tuple)) or not grade or not isinstance(grade[0], str):
        raise ValueError("A grade deve conter linhas de texto.")
    _dimensoes(len(grade), len(grade[0]))
    if any(not isinstance(linha, str) or len(linha) != len(grade[0]) for linha in grade):
        raise ValueError("A grade precisa ser retangular.")
    if any(set(linha) - {".", "#"} for linha in grade):
        raise ValueError("A instância convertida aceita apenas '.' e '#'.")
    if not any("." in linha for linha in grade):
        raise ValueError("O mapa não tem nenhuma casa livre.")


def ler_mapa(caminho):
    """Valida o cabeçalho e converte símbolos, preservando dimensões e posições."""
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
    except (ValueError, TypeError) as erro:
        raise ValueError("Cabeçalho de dimensões inválido.") from erro
    if h != "height" or w != "width":
        raise ValueError("As dimensões devem usar height e width, nessa ordem.")
    _dimensoes(linhas, colunas)
    bruto = texto[4:]
    if len(bruto) != linhas or any(len(linha) != colunas for linha in bruto):
        raise ValueError("A grade não corresponde às dimensões declaradas.")
    desconhecidos = set("".join(bruto)) - LIVRES - BLOQUEADOS
    if desconhecidos:
        raise ValueError(f"Símbolos não suportados: {sorted(desconhecidos)}. Mapas Terrain exigem outra política.")
    grade = tuple("".join("." if celula in LIVRES else "#" for celula in linha) for linha in bruto)
    _validar_grade(grade)
    return Mapa(grade, caminho.name, str(caminho.resolve()), sha256(dados).hexdigest(), linhas, colunas)


def recortar(mapa, linha, coluna, altura, largura):
    """Recorta células sem redimensioná-las; compõe os deslocamentos no original."""
    if any(type(n) is not int for n in (linha, coluna, altura, largura)):
        raise ValueError("Os parâmetros do recorte devem ser inteiros.")
    if linha < 0 or coluna < 0 or altura <= 0 or largura <= 0:
        raise ValueError("Posição e tamanho do recorte inválidos.")
    if linha + altura > mapa.linhas or coluna + largura > mapa.colunas:
        raise ValueError("O recorte ultrapassa os limites do mapa atual.")
    grade = tuple(l[coluna:coluna + largura] for l in mapa.grade[linha:linha + altura])
    _validar_grade(grade)
    return Mapa(grade, mapa.nome, mapa.fonte, mapa.sha256_original,
                mapa.linhas_originais, mapa.colunas_originais,
                (mapa.deslocamento[0] + linha, mapa.deslocamento[1] + coluna), mapa.alterado)


def ler_cenarios(caminho, mapa):
    """Converte x,y em linha,coluna e rejeita escalas incompatíveis."""
    caminho = Path(caminho)
    if caminho.stat().st_size > 16_000_000:
        raise ValueError("Arquivo de cenários maior que o limite de 16 MB.")
    linhas = caminho.read_text(encoding="utf-8-sig").splitlines()
    if not linhas or linhas[0].strip() not in {"version 1", "version 1.0"}:
        raise ValueError("Esperado um arquivo .scen de versão 1.")
    resultado = []
    for numero, linha in enumerate(linhas[1:], 2):
        if not linha.strip():
            continue
        campos = linha.split()
        if len(campos) != 9:
            raise ValueError(f"Cenário da linha {numero}: esperado um total de 9 campos.")
        nome = campos[1].replace("\\", "/").rsplit("/", 1)[-1]
        if nome != mapa.nome:
            continue
        try:
            grupo, largura, altura, x0, y0, x1, y1 = map(int,
                [campos[0], *campos[2:8]])
            custo = float(campos[8])
        except ValueError as erro:
            raise ValueError(f"Cenário da linha {numero}: números inválidos.") from erro
        if grupo < 0 or not isfinite(custo) or custo < 0:
            raise ValueError(f"Cenário da linha {numero}: grupo ou custo inválido.")
        if (altura, largura) != (mapa.linhas_originais, mapa.colunas_originais):
            raise ValueError("O cenário usa dimensões diferentes; não fazemos reescala automática.")
        origem, destino = (y0, x0), (y1, x1)
        for r, c in (origem, destino):
            if not (0 <= r < altura and 0 <= c < largura):
                raise ValueError(f"Cenário da linha {numero}: ponto fora do mapa.")
        resultado.append(Cenario(nome, altura, largura, origem, destino, custo))
    if not resultado:
        raise ValueError("Não há cenários para o mapa carregado neste arquivo.")
    return resultado


def pontos_locais(mapa, cenario):
    """Um cenário só pode ser aplicado se os dois pontos couberem no recorte."""
    if cenario.mapa != mapa.nome or (cenario.linhas, cenario.colunas) != (
            mapa.linhas_originais, mapa.colunas_originais):
        raise ValueError("O cenário pertence a outro mapa ou a outras dimensões.")
    dl, dc = mapa.deslocamento
    origem = (cenario.origem[0] - dl, cenario.origem[1] - dc)
    destino = (cenario.destino[0] - dl, cenario.destino[1] - dc)
    if not mapa.livre(origem) or not mapa.livre(destino):
        raise ValueError("Os pontos estão fora do recorte ou sobre obstáculos. Carregue o mapa completo.")
    return origem, destino


def salvar_instancia(caminho, mapa, grade, origem, destino):
    """Exporta uma entrada reproduzível, incluindo pontos e procedência do recorte."""
    _validar_grade(grade)
    local = Mapa(tuple(grade), mapa.nome, mapa.fonte, mapa.sha256_original,
                 mapa.linhas_originais, mapa.colunas_originais, mapa.deslocamento)
    if not local.livre(origem) or (destino is not None and not local.livre(destino)):
        raise ValueError("Origem e destino precisam estar em casas livres.")
    obj = {"formato": "grade-caminho-minimo-v1", "regras": {"direcoes": 4, "custo": 1},
           "grade": list(grade), "origem": list(origem),
           "destino": list(destino) if destino is not None else None,
           "procedencia": local.metadados(), "editado": mapa.alterado or tuple(grade) != mapa.grade}
    Path(caminho).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def ler_instancia(caminho):
    caminho = Path(caminho)
    if caminho.stat().st_size > 8_000_000:
        raise ValueError("Arquivo de instância maior que o limite de 8 MB.")
    obj = json.loads(caminho.read_text(encoding="utf-8-sig"))
    if not isinstance(obj, dict) or obj.get("formato") != "grade-caminho-minimo-v1":
        raise ValueError("Formato de instância desconhecido.")
    if obj.get("regras") != {"direcoes": 4, "custo": 1}:
        raise ValueError("A instância não usa quatro direções e custo 1.")
    grade = obj.get("grade")
    _validar_grade(grade)
    info = obj.get("procedencia", {})
    if not isinstance(info, dict):
        raise ValueError("Procedência inválida.")
    dimensoes = info.get("dimensoes_originais", [len(grade), len(grade[0])])
    deslocamento = info.get("deslocamento_linha_coluna", [0, 0])
    if (not isinstance(dimensoes, list) or len(dimensoes) != 2
            or not isinstance(deslocamento, list) or len(deslocamento) != 2
            or any(type(n) is not int for n in dimensoes + deslocamento)):
        raise ValueError("Dimensões ou deslocamento de procedência inválidos.")
    _dimensoes(*dimensoes)
    if min(deslocamento) < 0 or any(d + n > limite for d, n, limite in
            zip(deslocamento, (len(grade), len(grade[0])), dimensoes)):
        raise ValueError("O recorte não cabe nas dimensões originais.")
    if type(obj.get("editado", False)) is not bool:
        raise ValueError("Indicador de edição inválido.")
    mapa = Mapa(tuple(grade), str(info.get("nome", caminho.name)),
                str(info.get("fonte", caminho.resolve())), str(info.get("sha256_original", "")),
                *dimensoes, tuple(deslocamento), obj.get("editado", False))
    pontos = []
    for chave in ("origem", "destino"):
        ponto = obj.get(chave)
        if chave == "destino" and ponto is None:
            pontos.append(None)
            continue
        if not isinstance(ponto, list) or len(ponto) != 2 or any(type(n) is not int for n in ponto):
            raise ValueError(f"{chave.capitalize()} inválida.")
        ponto = tuple(ponto)
        if not mapa.livre(ponto):
            raise ValueError(f"{chave.capitalize()} fora da grade ou sobre uma parede.")
        pontos.append(ponto)
    return mapa, *pontos
