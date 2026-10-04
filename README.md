# Tabuleiro de caminho mínimo

Aplicação didática em Python para estudar caminhos mínimos em grafos, com obstáculos, zoom e animação da rota. O projeto faz parte de um estudo de Otimização e Complexidade de Algoritmos inspirado em *The Algorithm Design Manual*, de Steven Skiena.

## Estado atual

- Dijkstra por varredura linear, adaptado do código do livro.
- Dijkstra com fila de prioridade baseada em min-heap, selecionado inicialmente.
- BFS com fila FIFO, para caminhos mínimos com movimentos de custo 1.
- Força bruta por busca exaustiva com retrocesso, habilitada na interface.
- Dois mapas didáticos pequenos, de 3 × 3 e 4 × 4, para comparar os quatro algoritmos.
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
3. Na seção **Algoritmo**, escolha **Dijkstra — livro (varredura)**, **Dijkstra — min-heap**, **BFS — fila FIFO** ou **Força bruta**. As quatro opções estão habilitadas; min-heap é a inicial. Trocar o algoritmo reinicia o personagem na origem definida e preserva o destino, permitindo repetir a mesma consulta.
4. Nos mapas do dataset, a origem é o canto superior esquerdo e o destino é o canto inferior direito. Se um canto estiver bloqueado, a aplicação informa a célula livre mais próxima utilizada. A escolha usa distância Manhattan, com desempate por linha e coluna, e preserva os obstáculos.
5. Aperte **Play**. A linha verde mostra a rota mínima e o ponto azul percorre o caminho. **Menor caminho** informa a quantidade de movimentos.
6. Use **Pausar / Continuar** para interromper e retomar, ou **Concluir animação** para mostrar imediatamente a chegada.

Se aparecer **Sem rota**, os pontos estão desconectados nas regras do estudo. Se origem e destino coincidirem, o custo é zero.

Buscas em mapas grandes e todas as buscas por varredura ou força bruta acontecem em segundo plano. Durante o cálculo, o botão principal vira **Cancelar** e mostra o tempo decorrido. Clique nele para interromper; **Reiniciar percurso**, trocar de algoritmo ou carregar outro mapa também cancela a busca atual. **Concluir animação** só atua após o cálculo. A varredura pode demorar muito em mapas 512 × 512; use BFS ou min-heap para explorar os mapas completos. Para força bruta, comece com os mapas didáticos 3 × 3 e 4 × 4.

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

Dê foco ao tabuleiro com um clique. As setas movem o cursor; Enter seleciona a célula quando a edição está habilitada; Espaço inicia, pausa ou cancela uma busca em andamento; Ctrl+0 ajusta a visão geral.

## BFS com fila FIFO

Selecione **BFS — fila FIFO** na seção Algoritmo e aperte **Play**. A busca usa uma fila `collections.deque`: `append` coloca uma célula no final e `popleft` retira a primeira, ambos em O(1). FIFO significa que a primeira célula a entrar é a primeira a sair.

A origem entra na fila com distância zero. Ao retirar uma célula, a BFS descobre seus vizinhos livres, registra a distância como a distância atual mais 1 e guarda a célula anterior. Cada célula é marcada quando entra na fila, evitando inserções repetidas. Assim, a busca explora primeiro as células a um movimento, depois a dois, e assim sucessivamente. Ela encerra ao retirar o destino e reconstrói a rota pelos predecessores.

Como todos os movimentos custam 1, essa ordem garante o menor custo. A função rejeita arestas de custo diferente de 1; terrenos com custos variados exigiriam outro algoritmo, como Dijkstra. Origem igual ao destino retorna custo zero; destino desconectado retorna **Sem rota**. Nos mapas grandes, a BFS calcula em segundo plano e pode ser cancelada pelo botão principal ou ao trocar a entrada.

O tempo da busca, incluindo validação e reconstrução, é **O(V + E)**, com memória auxiliar **O(V)**. Na grade de quatro vizinhos, E = O(V), portanto o tempo é **O(V)**. Construir o grafo custa O(linhas × colunas) e fica fora do tempo de busca mostrado após a conclusão. BFS e Dijkstra podem escolher rotas diferentes em empates, mas devem obter o mesmo custo mínimo.

A referência é Skiena, 2ª edição, seção 5.6, p. 162–165; a seção 5.6.2 explica a reconstrução do caminho.

## As duas versões de Dijkstra

Na edição de 2008, Dijkstra está na **seção 6.3.1**, e o código em C da página 208 escolhe o próximo vértice por uma varredura linear. A seção **6.3.2** apresenta Floyd para caminhos mínimos entre todos os pares; esse não é o problema de uma única rota usado pelo tabuleiro.

