# Tabuleiro de caminho mínimo

Aplicação didática em Python para estudar caminhos mínimos em grafos, com obstáculos, zoom e animação da rota. O projeto faz parte de um estudo de Otimização e Complexidade de Algoritmos inspirado em *The Algorithm Design Manual*, de Steven Skiena.

## Estado atual

- Dijkstra por varredura linear, adaptado do código do livro.
- Dijkstra com fila de prioridade baseada em min-heap, selecionado inicialmente.
- BMSSP algoritmo recente que quebra a "barreira da ordenação" de Dijkstra, com script de comparação experimental.
- BFS com fila FIFO, para caminhos mínimos com movimentos de custo 1.
- Força bruta por busca exaustiva com retrocesso, habilitada na interface.
- Dez mapas sintéticos de benchmark, `teste1.map` a `teste10.map`, com 6 × 10 células.
- Dois mapas didáticos pequenos, de 3 × 3 e 4 × 4, para comparar os algoritmos.
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
3. No controle **Algoritmo**, logo acima do tabuleiro, escolha **Dijkstra (livro)**, **Dijkstra (heap)**, **BFS**, **BMSSP** ou **Força bruta**. A linha abaixo resume o algoritmo escolhido (estrutura e complexidade). As cinco opções estão habilitadas; Dijkstra (heap) é a inicial. Trocar o algoritmo reinicia o personagem na origem definida e preserva o destino, permitindo repetir a mesma consulta.
4. Nos mapas do dataset, a origem é o canto superior esquerdo e o destino é o canto inferior direito. Se um canto estiver bloqueado, a aplicação informa a célula livre mais próxima utilizada. A escolha usa distância Manhattan, com desempate por linha e coluna, e preserva os obstáculos.
5. Aperte **Play**. A linha verde mostra a rota mínima e o ponto azul percorre o caminho. **Menor caminho** informa a quantidade de movimentos.
6. Use **Pausar / Continuar** para interromper e retomar, ou **Concluir animação** para mostrar imediatamente a chegada.

Se aparecer **Sem rota**, os pontos estão desconectados nas regras do estudo. Se origem e destino coincidirem, o custo é zero.

Buscas em mapas grandes e todas as buscas por varredura ou força bruta acontecem em segundo plano; a força bruta roda sempre em um processo Python separado (`explorador.py`), para nunca disputar o interpretador com a janela, e cancelá-la encerra esse processo na hora. Durante o cálculo, o botão principal vira **Cancelar** e mostra o tempo decorrido. Clique nele para interromper; **Reiniciar percurso**, trocar de algoritmo ou carregar outro mapa também cancela a busca atual. **Concluir animação** só atua após o cálculo. A varredura pode demorar muito em mapas 512 × 512; use BFS ou min-heap para explorar os mapas completos. Para força bruta, comece com os mapas didáticos 3 × 3 e 4 × 4.

### Tabuleiro Mini

**Mini 12 × 18** abre o tabuleiro didático original, independente do mapa selecionado no catálogo. Ele tem 41 obstáculos, origem na linha 3/coluna 3 e destino a escolher. Clique em **Editar**, mantenha **Marcar destino** e selecione uma casa livre antes de apertar Play.

### Mapas de teste para benchmarks

Os arquivos **teste1.map a teste10.map** ficam em `datasets/testes/` e aparecem em ordem numérica no início da lista Mapa. Todos têm **6 linhas e 10 colunas**, com origem na **linha 1, coluna 1** e destino na **linha 6, coluna 10**. Selecione um mapa e aperte **Carregar mapa**; em seguida, escolha o algoritmo e aperte **Play**.

São instâncias sintéticas fixas, com obstáculos variados. **Todos os dez mapas têm destino alcançável a partir da origem.** A tabela registra o resultado esperado para os pontos definidos acima.

