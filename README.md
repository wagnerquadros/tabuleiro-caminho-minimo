# Tabuleiro de caminho mínimo

Aplicação didática em Python para estudar caminhos mínimos em grafos, com obstáculos, zoom e animação da rota. O projeto faz parte de um estudo de Otimização e Complexidade de Algoritmos inspirado em *The Algorithm Design Manual*, de Steven Skiena.

## Estado atual

- Dijkstra com fila de prioridade baseada em heap.
- Opção Força bruta visível e desativada; implementação prevista para a próxima etapa.
- 70 mapas Random de 512 × 512 do Moving AI Lab.
- Tabuleiro didático fixo no botão Mini 12 × 18.
- Edição de destino, origem e obstáculos habilitada pelo botão Editar.
- Zoom, navegação pelo mapa e animação com velocidade ajustável.
- Nome, dimensões e percentual de células bloqueadas em destaque.

Cada célula livre corresponde a um vértice. Movimentos ortogonais entre células vizinhas custam 1; não há diagonais.

## Executar

Requer **Python 3.10 ou posterior com Tkinter**. Não há bibliotecas externas a instalar.

Na pasta do projeto:

```text
python tabuleiro.py
```

No Windows, também é possível abrir **Abrir tabuleiro.bat** com um duplo clique. O aplicativo inicia no mapa `random512-20-0.map`.

## Como usar

1. Escolha um nome na lista **Mapa** e aperte **Carregar mapa** para abrir o arquivo completo.
2. Confira a área de informações logo abaixo: ela mostra o mapa efetivamente carregado, dimensões, casas livres, obstáculos e percentual bloqueado.
3. Na seção **Algoritmo**, **Dijkstra** fica selecionado. **Força bruta** está desativada por enquanto.
4. Nos mapas do dataset, a origem é o canto superior esquerdo e o destino é o canto inferior direito. Se um canto estiver bloqueado, a aplicação informa a célula livre mais próxima utilizada. A escolha usa distância Manhattan, com desempate por linha e coluna, e preserva os obstáculos.
5. Aperte **Play**. A linha verde mostra a rota mínima e o ponto azul percorre o caminho. **Menor caminho** informa a quantidade de movimentos.
6. Use **Pausar / Continuar** para interromper e retomar, ou **Concluir animação** para mostrar imediatamente a chegada.

Se aparecer **Sem rota**, os pontos estão desconectados nas regras do estudo. Se origem e destino coincidirem, o custo é zero.

### Tabuleiro Mini

**Mini 12 × 18** abre o tabuleiro didático original, independente do mapa selecionado no catálogo. Ele tem 41 obstáculos, origem na linha 3/coluna 3 e destino a escolher. Clique em **Editar**, mantenha **Marcar destino** e selecione uma casa livre antes de apertar Play.

### Editar pontos e obstáculos

Clique em **Editar** para habilitar:

- **Marcar destino:** clique em uma casa livre para escolher o destino.
- **Mover origem:** clique em uma casa livre para reposicionar o ponto inicial.
- **Editar obstáculos:** clique para adicionar ou remover uma parede.

**Concluir edição** desabilita as opções e impede alterações por clique ou Enter. Carregar outro mapa ou o Mini também desabilita a edição. Uma alteração na entrada interrompe a rota atual para que ela seja recalculada.

**Reiniciar percurso** devolve o personagem à origem definida, preservando o destino. Depois da chegada, um novo destino pode ser escolhido em Editar; a próxima busca parte da posição atual do personagem.

### Zoom e navegação

Use a roda do mouse sobre o mapa ou **+ / −** para ampliar. A roda mantém como referência a região sob o ponteiro. **Ajustar mapa** volta à visão geral.

Arraste com o botão direito ou use as barras de rolagem para navegar. **Origem / Destino** centralizam os pontos. **Seguir personagem no zoom** acompanha o movimento quando o mapa está ampliado.

O zoom muda apenas a apresentação. Na visão geral, algumas células podem ocupar menos de um pixel; amplie para selecionar uma casa com precisão. O algoritmo sempre usa a grade completa.

### Velocidade e teclado

| Velocidade | Duração programada |
|---|---|
| 1× | 0,12 segundo por movimento, limitada a oito segundos por percurso. |
| 2× | Metade da duração de 1×; limite de quatro segundos. |
| 4× | Um quarto da duração de 1×; limite de dois segundos. |
| Instantânea | Exibe diretamente a chegada. |

