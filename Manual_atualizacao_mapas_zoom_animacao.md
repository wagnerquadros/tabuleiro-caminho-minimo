# Manual da atualização: mapas Random, zoom e animação por tempo

Este manual explica a implementação atual em Python, salva em `D:\algoritimos\tabuleiro`. Leia `Como usar o tabuleiro.md` para experimentar os controles antes de estudar os métodos. O manual anterior continua sendo material de apoio para a construção inicial do tabuleiro; a versão abaixo acrescenta mapas grandes e muda a forma de animar.

## 1. Separar o problema da apresentação

O problema continua sendo encontrar o caminho de menor custo entre duas células livres. Cada célula é um vértice; cada passagem ortogonal entre vizinhos é uma aresta de custo 1. Não há diagonais.

A implementação tem três partes:

| Arquivo | Responsabilidade |
|---|---|
| `mapas_movingai.py` | Ler e validar os mapas; converter símbolos; preservar a procedência. |
| `roteamento.py` | Construir o grafo e calcular o caminho mínimo. |
| `tabuleiro.py` | Exibir a grade, receber cliques, aplicar zoom e animar o resultado. |

Essa separação permite conferir o algoritmo sem abrir a janela. Também impede que uma melhoria visual modifique silenciosamente a instância do problema.

## 2. Integrar o pacote recebido

O `random-map.zip` contém 70 arquivos `.map`, todos de 512 × 512: dez mapas para cada série 10, 15, 20, 25, 30, 35 e 40. Eles foram extraídos para `datasets/artificial_random` e validados pelo mesmo carregador usado pela aplicação.

A integração conferiu que cada entrada do ZIP era um nome simples de arquivo `.map`, sem caminhos para fora da pasta. Também comparou os três mapas que já existiam: os bytes eram iguais. Nenhum original foi convertido e sobrescrito no disco.

`manifesto_random_zip.json` registra o hash SHA-256 do ZIP, os nomes, tamanhos, hashes e quantidades de células livres. O hash serve para identificar a entrada exata de um experimento. O manifesto anterior continua registrando os três downloads e cenários da etapa anterior.

Para acrescentar futuramente um `.map` ao catálogo, coloque-o em `datasets/artificial_random` e reabra o aplicativo. A interface atual usa esse catálogo.

## 3. Converter o arquivo em uma grade

Um arquivo Moving AI começa com quatro linhas:

```text
type octile
height 3
width 5
map
..@..
.T...
.....
```

`ler_mapa` valida o tipo, os campos de dimensão, o número de linhas e a largura de cada linha. Rejeita símbolos sem uma regra de conversão, mapas vazios e arquivos maiores que os limites definidos no módulo.

A política do estudo é explícita: `.`, `G` e `S` viram células livres `.`; `@`, `O`, `T` e `W` viram obstáculos `#`. No exemplo:

```text
..#..
.#...
.....
```

A conversão conserva as posições e dimensões. O cabeçalho `octile` não obriga nossa implementação a permitir diagonais. Escolhemos quatro direções e recalculamos todas as rotas para essas regras.

O objeto imutável `Mapa` guarda a grade, nome, fonte, hash, dimensões originais e deslocamento de um eventual recorte. A interface usa `self.rows` e `self.cols`; deixa de pressupor que todo mapa tem 12 × 18.

## 4. Criar o catálogo na interface

No construtor de `RouteBoard`, `DATASET_DIR.glob("*.map")` encontra os arquivos incluídos. O dicionário `self.map_files` relaciona cada nome ao caminho, e `self.map_choice` guarda a escolha visível na lista.

**Carregar mapa** chama `load_selected`, que procura o caminho escolhido e usa `load_map_file`. Este método chama `ler_mapa` para `.map` ou `ler_instancia` para `.json`. Só depois de validar a entrada `load_board` substitui o estado atual.

**Mini 12 × 18** chama `load_example`, que reutiliza `restore` para abrir o tabuleiro didático fixo do antigo botão **Restaurar tabuleiro**. `default_walls()` gera suas 41 paredes, e `START = (2, 2)` define a origem na linha 3/coluna 3. O destino começa sem seleção. O botão Restaurar foi removido da interface; o Mini assume sua função.