| Mapa | Cenário | Obstáculos | Custo mínimo | Rotas simples |
|---|---|---:|---:|---:|
| `teste1.map` | Obstáculos distribuídos | 14 | 14 | 144 |
| `teste2.map` | Bloco central | 24 | 14 | 384 |
| `teste3.map` | Barreira vertical com passagem | 20 | 20 | 8 |
| `teste4.map` | Paredes alternadas | 20 | 22 | 24 |
| `teste5.map` | Corredor em serpentina | 27 | 32 | 1 |
| `teste6.map` | Corredores com becos sem saída | 37 | 14 | 1 |
| `teste7.map` | Rotas ao redor de blocos | 22 | 14 | 4 |
| `teste8.map` | Passagens estreitas | 27 | 32 | 1 |
| `teste9.map` | Barreira horizontal com abertura | 17 | 14 | 72 |
| `teste10.map` | Obstáculos intercalados | 18 | 14 | 20 |

O arquivo `datasets/testes/manifesto.json` registra dimensões, origem e destino, quantidade de obstáculos, custo mínimo esperado, quantidade de rotas simples e hash SHA-256 de cada mapa. Os custos foram conferidos com BFS, Dijkstra e enumeração exaustiva concluída. Esses valores servem para verificar os resultados; tempos de execução precisam ser medidos nas repetições do benchmark.

Para comparar os algoritmos, preserve os obstáculos e os mesmos pontos. Trocar o algoritmo devolve o personagem à origem configurada. Os dez mapas permitem comparar custos e esforço de busca em diferentes estruturas. Como todos têm 6 × 10 células, esse conjunto avalia a disposição dos obstáculos; a análise de crescimento com o tamanho exige também outras dimensões. A garantia de alcance se aplica aos mapas originais e aos extremos definidos; edições podem alterar a conectividade.

### Demonstração automática dos testes

Para assistir às instâncias de teste no tabuleiro, com animação:

```text
python -B demonstrar_testes.py
```

A janela abre e percorre, uma após a outra, os mapas `teste1` a `teste10`, com **Dijkstra — min-heap** e **BMSSP**. Em cada execução, carrega o mapa com a origem e o destino da instância, aperta Play, espera a busca e a animação e compara o custo exibido com o custo esperado do manifesto. O título da janela mostra o andamento (por exemplo, `Demonstração 7/20 · teste4.map · BMSSP … · esperado 22 ✓`), e o terminal recebe uma linha por execução e o resumo final. Fechar a janela encerra a demonstração.

Opções: `--explorar`, `--algoritmos dijkstra bmssp bfs dijkstra_simples forca_bruta`, `--velocidade 1×|2×|4×|Instantânea` e `--pausa 1.5` (segundos entre execuções).

### Mostrar exploração

Ligue o interruptor **Mostrar exploração**, no painel lateral, e aperte **Play**. As casas que o algoritmo examina aparecem em **amarelo enquanto ele explora**, na ordem em que ele as examina; as do passo mais recente ficam em amarelo claro, como uma frente que avança. Quando a exploração termina de aparecer, a rota verde é desenhada por cima e o personagem a percorre. Enquanto a busca roda, o botão principal cancela; depois que ela termina e a pintura ainda está em andamento, ele vira **Pular exploração**.

A comparação fica visível: Dijkstra e BFS param quando chegam ao destino e costumam deixar parte do mapa sem pintar; o BMSSP calcula as distâncias para todas as casas e pinta a região inteira da origem. O painel mostra **Casas examinadas**. Se não houver rota, a exploração mostra até onde a busca chegou.

**Sem impacto no tempo medido.** Com o interruptor ligado, a busca roda em outro processo Python (`explorador.py`), em outro núcleo do processador, e envia as casas em pequenos lotes enquanto explora; a janela só as pinta. Depois da exploração, o mesmo processo executa a busca de novo, sem nenhum registro, e é essa segunda execução que mede o tempo de **Busca**. Assim o tempo é o mesmo que com o interruptor desligado. O custo é rodar o algoritmo duas vezes; na força bruta, que pode demorar muito, isso dobra a espera.

Uma casa conta como examinada quando o algoritmo consulta a lista de vizinhos dela. O registro é feito por um invólucro do grafo, sem alterar os algoritmos de `roteamento.py`.

A janela nunca mostra uma casa antes de o algoritmo examiná-la. Em **Instantânea**, a exploração aparece no ritmo real do algoritmo. Em 1×, 2× e 4×, ela é desacelerada para dar para acompanhar (até cerca de 6 s em 1×); se o algoritmo for mais lento que isso, a pintura acompanha o ritmo dele. A demonstração automática aceita `--explorar`.

### Editar pontos e obstáculos