As duas implementações mantêm distâncias e predecessores, relaxam arestas e finalizam vértices na ordem de menor distância conhecida. O que muda é a estrutura que seleciona o próximo vértice:

| Implementação | Seleção do próximo vértice | Tempo na grade | Memória auxiliar na grade |
|---|---|---|---|
| Livro / varredura | Percorre os vértices ainda não finalizados. | O(V²) | O(V) |
| Min-heap | Retira da fila de prioridade a menor distância. | O(V log(V + 1)) | O(V) |

V é o número de células livres. Cada vértice tem no máximo quatro vizinhos, portanto E = O(V). O grafo usa O(V + E) de memória, além das estruturas da busca. Construir o grafo e ler os obstáculos custa O(linhas × colunas), inclusive quando existem muitas células bloqueadas.

Em grafos gerais, a varredura custa O(V² + E). Nosso min-heap usa inserções de novas estimativas e descarta entradas desatualizadas, sem `decrease-key`; por isso, o limite geral é O(V + E log(E + 2)) de tempo e O(V + E) de memória auxiliar. Para grafos simples, também vale O((V + E) log(V + 1)).

O código do livro calcula distâncias da origem para todos os vértices alcançáveis. Na aplicação, ambas as versões encerram quando o destino é retirado como o próximo vértice de distância definitiva. Essa adaptação preserva o resultado da consulta origem–destino. Em caso de empate, as rotas podem ter células diferentes e o mesmo custo ótimo.

## Força bruta com retrocesso

Para experimentar, selecione **didatico-3x3.map** ou **didatico-4x4.map** na lista Mapa, aperte **Carregar mapa**, escolha **Força bruta** e aperte **Play**. São grades abertas, com origem no primeiro canto e destino no último: os custos mínimos são 4 e 6 movimentos, respectivamente. Há 12 caminhos simples no primeiro mapa e 184 no segundo; a força bruta enumera todos eles. Use Editar para adicionar obstáculos ou mover os pontos e repita a comparação.

No **Mini 12 × 18**, colocar o destino ao lado da origem não torna a enumeração rápida: além da rota de um movimento, existem muitas rotas maiores que também precisam ser examinadas. O aplicativo continua trabalhando e mostra **estados explorados** e **rotas completas**. Cada estado é um prefixo de rota examinado, não uma célula distinta; cada rota completa é uma chegada ao destino. Os contadores são atualizados em lotes durante a busca e mostram os totais quando ela termina. Enquanto isso, o campo de menor caminho fica sem resultado.

O algoritmo mantém a rota atual, seu custo e um conjunto com as células usadas nessa rota. Ao escolher um vizinho, ele acrescenta a célula e a marca; ao retornar, desfaz essa escolha e desmarca a célula. Assim, uma célula pode aparecer em outra rota, mas nunca se repete na mesma rota.

Ao chegar ao destino, compara o custo com o melhor encontrado e continua explorando as outras possibilidades. **Não encerra na primeira solução, não usa podas por custo e não usa Dijkstra ou BFS para auxiliar a busca.** Chegar ao destino encerra apenas o ramo atual: continuar e voltar ao mesmo destino repetiria uma célula.

Uma pilha explícita guarda os vizinhos ainda não tentados em cada etapa, cumprindo o papel das chamadas recursivas. Isso permite testar corredores longos sem atingir o limite de recursão do Python. O algoritmo guarda apenas a rota atual e a melhor rota, com memória auxiliar O(V), além do grafo.

O tempo depende da quantidade de caminhos simples explorados e é exponencial no pior caso. Na grade, a primeira célula tem até quatro opções e as seguintes até três, porque voltar à célula anterior é proibido. Com profundidade de no máximo V − 1 movimentos e cópias de rota de até V células, **O(V · 3^V)** é um limite superior conservador. Essa complexidade é da enumeração; o problema de caminho mínimo continua tendo soluções polinomiais, como Dijkstra.

A enumeração só retorna um resultado quando termina. Se for cancelada, o personagem não inicia uma rota parcial, e **Sem rota** não é exibido como conclusão da busca interrompida. Não há limite automático de tempo ou tamanho. Mesmo o Mini 12 × 18 pode exigir um número impraticável de caminhos; comece com as instâncias didáticas pequenas e use Reiniciar percurso para cancelar quando necessário.

## Estrutura

| Caminho | Conteúdo |
|---|---|
| `tabuleiro.py` | Interface, controles, zoom e animação. |
| `roteamento.py` | Grafo da grade, BFS, duas versões de Dijkstra e força bruta. |
| `mapas_movingai.py` | Leitura, validação e conversão dos arquivos `.map`. |
| `datasets/artificial_random/` | Mapas originais, manifestos e cenários anteriores. |
| `datasets/didaticos/` | Duas instâncias sintéticas abertas para comparação pequena. |
| `testes/` | Referências de correção e verificações dos algoritmos, dados e interface. |
| `docs/` | Proposta resumida do estudo; os manuais serão elaborados na etapa final. |

