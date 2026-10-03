# Comparação analítica e experimental entre Dijkstra e busca exaustiva para caminhos mínimos em grades de jogos digitais

## Proposta preliminar — versão detalhada com justificativas metodológicas

Esta versão reúne a proposta e as decisões que orientarão a implementação e os experimentos. O arquivo `Resumo_Entregavel_1_Dijkstra_Forca_Bruta.md` apresenta uma versão curta, adequada ao pedido de resumo do primeiro entregável. Quantidades de instâncias, repetições e limites de execução serão definidos no piloto e registrados antes da coleta principal.

### 1. Problema e aplicação

Em jogos digitais, personagens precisam encontrar rotas até um objetivo sem atravessar paredes ou outros obstáculos do cenário. Este trabalho investigará o problema de encontrar um caminho de menor custo entre uma origem e um destino em uma grade bidimensional com obstáculos estáticos.

O cenário será representado por um tabuleiro visto de cima, no qual um personagem recebe um destino selecionado pelo usuário. O objetivo será determinar uma rota com o menor número de movimentos ou informar que não existe caminho entre os pontos.

### 2. Instância e modelagem

Uma instância será composta por uma grade, suas células bloqueadas, uma posição inicial e uma posição final. Cada célula livre corresponderá a um vértice de um grafo; os movimentos permitidos entre células vizinhas corresponderão às arestas. Serão permitidos movimentos para cima, baixo, esquerda e direita, todos com custo 1, sem diagonais.

Serão estudados cenários com áreas abertas, corredores, múltiplas rotas e destinos inacessíveis. A grade é uma representação simplificada do deslocamento de um personagem em um mapa de jogo. Um caso inicial será o tabuleiro de 12 × 18 células já desenvolvido em Python; a comparação com força bruta começará em instâncias menores, conforme a viabilidade observada em testes-piloto.

Formalmente, uma entrada será dada por `I = (L, C, B, s, t)`, em que `L` e `C` são as dimensões da grade, `B` é o conjunto de células bloqueadas e `s` e `t` são a origem e o destino, ambos em células livres. A saída será uma sequência de posições adjacentes de `s` até `t`, sem atravessar obstáculos, que minimize o número de movimentos. Se não existir tal sequência, a saída deverá indicar ausência de caminho. Origem igual ao destino é uma entrada válida e tem custo zero.

O escopo será de um único personagem, com obstáculos estáticos durante cada busca, sem diagonais e com custos unitários. Alterações feitas pela interface gerarão uma nova consulta. Obstáculos móveis, múltiplos personagens, custos variáveis, A* e outras variantes ficarão fora da comparação principal, permitindo concluir o estudo dentro do semestre.

Por exemplo, no mapa padrão já existente, a origem de índice `(2, 2)` e o destino `(11, 17)` formam uma instância com custo ótimo 24. Na interface, que exibe números começando em 1, esses pontos são linha 3/coluna 3 e linha 12/coluna 18. Essa demonstração não implica que seja viável enumerar todos os caminhos do mapa inteiro por força bruta.

### 3. Algoritmos e justificativa

Serão comparadas duas estratégias exatas para o mesmo problema:

- **Dijkstra com min-heap:** mantém as melhores distâncias conhecidas e utiliza uma fila de prioridade para selecionar a próxima posição a processar.
- **Força bruta por busca exaustiva:** utiliza busca em profundidade com retrocesso para enumerar os caminhos simples entre origem e destino, mantendo o de menor custo. Um caminho simples não repete vértices. A busca não encerra ao encontrar a primeira rota e não utiliza podas baseadas no custo da melhor solução.

A restrição a caminhos simples preserva a solução ótima, pois todos os movimentos têm custo positivo e incluir um ciclo só aumenta o custo. A comparação permitirá investigar o efeito da estratégia de exploração sobre o esforço computacional. Embora a busca em largura também resolva eficientemente o caso de custos unitários, o estudo terá como foco Dijkstra e enumeração exaustiva, relacionando a implementação aos conceitos estudados na disciplina.

Quando concluídas, ambas as estratégias devem devolver uma solução ótima ou comprovar a inexistência de caminho. Portanto, a comparação principal será de esforço computacional e escalabilidade. Não se espera que Dijkstra produza uma rota de custo menor que uma enumeração exaustiva correta e concluída.