Clique em **Editar** para habilitar:

- **Marcar destino:** clique em uma casa livre para escolher o destino.
- **Mover origem:** clique em uma casa livre para reposicionar o ponto inicial.
- **Editar obstáculos:** clique para adicionar ou remover uma parede.

**Concluir edição** desabilita as opções e impede alterações por clique ou Enter. Carregar outro mapa ou o Mini também desabilita a edição. Uma alteração na entrada interrompe a rota atual para que ela seja recalculada.

**Reiniciar percurso** devolve o personagem à origem definida, preservando o destino. **Play** também reinicia o percurso: toda nova busca parte da origem definida, mesmo depois de uma chegada. Para buscar a partir de outra casa, use **Mover origem** em Editar.

### Zoom e navegação

Use a roda do mouse sobre o mapa ou **+ / −** para ampliar. A roda mantém como referência a região sob o ponteiro. **Ajustar mapa** volta à visão geral.

Arraste com o botão direito ou use as barras de rolagem para navegar. **Origem / Destino** centralizam os pontos. **Seguir personagem no zoom** acompanha o movimento quando o mapa está ampliado.

Com **Seguir personagem no zoom** ligado e o mapa ampliado, a câmera acompanha o personagem quadro a quadro, centralizado. O mapa é desenhado em blocos de 256 × 256 pixels guardados em cache: rolar a visão só move imagens prontas, e apenas os blocos que entram na tela são desenhados, poucos por quadro, para a animação não travar.

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

Selecione **BFS** no controle Algoritmo e aperte **Play**. A busca usa uma fila `collections.deque`: `append` coloca uma célula no final e `popleft` retira a primeira, ambos em O(1). FIFO significa que a primeira célula a entrar é a primeira a sair.

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

## BMSSP — Duan et al. (2025)

Selecione **BMSSP** no controle Algoritmo e aperte **Play**. O BMSSP (*Bounded Multi-Source Shortest Path*) é o núcleo do algoritmo de Duan, Mao, Mao, Shu e Yin, que em 2025 obteve tempo **O(m log^(2/3) n)** para caminhos mínimos de fonte única com pesos não negativos. Foi o primeiro resultado a superar o limite **O(m + n log n)** de Dijkstra em grafos esparsos, no modelo de comparação e adição. Dijkstra precisa retirar os vértices em ordem exata de distância; isso equivale a ordená-los, e ordenar n elementos custa Ω(n log n). O BMSSP evita essa ordenação total.

A implementação em `roteamento.py` segue os três algoritmos do artigo:

| Etapa do artigo | Função | O que faz |
|---|---|---|
| Algoritmo 1 — FindPivots | `encontrar_pivos` | Faz k rodadas de relaxamento estilo Bellman-Ford a partir da fronteira S. Se o conjunto alcançado W ficar grande (> k·\|S\|), mantém S; senão, só as raízes da floresta de caminhos mínimos com pelo menos k vértices viram **pivôs**. Assim a fronteira encolhe por um fator k. |
| Algoritmo 2 — BaseCase | `caso_base` | No nível 0, executa um Dijkstra limitado que finaliza no máximo k + 1 vértices. |
| Algoritmo 3 — BMSSP | `resolver` | Divide a faixa de distâncias em blocos: retira da estrutura D até 2^((l−1)t) vértices de menor distância, resolve o bloco recursivamente no nível l − 1, relaxa as arestas dos vértices concluídos e devolve à estrutura os que mudaram. |

Os parâmetros vêm do artigo: k = ⌊log^(1/3) n⌋, t = ⌊log^(2/3) n⌋ e ⌈log n / t⌉ níveis de recursão. No mapa 512 × 512 com 20% de obstáculos (209.281 casas), isso dá k = 2, t = 6 e três níveis.

**Empates.** O artigo supõe que todos os caminhos têm comprimentos diferentes. Em uma grade de custo 1 há muitos empates; por isso, cada vértice é comparado pela tupla (distância, número de arestas, índice do vértice), uma ordem total que separa os empates. Ela também aceita arestas de custo zero, porque o número de arestas cresce em cada passo.

**Diferenças em relação ao artigo.**

