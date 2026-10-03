# Moving AI Lab — Artificial Benchmarks / Random maps

Este diretório contém os **70 mapas** da família Random recebidos no arquivo `random-map.zip`: dez mapas por série 10, 15, 20, 25, 30, 35 e 40. Também preserva os cenários dos três mapas incluídos anteriormente. Todos os arquivos originais foram mantidos sem modificar seus bytes.

`manifesto_random_zip.json` registra o pacote recebido e os 70 mapas. `manifesto.json` continua identificando os downloads anteriores e os três arquivos de cenários. O pacote novo não inclui cenários adicionais.

Fonte: [Random maps](https://www.movingai.com/benchmarks/random/index.html), parte dos [Artificial Benchmarks](https://www.movingai.com/benchmarks/grids.html).

Autor/fonte indicado pelo repositório: Nathan Sturtevant / HOG2, Moving AI Lab.

Referência: STURTEVANT, N. *Benchmarks for Grid-Based Pathfinding*. IEEE Transactions on Computational Intelligence and AI in Games, v. 4, n. 2, p. 144–148, 2012. [Texto do autor](https://www.cs.du.edu/~sturtevant/papers/benchmarks.pdf).

O repositório disponibiliza seus dados sob a [Open Data Commons Attribution License v1.0](https://opendatacommons.org/licenses/by/1-0/). Esta atribuição e o manifesto acompanham o subconjunto.

## Três mapas de referência e valores observados

Todos os mapas têm 512 linhas e 512 colunas, totalizando 262.144 células.

| Mapa | Células livres | Células bloqueadas | Cenários |
|---|---:|---:|---:|
| random512-10-0.map | 235.900 | 26.244 | 1.780 |
| random512-20-0.map | 209.281 | 52.863 | 1.910 |
| random512-40-0.map | 104.950 | 157.194 | 3.170 |

Os números 10, 20 e 40 são **rótulos das séries nos nomes dos arquivos**. A análise deve usar a proporção efetivamente medida no mapa ou recorte: aproximadamente 10,01%, 20,17% e 59,96% de células bloqueadas nestes três arquivos. A documentação desta entrega não atribui uma causa à diferença observada no terceiro arquivo.

`manifesto.json` registra URLs, tamanhos e SHA-256 dos arquivos extraídos. Ele permite conferir se o conteúdo mudou entre execuções.

## Conversão usada pelo aplicativo

O aplicativo lê o cabeçalho `type octile / height / width / map`. Converte `.`, `G` e `S` em células livres e `@`, `O`, `T` e `W` em bloqueadas. Símbolos desconhecidos são rejeitados. Nos três mapas de referência foram observados os símbolos `.`, `@` e `T`; não há necessidade de converter terrenos com custos diferentes neste subconjunto.

As regras do estudo são **quatro direções, sem diagonais, custo 1 por movimento**. O aplicativo conserva dimensões e coordenadas, e não faz reescala automática. A política sobre `S` e `W` é uma simplificação explícita para arquivos externos; mapas da família Terrain, com codificação e custos próprios, não fazem parte desta integração.

Os arquivos `.map.scen` contêm origem e destino com coordenadas `(x, y)`. A importação converte para `(linha, coluna) = (y, x)`. Os custos ótimos publicados nesses cenários consideram diagonais de custo raiz de 2 e não validam diretamente nosso modelo adaptado. A aplicação recalcula o custo ortogonal.

## Exemplo didático fixo

O botão **Mini 12 × 18** abre o tabuleiro didático original do aplicativo, com 41 obstáculos, e não faz um recorte do mapa Random. Para estudar o dataset completo, selecione um arquivo na lista e use **Carregar mapa**. O módulo Python continua oferecendo `recortar` para criar regiões em scripts e verificações.