### 4. Questão de pesquisa e objetivo

**Como o tamanho da grade e a disposição dos obstáculos afetam o tempo de execução e o esforço de busca de Dijkstra e da enumeração exaustiva na resolução de caminhos mínimos em cenários de jogos digitais?**

O objetivo será implementar as estratégias em Python, verificar a correção dos resultados e comparar seus custos analíticos e experimentais, identificando os limites práticos da busca exaustiva nas instâncias estudadas.

### 5. Avaliação prevista

A avaliação analítica examinará a correção e a complexidade de tempo e memória das implementações. A avaliação experimental utilizará as mesmas grades e os mesmos pares de origem e destino para ambos os algoritmos, variando tamanho, quantidade e disposição dos obstáculos.

Serão registrados o custo da rota, o tempo de execução, as expansões realizadas durante a busca e a situação de término. Os testes serão repetidos em ambiente documentado, com instâncias e sementes aleatórias preservadas. A geração do mapa, a construção do grafo e a animação serão separadas da medição principal da busca.

Um limite de tempo será definido após os testes-piloto e antes dos experimentos principais. Execuções interrompidas serão identificadas como inconclusivas por limite de tempo, sem serem confundidas com ausência de caminho ou com uma solução ótima comprovada.

### 6. Dados e contribuição esperada

Serão utilizados os **Artificial Benchmarks** do Moving AI Lab, começando pela família **Random maps**, acompanhados de mapas sintéticos controlados para testes de correção e cenários específicos. Foram selecionados os arquivos `random512-10-0.map`, `random512-20-0.map` e `random512-40-0.map`, com 512 × 512 células, e seus arquivos de cenários. A escolha permite estudar ambientes artificiais de pathfinding compatíveis com a modelagem de jogos, sem depender de mapas de um jogo comercial.

A aplicação Python importa os arquivos `.map`, converte os símbolos em células livres ou bloqueadas e permite carregar o mapa inteiro ou recortes explícitos. Os recortes serão utilizados para viabilizar a comparação com força bruta. A adaptação para quatro direções, a posição das regiões e os critérios de seleção serão documentados. As distâncias de referência de cenários que permitem diagonais não serão usadas diretamente para validar o modelo adaptado. A densidade será medida nas células efetivas; os números nos nomes das séries não serão presumidos como densidades exatas.

A contribuição esperada é um estudo reproduzível sobre duas estratégias conhecidas, acompanhado de uma interface didática para visualizar as rotas. Não se pretende propor um novo algoritmo nem generalizar os resultados para todos os tipos de jogos.

### 7. Definição operacional da força bruta

O algoritmo começará na origem, tentará cada vizinho permitido e continuará construindo uma rota. Quando chegar ao destino, comparará o custo da rota com o melhor custo encontrado. Depois retornará às decisões anteriores para tentar as alternativas restantes.

Uma casa não pode aparecer duas vezes na mesma rota. Entretanto, ela poderá participar de outras rotas quando a busca retornar e tentar outro ramo. Por isso, o conjunto de visitados deve representar o caminho atual: a casa entra ao avançar e sai ao retroceder. Usar um conjunto global que nunca remove casas não enumera todos os caminhos simples.

O algoritmo manterá o caminho atual e o melhor caminho, sem armazenar todas as rotas encontradas. Encontrar a primeira rota não prova que ela é mínima. Encontrar alguma rota antes de um limite de tempo também não prova sua otimalidade.

Evitar uma repetição de vértice é parte da definição do espaço de busca. Já descartar um ramo porque seu custo atingiu o melhor custo conhecido adicionaria uma poda por limite de custo. Essa variante poderia ser estudada depois, mas não será misturada à versão exaustiva básica.

Busca em largura, busca em profundidade comum com visitados globais e enumeração exaustiva são procedimentos diferentes. Em particular, BFS não deve ser apresentada como a nossa força bruta.

Se uma rota repetir uma casa, haverá um ciclo entre duas ocorrências dessa casa. Remover o ciclo preserva uma rota entre os mesmos extremos e diminui seu custo, pois cada aresta custa 1. Logo, existe uma solução ótima sem ciclos. A enumeração de caminhos simples é finita e suficiente para resolver o problema.

### 8. Plano experimental inicial