- A estrutura D (Lema 3.3) usa um min-heap com valores atualizáveis, e não a lista de blocos do artigo. A correção é a mesma, mas cada operação custa O(log N). Por isso, **esta implementação não atinge o limite O(m log^(2/3) n)**: ela serve para estudar a estratégia e medir o esforço, não para demonstrar o ganho assintótico.
- O artigo resolve o problema de fonte única; o BMSSP **não para ao alcançar o destino** e calcula as distâncias para todas as casas alcançáveis. Para uma comparação justa, o script de benchmark também mede `dijkstra_completo`, o Dijkstra com min-heap sem a parada antecipada.
- O artigo transforma o grafo para ter grau constante. Na grade de quatro vizinhos o grau já é no máximo 4, então a transformação não é necessária.

Memória auxiliar: O(V + E). Sem rota, retorna **Sem rota**; origem igual ao destino retorna custo zero. Nos mapas grandes, a busca roda em segundo plano e pode ser cancelada.

## Comparação experimental: Dijkstra × BMSSP × força bruta

```text
python -B comparar_algoritmos.py
```

O script mede, para as mesmas instâncias, grade, origem e destino:

- `dijkstra_heap`: Dijkstra com min-heap, encerrando no destino (a versão da interface);
- `dijkstra_completo`: o mesmo Dijkstra, calculando todas as casas, como o BMSSP;
- `bmssp`: BMSSP de Duan et al. (2025);
- `forca_bruta` (opcional): enumeração exaustiva com limite de tempo por execução.

Para incluir a força bruta, liste os algoritmos e, se quiser, o limite em segundos (padrão: 60):

```text
python -B comparar_algoritmos.py --algoritmos dijkstra_heap dijkstra_completo bmssp forca_bruta --limite-forca-bruta 60
```

A força bruta consulta o relógio só a cada 4.096 passos, para a verificação não pesar no tempo medido. Se a primeira repetição atingir o limite, as demais são puladas, pois também o atingiriam; a execução é registrada como incompleta, sem custo confirmado, com os estados explorados e as rotas completas contados até a interrupção. Nas instâncias maiores, isso é o esperado.

As instâncias são os dez mapas `teste1` a `teste10`, grades abertas n × n, recortes n × n do canto superior esquerdo de `random512-S-0.map` (séries S = 10, 20, 30, 40), com n = 16, 32, 64, 128, 256 e 512. Nos recortes, origem e destino são as casas livres mais próximas dos cantos, pela mesma regra da interface. Nas grades 512 × 512, o BMSSP leva de 2 a 4 segundos por execução; com cinco repetições, a rodada completa demora cerca de 15 minutos.

Para cada par (instância, algoritmo), o CSV gravado em `outputs/` registra a **situação de término** (`situacao`: `otimo`, `sem_caminho` ou `limite_de_tempo`), o número de repetições concluídas, custo, tamanho da rota, tempo mediano, primeiro e terceiro quartis (`tempo_q1_ms`, `tempo_q3_ms`) e intervalo interquartil (`tempo_iqr_ms`), mínimo e máximo das repetições, **consultas à lista de adjacência** (medida de esforço independente da máquina), pico de memória com `tracemalloc` e, para o BMSSP, k, t, níveis, chamadas recursivas e casos-base. Para as duas versões de Dijkstra, registra também as **retiradas** do min-heap, as **descartadas** (entradas desatualizadas, que existem porque uma melhora insere uma nova entrada em vez de alterar a antiga) e as **expandidas** (casas cujos vizinhos foram examinados; quando a busca para no destino, a retirada dele não conta como expansão). Nas grades de custo 1 não há descartes: a primeira distância que cada casa recebe já é a definitiva. Para a força bruta, registra **estados explorados** e **rotas completas** (`forca_estados`, `forca_rotas`). Os quartis são calculados por interpolação dentro dos dados e exigem pelo menos duas repetições. O tempo mede só a chamada do algoritmo; o esforço e a memória são medidos em execuções separadas, para não distorcer o tempo. Só execuções concluídas entram na conferência de custos: se duas delas obtiverem custos diferentes na mesma instância, o script avisa e termina com erro.

Ao lado do CSV, um arquivo `.json` com o mesmo nome registra o **ambiente** da coleta: versão e implementação do Python, sistema, processador, arquitetura, núcleos lógicos, repetições, algoritmos, tamanhos, séries, limite da força bruta, o comando usado, os horários de início e fim, o número de instâncias, as execuções incompletas e as divergências.

