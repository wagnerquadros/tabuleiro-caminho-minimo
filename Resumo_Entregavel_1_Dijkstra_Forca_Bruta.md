# Comparação analítica e experimental entre Dijkstra e busca exaustiva para caminhos mínimos em grades de jogos digitais

## Problema e aplicação

Em jogos digitais, personagens precisam deslocar-se até um objetivo sem atravessar paredes ou outros obstáculos. Este trabalho investigará o problema de encontrar um caminho de menor custo entre uma origem e um destino em uma grade bidimensional. O cenário será representado por um tabuleiro visto de cima, no qual o usuário seleciona um destino para o personagem.

## Instâncias e modelagem

Cada instância será composta por uma grade, um conjunto de obstáculos estáticos e duas posições livres: origem e destino. Células livres serão vértices de um grafo, e movimentos entre vizinhos ortogonais serão arestas de custo 1. Não haverá diagonais. Serão considerados mapas com áreas abertas, corredores, múltiplas rotas e destinos inacessíveis, começando por grades pequenas para viabilizar a comparação.

## Algoritmos e justificativa

Serão comparados Dijkstra com fila de prioridade baseada em min-heap e força bruta por busca exaustiva com retrocesso. A força bruta enumerará caminhos simples, sem repetir células na mesma rota, mantendo o de menor custo. Não encerrará ao encontrar a primeira solução nem utilizará podas por custo. Como cada movimento custa 1, ciclos não pertencem a uma rota ótima.

Ambas as estratégias devem produzir custos ótimos iguais quando concluídas. A comparação investigará esforço computacional e escalabilidade. A busca em largura também é eficiente neste modelo, mas será utilizada apenas como apoio à validação; o foco será a comparação entre Dijkstra e enumeração exaustiva.

## Objetivo e avaliação prevista

O estudo investigará como tamanho da grade e disposição dos obstáculos afetam os algoritmos. As implementações em Python serão avaliadas quanto à correção e à complexidade de tempo e memória. Os experimentos usarão as mesmas entradas, registrando custo da rota, tempo de busca, estados processados e situação de término. Geração de mapas, construção do grafo e animação serão medidas separadamente da busca.

Instâncias, sementes aleatórias e ambiente serão documentados. Um limite de tempo será fixado antes da coleta principal; execuções interrompidas não serão confundidas com ausência de caminho ou otimalidade comprovada.

## Dados e contribuição esperada

Serão utilizados mapas da família **Random maps**, dos [Artificial Benchmarks do Moving AI Lab](https://www.movingai.com/benchmarks/grids.html), e mapas sintéticos controlados. A aplicação importará o formato `.map` e trabalhará com recortes pequenos documentados para a comparação. Os pares de origem e destino dos arquivos `.scen` poderão ser importados quando compatíveis com a região escolhida. A densidade será medida nas células, e custos de referência com diagonais não serão usados diretamente na validação. A contribuição será um estudo reproduzível de estratégias conhecidas, acompanhado de uma interface didática, sem pretensão de propor um novo algoritmo.

## Referências iniciais

- SKIENA, Steven S. *The Algorithm Design Manual*. 2. ed. Springer, 2008. Seção 6.3.1, “Dijkstra's Algorithm”.
- STURTEVANT, Nathan R. *Benchmarks for Grid-Based Pathfinding*. 2012. [Texto do autor](https://www.cs.du.edu/~sturtevant/papers/benchmarks.pdf).
- MOVING AI LAB. [Pathfinding Benchmarks: File Formats](https://www.movingai.com/benchmarks/formats.html).