1. **Testes de correção:** usar mapas pequenos com soluções conhecidas, incluindo origem igual ao destino, corredor único, múltiplas rotas e destino isolado. Conferir custo, extremidades, vizinhança e ausência de obstáculos na rota. Rotas diferentes podem ter o mesmo custo ótimo.
2. **Piloto:** começar, por exemplo, com grades 3 × 3, 4 × 4 e 5 × 5, variando estrutura e obstáculos. Esses tamanhos são pontos de partida, não uma promessa de que todos serão baratos para a enumeração.
3. **Definição do protocolo:** fixar instâncias, sementes, quantidade de repetições e tempo máximo antes da coleta principal. Preservar casos concluídos e inconclusivos.
4. **Comparação pareada:** executar ambos sobre a mesma representação e entrada. Documentar a ordem dos vizinhos e alternar a ordem de execução dos algoritmos para reduzir efeitos sistemáticos do ambiente.
5. **Medição:** cronometrar a chamada da busca, incluindo a reconstrução da rota e um tratamento equivalente da validação de entrada. Usar contagens de operações como complemento ao tempo. Se a instrumentação alterar muito os tempos, separar a coleta de contadores da cronometragem.
6. **Análise:** apresentar medianas e dispersão dos tempos, resultados de correção e proporção de casos concluídos por categoria. Não calcular uma média comum tratando o timeout como se fosse tempo de conclusão.
7. **Escalabilidade complementar:** se Dijkstra for executado em grades maiores nas quais a força bruta não foi concluída, identificar esse conjunto separadamente. Não atribuir à força bruta um tempo estimado como se ele tivesse sido medido.

Tempo de animação não mede eficiência da busca. A interface permite demonstrar o resultado; os experimentos devem funcionar também sem a janela.

Serão documentados processador, memória disponível, sistema operacional, versão do Python e versão do código. A representação do grafo será compartilhada, e cada execução começará com o estado da busca reinicializado. A ordem dos vizinhos será determinística. A política de limite de tempo será a mesma para ambos os algoritmos e seu custo de monitoramento será considerado no protocolo.

Serão incluídos vários mapas e pares de origem e destino por categoria. Repetir a busca no mesmo mapa mede a variação temporal, mas não substitui a diversidade de instâncias. Serão registradas a distância de Manhattan entre os extremos e a alcançabilidade, evitando atribuir apenas ao tamanho da grade diferenças que também podem decorrer da posição dos pontos ou da conectividade do mapa.

As categorias iniciais serão:

| Categoria | Característica investigada |
|---|---|
| Área aberta | Muitas alternativas de caminho e elevada ramificação. |
| Corredor único | Poucas alternativas, mesmo quando o percurso é comprido. |
| Salas conectadas | Efeito de passagens estreitas entre regiões abertas. |
| Obstáculos aleatórios | Variação entre mapas com densidades controladas e sementes fixas. |
| Destino inacessível | Custo de comprovar a inexistência de uma rota. |

Os critérios de seleção serão fixados antes da coleta principal. Casos sem rota e execuções que excederem o limite serão preservados e analisados separadamente. Se houver recortes ou seleção de pares conectados para algum subconjunto, essa decisão será explícita.

### 9. Métricas e interpretação

| Medida | Finalidade |
|---|---|
| Linhas, colunas, vértices livres e arestas | Caracterizar o tamanho da entrada. |
| Obstáculos e tipo de cenário | Caracterizar a estrutura do mapa. |
| Custo da rota | Verificar a qualidade e a concordância das soluções. |
| Tempo de execução | Medir o custo observado no ambiente utilizado. |
| Estados de busca processados | Em Dijkstra, contar retiradas válidas da fila; na força bruta, contar entradas em caminhos parciais válidos. A mesma casa pode ser processada muitas vezes na enumeração, em rotas distintas. |
| Caminhos completos examinados pela força bruta | Ilustrar o tamanho da enumeração; não é um contador equivalente ao de Dijkstra. |
| Situação de término | Separar ótimo encontrado, inexistência de rota comprovada e interrupção por limite. |

Não supor que aumentar a proporção de obstáculos sempre piora o desempenho: obstáculos podem reduzir o número de rotas possíveis ou tornar o destino inacessível. Tamanho e densidade iguais também podem produzir dificuldades diferentes se a disposição das paredes mudar.