Opções: `--repeticoes 5`, `--tamanhos 16 32 64`, `--series 10 40`, `--algoritmos dijkstra_heap dijkstra_completo bmssp bfs` e `--saida arquivo.csv`.

**O que esperar.** Em Python, o BMSSP é várias vezes mais lento que Dijkstra com min-heap em todas as grades do estudo. Isso não contradiz o artigo: o ganho é assintótico, de um fator log^(1/3) n, que vale cerca de 2,6 para n = 262.144 (a grade 512 × 512 aberta). As constantes do BMSSP são muito maiores (relaxamentos repetidos em FindPivots, recursão e estrutura D) e, nesta versão, a estrutura D ainda usa heap. A razão entre os tempos tende a cair conforme a grade cresce, o que pode ser analisado nos resultados.

## Força bruta com retrocesso

Para experimentar, selecione **didatico-3x3.map** ou **didatico-4x4.map** na lista Mapa, aperte **Carregar mapa**, escolha **Força bruta** e aperte **Play**. São grades abertas, com origem no primeiro canto e destino no último: os custos mínimos são 4 e 6 movimentos, respectivamente. Há 12 caminhos simples no primeiro mapa e 184 no segundo; a força bruta enumera todos eles. Use Editar para adicionar obstáculos ou mover os pontos e repita a comparação.

No **Mini 12 × 18**, colocar o destino ao lado da origem não torna a enumeração rápida: além da rota de um movimento, existem muitas rotas maiores que também precisam ser examinadas. O aplicativo continua trabalhando e mostra **estados explorados** e **rotas completas**. Cada estado é um prefixo de rota examinado, não uma célula distinta; cada rota completa é uma chegada ao destino. Os contadores são atualizados em lotes durante a busca e mostram os totais quando ela termina. Enquanto isso, o campo de menor caminho fica sem resultado.

Durante a enumeração, uma **linha laranja** mostra a rota que a força bruta está testando naquele momento, com um ponto na casa da ponta. Ela deixa visível o comportamento da busca em profundidade: a rota avança, e o retrocesso testa todas as variações a partir da ponta antes de recuar mais um passo. Em mapas grandes, a ponta fica mudando enquanto o resto da linha quase não se move, porque as combinações perto do fim crescem exponencialmente. Para não pesar na janela, a linha usa só os cantos da rota, é desenhada com linhas finas e é atualizada no máximo a cada 120 ms. Com a exploração desligada, o processo faz uma única execução, que também mede o tempo; o envio do progresso e da rota laranja acontece a cada 4.096 passos e não altera o tempo de forma perceptível.

O algoritmo mantém a rota atual, seu custo e um conjunto com as células usadas nessa rota. Ao escolher um vizinho, ele acrescenta a célula e a marca; ao retornar, desfaz essa escolha e desmarca a célula. Assim, uma célula pode aparecer em outra rota, mas nunca se repete na mesma rota.

Ao chegar ao destino, compara o custo com o melhor encontrado e continua explorando as outras possibilidades. **Não encerra na primeira solução, não usa podas por custo e não usa Dijkstra ou BFS para auxiliar a busca.** Chegar ao destino encerra apenas o ramo atual: continuar e voltar ao mesmo destino repetiria uma célula.

Uma pilha explícita guarda os vizinhos ainda não tentados em cada etapa, cumprindo o papel das chamadas recursivas. Isso permite testar corredores longos sem atingir o limite de recursão do Python. O algoritmo guarda apenas a rota atual e a melhor rota, com memória auxiliar O(V), além do grafo.

O tempo depende da quantidade de caminhos simples explorados e é exponencial no pior caso. Na grade, a primeira célula tem até quatro opções e as seguintes até três, porque voltar à célula anterior é proibido. Com profundidade de no máximo V − 1 movimentos e cópias de rota de até V células, **O(V · 3^V)** é um limite superior conservador. Essa complexidade é da enumeração; o problema de caminho mínimo continua tendo soluções polinomiais, como Dijkstra.