A área `map_card` fica abaixo da seleção de mapa e antes da seção Algoritmo. `map_name` mostra o nome efetivamente carregado, `map_density` destaca o percentual bloqueado e `map_info` apresenta dimensões e quantidades. `update_map_info` recalcula esses dados quando um mapa é carregado ou seus obstáculos são editados. O Mini também mostra sua densidade: 41/216, aproximadamente 19,0%.

O botão **Editar** chama `toggle_editing`, que alterna `editing_enabled` e usa `set_editing` para habilitar ou desabilitar as três opções. Ao habilitar, o botão passa a mostrar **Concluir edição**. `select_cell` também confere essa condição antes de alterar os pontos ou paredes; assim, desabilitar os controles protege tanto os cliques quanto o Enter. Carregar um mapa ou o Mini encerra a edição.

A seção **Algoritmo** usa um `ttk.LabelFrame` e duas opções de seleção (`ttk.Radiobutton`). As duas compartilham `self.algorithm`, uma `tk.StringVar` inicializada com `"dijkstra"`. Uma variável comum permite que apenas uma opção fique selecionada.

A opção **Dijkstra** está habilitada. A opção **Força bruta** recebe `state="disabled"`, ficando visível e impedindo a seleção por mouse ou teclado. Nesta etapa, Play continua chamando a implementação existente de Dijkstra. O algoritmo de força bruta será implementado depois.

Os botões **Abrir arquivo**, **Recortar**, **Carregar cenário** e **Salvar instância** foram retirados da interface. As funções de leitura, recorte e instâncias permanecem disponíveis no código de apoio e nas verificações.

O `main` cria a janela e agenda o carregamento inicial com `after_idle`. Assim, a aplicação abre no mapa `random512-20-0.map`, com a janela já em processo de organizar seus componentes.

## 5. Definir origem e destino automaticamente

Dentro do código, as coordenadas começam em zero. Na interface, começam em um:

| Posição | Código | Interface |
|---|---|---|
| Primeiro canto | `(0, 0)` | linha 1, coluna 1 |
| Último canto de 512 × 512 | `(511, 511)` | linha 512, coluna 512 |

`load_board` usa o primeiro canto para a origem e o último para o destino quando esses pontos não foram fornecidos explicitamente. Essa regra se aplica aos mapas carregados do dataset. O Mini preserva a origem e as paredes do tabuleiro didático original e solicita que o usuário marque um destino após clicar em Editar.

Um canto pode estar bloqueado. Escolhemos uma casa livre próxima com `livre_mais_proxima`, usando a distância Manhattan:

```text
distância = |linha - linha_do_canto| + |coluna - coluna_do_canto|
```

Se houver empate, a menor linha e depois a menor coluna vencem. Essa regra torna a escolha reproduzível. Não verificamos a conectividade para escolher os pontos: um caso sem rota continua sendo uma instância válida.

Se houver ajuste, o painel informa o canto solicitado e a posição usada. Por exemplo, no arquivo `random512-40-0.map`, os pontos escolhidos são linha 5/coluna 140 e linha 474/coluna 512. Os cantos desse mapa são obstáculos; as paredes permanecem no lugar.

Não removemos paredes para satisfazer a posição desejada, pois isso criaria uma entrada diferente do benchmark. Os pontos efetivos também são registrados ao salvar um JSON. JSONs e cenários com pontos explícitos preservam seus pares de origem e destino.

## 6. Transformar a grade em um grafo e buscar a rota

Ao apertar Play, `current_grid` copia o estado atual das paredes para uma tupla de linhas. A função `calcular_rota` usa essa cópia:

```python
grafo = grafo_da_grade(grade)
inicio = perf_counter()
custo, caminho = dijkstra_heap(grafo, origem, destino)
return custo, caminho, perf_counter() - inicio
```

`grafo_da_grade` conecta apenas vizinhos livres. `dijkstra_heap` mantém distâncias, predecessores e uma fila de prioridade. Cada relaxamento substitui uma estimativa quando encontra uma rota de custo menor. A reconstrução segue os predecessores do destino até a origem.

Em grades maiores que 6.000 células, a chamada ocorre em um `ThreadPoolExecutor`. A janela consulta o resultado com `after(40, poll_search)`, sem esperar bloqueada pela tarefa. A tarefa não chama Tkinter; a atualização da janela ocorre na thread principal.