A contagem de estados incluirá o estado correspondente ao destino quando ele for processado. Entradas desatualizadas descartadas pelo heap poderão ser registradas em um contador separado. Esses contadores representam eventos distintos em cada estratégia; auxiliam a interpretar os tempos, mas não são contagens de casas únicas nem medidas universais de custo por operação.

A memória será analisada teoricamente. A medição experimental de memória poderá ser acrescentada como complemento, se houver tempo e um procedimento adequado; não será requisito da primeira comparação. Essa separação evita prometer uma métrica cuja instrumentação ainda não foi definida.

### 10. Expectativas analíticas iniciais

Com `V` vértices e `E` arestas, Dijkstra com heap na representação de grafo simples pode ser analisado em O((V + E) log(V + 1)). A implementação Python existente utiliza entradas repetidas na fila e descarta as desatualizadas; a análise final deve corresponder a esse código. Como a grade tem grau máximo 4, E = O(V), simplificando o limite para O(V log(V + 1)). Construir a grade e seu grafo tem custo O(L × C), contabilizado à parte.

A enumeração pode explorar exponencialmente muitos caminhos simples. Uma análise adequada deve contar os caminhos parciais visitados, e não apenas as casas do tabuleiro: a mesma casa reaparece em diversos ramos. Com implementação in-place, manter o conjunto do caminho atual, a pilha e a melhor rota exige O(V) de memória auxiliar; não é necessário guardar todas as rotas.

Para a grade de quatro vizinhos, um limite superior grosseiro para os nós da árvore de busca é O(3^V): após o primeiro movimento há no máximo três escolhas, pois voltar imediatamente à casa anterior é proibido, e a profundidade é no máximo V−1. A restrição de outras casas já visitadas pode reduzir bastante esse número. A análise de tempo detalhada também deve incluir o custo das operações implementadas, especialmente eventuais cópias de listas e conjuntos; por isso, o resultado analítico definitivo virá depois de especificarmos a implementação.

Essas expectativas orientam o estudo. Os experimentos não constituem prova de complexidade assintótica, nem devem ser selecionados apenas para confirmar que Dijkstra é mais rápido em todos os casos.

O problema de caminho mínimo deste estudo admite solução em tempo polinomial. O crescimento exponencial da enumeração caracteriza essa estratégia de solução, e não demonstra que o problema em si seja intrinsecamente exponencial ou NP-difícil.

### 11. Dataset público e adaptação

O Moving AI Lab disponibiliza famílias de **Artificial Benchmarks**, incluindo Random maps, Mazes e Room maps. Nesta etapa, foi integrada a família Random. Para manter a comparação viável, a proposta usará recortes pequenos, escolhidos por regra documentada, além dos mapas sintéticos. As conclusões deverão ser limitadas a esses recortes e categorias de entrada.

A documentação do formato informa que os custos ótimos dos arquivos de cenários consideram diagonais com custo raiz de 2. Como nosso modelo permite somente quatro direções, esses custos não são uma referência diretamente válida. Será necessário recomputar os resultados esperados sob nossas regras, documentar quais símbolos representam bloqueios e não confundir coordenadas `(x, y)` dos arquivos com `(linha, coluna)` da aplicação.

Os três mapas e seus cenários foram baixados e integrados à aplicação. Os arquivos originais permanecem sem alteração; um manifesto registra URLs e hashes SHA-256. A conversão aceita `.`, `G` e `S` como livres, e `@`, `O`, `T` e `W` como bloqueados; símbolos desconhecidos são rejeitados. Nos mapas Random selecionados, aparecem apenas `.`, `@` e `T`.

A aplicação exporta a entrada convertida em JSON com origem, destino, regras, dimensões originais, deslocamento do recorte e indicação de edição. O botão de exemplo utiliza uma janela central fixa de 12 × 18, independente do resultado da busca. Esse exemplo serve à demonstração, e não substitui a seleção de múltiplas instâncias para os experimentos principais.

A integração já permite buscar rotas com Dijkstra. A enumeração exaustiva e a coleta experimental pareada serão implementadas na próxima etapa do estudo.

### 12. Hipóteses de trabalho

As hipóteses orientarão a análise, sem substituir os resultados:

- **H1 — Crescimento do esforço:** em famílias de grades com muitas alternativas de percurso, o aumento do tamanho tenderá a ampliar a diferença de esforço e de tempo entre a enumeração exaustiva e Dijkstra, incluindo a ocorrência de execuções inconclusivas da enumeração dentro do limite fixado.
- **H2 — Efeito da estrutura:** o número de células e a proporção de obstáculos não serão suficientes, isoladamente, para explicar o desempenho. Mapas com corredores, salas e áreas abertas poderão ter comportamentos diferentes mesmo quando apresentarem tamanhos e densidades semelhantes.

H1 será examinada por meio de curvas de tempo, contagens de estados e taxas de conclusão por tamanho e categoria. H2 será examinada comparando estruturas sob tamanhos e densidades semelhantes e documentando diferenças de distância entre os extremos e alcançabilidade. Não será assumido que Dijkstra sempre vence em toda instância ou que adicionar paredes sempre aumenta o tempo.

### 13. Validação e critérios de sucesso

Antes da coleta de desempenho, as implementações deverão satisfazer os seguintes critérios:

1. Toda rota retornada começa na origem, termina no destino e passa apenas por células livres e vizinhas ortogonais.
2. O custo informado corresponde à quantidade de movimentos, isto é, ao número de posições da rota menos um.
3. Em execuções concluídas na mesma instância, os dois algoritmos concordam sobre o custo ótimo ou a inexistência de caminho. As sequências de posições podem diferir quando houver empate.
4. Origem igual ao destino resulta em custo zero, e uma origem ou destino fora da grade ou sobre uma parede é tratado como entrada inválida, não como caso sem rota.
5. Uma interrupção por limite de tempo é distinguida de uma conclusão. Uma rota encontrada antes da interrupção poderá ser apresentada como solução viável, mas não como ótima certificada pela enumeração incompleta.

Nos casos pequenos, serão utilizadas instâncias com respostas conhecidas e uma implementação de BFS como verificação independente dos custos unitários. Seu papel será validar a correção, sem ampliar a comparação principal para um terceiro algoritmo. A concordância experimental complementará, mas não substituirá, a justificativa de correção de cada estratégia.

O estudo será considerado concluído quando houver implementações documentadas, testes de correção, análise assintótica, protocolo reproduzível, resultados experimentais com limitações discutidas e uma demonstração gráfica. Não será necessário que a força bruta conclua todos os mapas grandes nem que os resultados confirmem todas as hipóteses.

### 14. Apresentação dos resultados e limitações

Serão produzidos gráficos de tempo de execução em função do tamanho das instâncias, gráficos ou tabelas de estados processados e proporções de execuções concluídas por categoria. A escala logarítmica poderá ser usada quando facilitar a leitura das diferenças de tempo, com eixos e unidades claramente identificados.

As razões entre tempos serão calculadas apenas para execuções concluídas de ambos os algoritmos na mesma instância. Resultados interrompidos aparecerão explicitamente, acompanhados do limite utilizado. Comparações restritas aos casos concluídos serão identificadas como tal, pois ignorar os casos mais difíceis pode distorcer a interpretação.

O relatório discutirá a influência do ambiente de execução, da seleção de mapas e posições, da instrumentação e do limite de tempo. Mapas sintéticos e pequenos recortes de jogos não representam todos os jogos digitais. A discussão limitará as conclusões às famílias de instâncias avaliadas.

Serão preservados código-fonte, testes, mapas, parâmetros, sementes, resultados brutos em formato tabular e instruções de reprodução. A interface será utilizada para apresentar exemplos de rotas e casos sem solução; a duração de sua animação não será usada para comparar eficiência.

### Referências iniciais

- SKIENA, Steven S. *The Algorithm Design Manual*. 2. ed. Springer, 2008. Seção 6.3.1, “Dijkstra's Algorithm”.
- STURTEVANT, Nathan R. *Benchmarks for Grid-Based Pathfinding*. 2012. [Texto disponibilizado pelo autor](https://www.cs.du.edu/~sturtevant/papers/benchmarks.pdf).
- MOVING AI LAB. [Pathfinding Benchmarks](https://www.movingai.com/benchmarks/).
- MOVING AI LAB. [Artificial Benchmarks](https://www.movingai.com/benchmarks/grids.html), família [Random maps](https://www.movingai.com/benchmarks/random/index.html).
- MOVING AI LAB. [Pathfinding Benchmarks: File Formats](https://www.movingai.com/benchmarks/formats.html).