A enumeração só retorna um resultado quando termina. Se for cancelada, o personagem não inicia uma rota parcial, e **Sem rota** não é exibido como conclusão da busca interrompida. Não há limite automático de tempo ou tamanho. Mesmo o Mini 12 × 18 pode exigir um número impraticável de caminhos; comece com as instâncias didáticas pequenas e use Reiniciar percurso para cancelar quando necessário.

## Estrutura

| Caminho | Conteúdo |
|---|---|
| `tabuleiro.py` | Interface, controles, zoom e animação. |
| `explorador.py` | Processo auxiliar da exploração ao vivo: envia as casas examinadas e mede o tempo sem registro. |
| `roteamento.py` | Grafo da grade, BFS, duas versões de Dijkstra, BMSSP e força bruta. |
| `demonstrar_testes.py` | Executa as instâncias de teste no tabuleiro, com animação, e confere os custos. |
| `comparar_algoritmos.py` | Benchmark Dijkstra × BMSSP × força bruta: tempo (mediana e quartis), esforço, memória e situação de término em CSV, e ambiente em JSON. |
| `mapas_movingai.py` | Leitura, validação e conversão dos arquivos `.map`. |
| `datasets/artificial_random/` | Mapas originais, manifestos e cenários anteriores. |
| `datasets/testes/` | Dez mapas de benchmark 6 × 10, todos alcançáveis, e manifesto com resultados esperados. |
| `datasets/didaticos/` | Duas instâncias sintéticas abertas para comparação pequena. |
| `testes/` | Referências de correção e verificações dos algoritmos, dados e interface. |
| `docs/` | Proposta resumida do estudo; os manuais serão elaborados na etapa final. |

As orientações de uso ficam neste README. `work/` e `outputs/` guardam registros e arquivos gerados localmente e ficam fora do histórico Git.

Documento do estudo: [proposta resumida](docs/Proposta_Dijkstra_Forca_Bruta.md).

## Verificações

```text
python -B testes/verificar_mapas_teste.py
python -B testes/verificar_bfs.py
python -B testes/verificar_dijkstra.py
python -B testes/verificar_benchmark.py
python -B testes/verificar_bmssp.py
python -B testes/verificar_forca_bruta.py
python -B testes/verificar_datasets.py
python -B testes/verificar_zoom_animacao.py
python -B testes/verificar_exploracao.py
```

As verificações de mapas de teste, BFS, força bruta, datasets e zoom exigem Tkinter funcional e podem abrir janelas. Os testes incluem hashes dos 70 mapas, conversão, consultas em regiões pequenas, comparação dos quatro algoritmos nas grades, pesos zero, destinos inalcançáveis, cancelamento, cliques após zoom e controles da animação. A força bruta é conferida em todas as 512 disposições de obstáculos da grade 3 × 3, para todos os pares de casas livres, e em grafos ponderados pequenos; também são verificadas enumeração completa, ausência de podas por custo e uma rota de 1.500 vértices. Os testes preservam uma BFS independente e Bellman-Ford como referências de correção. A BFS de produção também é conferida contra Dijkstra, incluindo todas as disposições de obstáculos 3 × 3 e mapas completos de 512 × 512. O BMSSP é conferido vértice a vértice contra um Dijkstra independente em grafos aleatórios com pesos zero e reais (até três níveis de recursão), em todas as disposições 3 × 3 com todos os pares de casas, em grades aleatórias, nos dez mapas de teste e em um mapa completo de 512 × 512.

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

- DUAN, Ran; MAO, Jiayi; MAO, Xiao; SHU, Xinkai; YIN, Longhui. *Breaking the Sorting Barrier for Directed Single-Source Shortest Paths*. STOC 2025. [arXiv:2504.17033](https://arxiv.org/abs/2504.17033).
- SKIENA, Steven S. *The Algorithm Design Manual*. 2. ed. Springer, 2008, seção 5.6, “Breadth-First Search”, p. 162–165; seção 6.3.1, “Dijkstra’s Algorithm”, p. 206–209. A seção 6.3.2 trata de caminhos mínimos entre todos os pares com Floyd.
- STURTEVANT, Nathan R. *Benchmarks for Grid-Based Pathfinding*. IEEE Transactions on Computational Intelligence and AI in Games, v. 4, n. 2, p. 144–148, 2012. [Texto do autor](https://www.cs.du.edu/~sturtevant/papers/benchmarks.pdf).