Se outro mapa for carregado durante a busca, `cancel_search` deixa de acompanhar o resultado anterior. Uma tarefa que já começou pode terminar internamente, mas não altera o novo tabuleiro.

## 7. Implementar zoom sem mudar a instância

O mapa tem coordenadas lógicas em células. O Canvas tem coordenadas gráficas em pixels. O zoom muda a relação entre elas.

`draw_board` calcula primeiro `fit_size`, o tamanho de célula que faz o mapa inteiro caber na janela. Em seguida:

```python
self.cell_size = self.fit_size * self.zoom
```

`self.zoom == 1` significa visão geral. O limite de ampliação corresponde a células de até 64 pixels, ou ao tamanho da visão geral quando ela já for maior. `self.offset` posiciona o canto da grade, e `self.world_size` define a área virtual rolável.

O método `center((r, c))` calcula o centro da célula:

```python
x = offset_x + (c + 0.5) * cell_size
y = offset_y + (r + 0.5) * cell_size
```

O `0.5` coloca o personagem no centro da casa. Para um clique, `cell_at` faz a transformação inversa e usa `floor` para descobrir a célula que contém o ponto.

Depois de rolar, o canto visível do Canvas já não é o canto da área virtual. Por isso, `cell_at` soma `canvasx(0)` e `canvasy(0)` às coordenadas do evento antes de converter. Sem essa soma, um clique no mapa ampliado selecionaria outra célula.

`change_zoom` registra qual posição do mapa está sob o ponteiro, muda a escala e reposiciona a vista para conservar essa posição. Nas bordas, a rolagem é limitada pela área virtual. Os botões usam o centro da janela como referência.

`pan_start` chama `scan_mark`, e `pan_move` usa `scan_dragto` para arrastar a vista. As barras chamam `scroll_x` e `scroll_y`. `focus_cell` centraliza uma célula, sendo usado pelos botões **Origem / Destino**, pelas setas e pelo acompanhamento opcional do personagem.

## 8. Desenhar somente a região visível

Desenhar 262.144 retângulos em um mapa 512 × 512 adicionaria muitos objetos ao Canvas. Criar uma imagem gigantesca ao ampliar também desperdiçaria memória.

`draw_background` identifica as linhas e colunas que intersectam a janela visível. Quando as células têm pelo menos seis pixels e há até 6.000 células visíveis, desenha somente essas casas como retângulos. A grade fica legível no detalhe.

Nas outras escalas, `draw_overview` produz uma imagem PPM apenas da área visível. Cada pixel recebe a cor da célula correspondente. A imagem é mantida em `self.map_image`, pois Tkinter precisa que a referência continue existindo.

A visão geral pode ter células menores que um pixel. Nesse caso, o desenho não mostra individualmente todas as casas; o algoritmo continua usando a grade completa. Use zoom para selecionar uma casa com precisão.

`queue_view` agrupa eventos sucessivos de arraste e rolagem usando `after_idle`. Isso evita gerar várias imagens intermediárias que não chegariam a aparecer.

Todos os objetos do fundo recebem a etiqueta `map`. Os marcadores e a rota usam `overlay`. Ao rolar, redesenhamos o fundo visível e mantemos as outras camadas nas coordenadas virtuais.

## 9. Corrigir a animação lenta

A versão anterior usava oito quadros de 20 ms por movimento: cerca de 0,16 segundo por aresta. Uma rota de 1.022 movimentos demoraria aproximadamente 163,52 segundos, sem contar o custo do desenho. Além disso, a rota inteira era recriada em cada quadro.

A nova função `duracao_animacao` define a duração visual:

```python
fator = {"1×": 1, "2×": 2, "4×": 4}[velocidade]
return min(8.0, passos * 0.12) / fator
```

Para **Instantânea**, a função retorna zero. Rotas pequenas mantêm movimentos visíveis; rotas grandes aumentam automaticamente a velocidade para caber no limite programado.

`tick` mede o tempo decorrido com `perf_counter`, chama `advance_animation` e agenda a próxima atualização. Não depende de cada callback ocorrer exatamente após 20 ms.

`advance_animation` calcula a posição ao longo da sequência já encontrada:

```text
posição = passos × tempo_acumulado / duração
índice = floor(posição)
fração = posição - índice
```

O índice determina a última célula alcançada. A fração interpola o personagem entre essa célula e a próxima. Se a máquina atrasar um quadro, a próxima atualização avança para a posição correspondente ao tempo real.

Em uma rota grande, algumas células intermediárias não aparecem em um quadro próprio. Elas continuam na lista do caminho e no custo. A interpolação usa sempre dois vizinhos consecutivos da rota; não cria uma passagem através de paredes.

`draw_overlay` desenha a rota uma vez, como uma única linha. O círculo e a letra do personagem têm identificadores guardados em `player_item` e `player_text`. `update_player` altera suas coordenadas com `canvas.coords`, sem recriar a rota. Ao mudar o zoom, a projeção gráfica é reconstruída na nova escala, preservando o caminho calculado.

## 10. Pausar, retomar e concluir

Ao pausar, a aplicação atualiza a posição pelo tempo decorrido e cancela o callback agendado. Guarda o tempo acumulado e a posição interpolada.

Ao continuar, reinicia apenas o relógio de referência. O tempo em pausa não entra no percurso. `finish_route` avança até o último ponto e mantém a rota e o custo disponíveis para observar.

`restart` cancela a animação, limpa a rota calculada e devolve o personagem à origem definida. Mudar destino, origem ou paredes também limpa a rota. Isso evita usar um caminho calculado para uma entrada que já mudou.

## 11. Analisar os custos separadamente

Considere `L × C` células totais, `V` casas livres, `E` movimentos dirigidos e `k` arestas da rota. Na grade, cada vértice tem até quatro vizinhos, então `E ≤ 4V`.

| Etapa | Custo relevante |
|---|---|
| Ler e converter o arquivo | O(L × C) tempo e memória da grade. |
| Escolher ponto próximo a canto bloqueado | O(L × C) tempo; percorre as casas livres. |
| Construir o grafo | O(L × C) tempo, O(V + E) memória. |
| Dijkstra com heap nesta grade | O(V log(V + 1)) tempo, O(V) memória auxiliar. |
| Criar a linha da rota | O(k) coordenadas e tempo de preparação no Python. |
| Atualizar posição do personagem | O(1) operações de coordenadas por quadro no Python. |
| Preparar o fundo visível | Proporcional aos pixels ou células visíveis. |

O trabalho do código Python da animação passa de O(k²), quando redesenhava a rota a cada quadro de cada movimento, para O(k + F), em que `F` é o número de atualizações, sem contar mudanças de zoom. O mecanismo gráfico do Tk ainda pode redesenhar regiões e processar a linha; essa análise não afirma custo constante de todo o renderizador.

O limite de oito segundos é uma decisão de apresentação, não uma melhoria assintótica de Dijkstra. Pausas e atrasos da interface podem aumentar a duração observada.

Como os pesos são 1, BFS é suficiente para encontrar o ótimo em O(V + E). Dijkstra permanece sendo o algoritmo estudado; BFS funciona como conferência independente. A comparação científica com força bruta deverá usar as mesmas instâncias e medir a busca fora da animação.

## 12. Verificar a implementação

`testes/verificar_datasets.py` confere conversão, cenários, recortes, exportação e 192 consultas contra BFS. `testes/verificar_zoom_animacao.py` verifica todos os 70 hashes, as células próximas dos cantos, três mapas completos contra BFS, cliques depois de zoom/rolagem, a permanência dos objetos gráficos e os controles da animação.

Nos mapas completos `random512-10-0.map`, `random512-20-0.map` e `random512-40-0.map`, os custos verificados para os pontos automáticos foram 1.022, 1.022 e 1.107, respectivamente. Isso não significa que todos os mapas das séries tenham esses custos.

O teste avança o tempo da animação de modo controlado, para verificar uma rota longa sem esperar oito segundos em cada execução. A conferência visual complementa os testes: abrir o mapa, ampliar, mover a vista, apertar Play e observar a chegada.

A enumeração exaustiva de caminhos e o executor da comparação experimental ainda pertencem à próxima etapa do estudo; esta atualização entrega os mapas e as melhorias da interface com Dijkstra.