As orientações de uso ficam neste README. `work/` e `outputs/` guardam registros e arquivos gerados localmente e ficam fora do histórico Git.

Documento do estudo: [proposta resumida](docs/Proposta_Dijkstra_Forca_Bruta.md).

## Verificações

```text
python -B testes/verificar_bfs.py
python -B testes/verificar_dijkstra.py
python -B testes/verificar_forca_bruta.py
python -B testes/verificar_datasets.py
python -B testes/verificar_zoom_animacao.py
```

As verificações de BFS, força bruta, datasets e zoom exigem Tkinter funcional e podem abrir janelas. Os testes incluem hashes dos 70 mapas, conversão, consultas em regiões pequenas, comparação dos quatro algoritmos nas grades, pesos zero, destinos inalcançáveis, cancelamento, cliques após zoom e controles da animação. A força bruta é conferida em todas as 512 disposições de obstáculos da grade 3 × 3, para todos os pares de casas livres, e em grafos ponderados pequenos; também são verificadas enumeração completa, ausência de podas por custo e uma rota de 1.500 vértices. Os testes preservam uma BFS independente e Bellman-Ford como referências de correção. A BFS de produção também é conferida contra Dijkstra, incluindo todas as disposições de obstáculos 3 × 3 e mapas completos de 512 × 512.

Durante o cálculo, **Decorrido: ... s** mostra o tempo desde o envio da tarefa, incluindo a construção do grafo e eventual espera na fila. Após a conclusão, **Busca: ... ms** mede a chamada do algoritmo selecionado, incluindo validação, obtenção do caminho e, na força bruta, atualização dos contadores, depois de construir o grafo. Não inclui carregar arquivos, construir o grafo, esperar na fila de execução ou animar. A avaliação experimental exige repetições e condições documentadas. Como os pesos são 1, BFS também encontra o caminho mínimo e pode ser selecionada na interface para comparação com Dijkstra.

## Dataset: origem, atribuição e regras

Os mapas são da família [Random maps do Moving AI Lab](https://www.movingai.com/benchmarks/random/index.html), parte dos [Artificial Benchmarks](https://www.movingai.com/benchmarks/grids.html). Autor/fonte indicado pelo repositório: **Nathan Sturtevant / HOG2, Moving AI Lab**.

O dataset é disponibilizado pela fonte sob a [Open Data Commons Attribution License v1.0](https://opendatacommons.org/licenses/by/1-0/). Esta atribuição acompanha os mapas neste README; a licença citada refere-se aos dados de origem.

A pasta contém 70 mapas, dez para cada série 10, 15, 20, 25, 30, 35 e 40. Também preserva os arquivos de cenários dos três mapas incluídos na integração inicial. Os arquivos originais mantêm seus bytes.

- `manifesto_random_zip.json` registra o pacote recebido, os 70 mapas e seus hashes SHA-256.
- `manifesto.json` registra os downloads anteriores, URLs, licença e hashes dos mapas e cenários.

Os números nos nomes das séries são rótulos da fonte. A proporção bloqueada deve ser medida na grade; por exemplo, `random512-40-0.map` tem aproximadamente 59,96% de células bloqueadas na conversão deste estudo.

O carregador valida o cabeçalho `type octile / height / width / map` e converte `.`, `G` e `S` em células livres e `@`, `O`, `T` e `W` em bloqueadas. Símbolos desconhecidos são rejeitados. A política de `S` e `W` é uma simplificação do modelo; mapas Terrain com regras próprias não fazem parte deste conjunto.

As regras da aplicação são quatro direções e custo 1. Arquivos `.scen` e instâncias JSON da preparação anterior permanecem como dados, mas não são carregados pela interface atual. Os custos publicados nos cenários incluem diagonais e não são resultados esperados para nosso modelo ortogonal.

Para adicionar outro mapa compatível ao catálogo, coloque o arquivo `.map` em `datasets/artificial_random` e reabra a aplicação.

## Referências

- SKIENA, Steven S. *The Algorithm Design Manual*. 2. ed. Springer, 2008, seção 5.6, “Breadth-First Search”, p. 162–165; seção 6.3.1, “Dijkstra’s Algorithm”, p. 206–209. A seção 6.3.2 trata de caminhos mínimos entre todos os pares com Floyd.
- STURTEVANT, Nathan R. *Benchmarks for Grid-Based Pathfinding*. IEEE Transactions on Computational Intelligence and AI in Games, v. 4, n. 2, p. 144–148, 2012. [Texto do autor](https://www.cs.du.edu/~sturtevant/papers/benchmarks.pdf).