A velocidade escolhida vale no próximo Play. Pausas não consomem o tempo restante; atrasos da interface podem aumentar a duração observada.

Dê foco ao tabuleiro com um clique. As setas movem o cursor; Enter seleciona a célula quando a edição está habilitada; Espaço inicia ou pausa; Ctrl+0 ajusta a visão geral.

## Estrutura

| Caminho | Conteúdo |
|---|---|
| `tabuleiro.py` | Interface, controles, zoom e animação. |
| `roteamento.py` | Grafo da grade, Dijkstra e BFS para conferência. |
| `mapas_movingai.py` | Leitura e validação dos mapas e instâncias. |
| `datasets/artificial_random/` | Mapas originais, manifestos e cenários anteriores. |
| `testes/` | Verificações dos dados, zoom e animação. |
| `docs/` | Proposta e resumo acadêmico; os manuais serão elaborados na etapa final. |

As orientações de uso ficam neste README. `work/` e `outputs/` guardam registros e arquivos gerados localmente e ficam fora do histórico Git.

Documentos do estudo: [proposta](docs/Proposta_Python_Dijkstra_Forca_Bruta.md) e [resumo do primeiro entregável](docs/Resumo_Entregavel_1_Dijkstra_Forca_Bruta.md).

## Verificações

```text
python -B testes/verificar_datasets.py
python -B testes/verificar_zoom_animacao.py
```

As verificações exigem Tkinter funcional e podem abrir janelas. Incluem hashes dos 70 mapas, conversão, recortes, instâncias, comparação entre Dijkstra e BFS, casos sem rota, cliques após zoom e controles da animação.

**Busca: ... ms** mede a chamada de Dijkstra, incluindo validação e reconstrução, depois de construir o grafo. Não inclui carregar arquivos, construir o grafo ou animar. A avaliação experimental exige repetições e condições documentadas. Como os pesos são 1, BFS também encontra o caminho mínimo; aqui é usada como referência de validação.

## Dataset: origem, atribuição e regras

Os mapas são da família [Random maps do Moving AI Lab](https://www.movingai.com/benchmarks/random/index.html), parte dos [Artificial Benchmarks](https://www.movingai.com/benchmarks/grids.html). Autor/fonte indicado pelo repositório: **Nathan Sturtevant / HOG2, Moving AI Lab**.

O dataset é disponibilizado pela fonte sob a [Open Data Commons Attribution License v1.0](https://opendatacommons.org/licenses/by/1-0/). Esta atribuição acompanha os mapas neste README; a licença citada refere-se aos dados de origem.

A pasta contém 70 mapas, dez para cada série 10, 15, 20, 25, 30, 35 e 40. Também preserva os arquivos de cenários dos três mapas incluídos na integração inicial. Os arquivos originais mantêm seus bytes.

- `manifesto_random_zip.json` registra o pacote recebido, os 70 mapas e seus hashes SHA-256.
- `manifesto.json` registra os downloads anteriores, URLs, licença e hashes dos mapas e cenários.

Os números nos nomes das séries são rótulos da fonte. A proporção bloqueada deve ser medida na grade; por exemplo, `random512-40-0.map` tem aproximadamente 59,96% de células bloqueadas na conversão deste estudo.

O carregador valida o cabeçalho `type octile / height / width / map` e converte `.`, `G` e `S` em células livres e `@`, `O`, `T` e `W` em bloqueadas. Símbolos desconhecidos são rejeitados. A política de `S` e `W` é uma simplificação do modelo; mapas Terrain com regras próprias não fazem parte deste conjunto.

As regras da aplicação são quatro direções e custo 1. Os cenários publicados usam coordenadas `(x, y)`, convertidas pelo módulo para `(linha, coluna) = (y, x)`. Seus custos com diagonais não são resultados esperados para nosso modelo ortogonal.

Para adicionar outro mapa compatível ao catálogo, coloque o arquivo `.map` em `datasets/artificial_random` e reabra a aplicação.

## Referências

- SKIENA, Steven S. *The Algorithm Design Manual*. 2. ed. Springer, 2008, capítulo 6, caminhos mínimos e Dijkstra.
- STURTEVANT, Nathan R. *Benchmarks for Grid-Based Pathfinding*. IEEE Transactions on Computational Intelligence and AI in Games, v. 4, n. 2, p. 144–148, 2012. [Texto do autor](https://www.cs.du.edu/~sturtevant/papers/benchmarks.pdf).
