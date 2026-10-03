> Atualização: a versão atual contém os 70 mapas do ZIP enviado, selecionáveis por nome, com zoom e pontos automáticos nos cantos quando livres. Consulte `Como usar o tabuleiro.md` e `Manual_atualizacao_mapas_zoom_animacao.md`. Este texto abaixo documenta a integração inicial de três mapas e os cenários que continuam incluídos. Os nomes de alguns botões mudaram.

# Usar os Artificial Benchmarks no tabuleiro Python

O aplicativo agora importa mapas do Moving AI Lab e pode carregar origens e destinos de seus arquivos de cenários. A integração usa a família **Random maps**, pertencente aos **Artificial Benchmarks**. Esse subconjunto contém três mapas reais do repositório público, embora seus ambientes tenham sido gerados artificialmente.

## 1. Experimente um mapa público

1. Abra `Abrir tabuleiro.bat`.
2. Na barra superior, escolha a série Random 10, 20 ou 40.
3. Aperte **Carregar exemplo**.
4. A janela mostrará um recorte central de 12 × 18 do arquivo público escolhido. O nome, as dimensões, as casas livres, a proporção bloqueada e a posição do recorte aparecem acima do tabuleiro.
5. Use **Mover origem** para escolher a posição inicial e **Marcar destino** para escolher a posição final.
6. Aperte **Play**.

O recorte não cria um mapa aleatório novo. Ele seleciona uma região exata do arquivo baixado. As coordenadas de origem e destino são locais ao recorte, e a procedência permite convertê-las para o mapa completo.

## 2. Abra o mapa inteiro

Use **Abrir mapa** e escolha um arquivo `.map` em `datasets/artificial_random`:

- `random512-10-0.map`;
- `random512-20-0.map`;
- `random512-40-0.map`.

O original completo tem 512 × 512 células. A janela mostra uma visão geral, na qual algumas células podem ocupar menos de um pixel. Essa limitação é visual: a grade usada pelo algoritmo continua contendo todas as células. Para selecionar regiões com precisão e estudar instâncias pequenas, use **Recortar**.

O carregador aceita mapas padrão com até 1.048.576 células e arquivos `.map` de até 8 MB. Dimensões incompatíveis com o cabeçalho, mapas sem casas livres e símbolos desconhecidos produzem uma mensagem de erro. O tabuleiro atual só é substituído depois da validação.

## 3. Crie um recorte

1. Abra o mapa completo.
2. Aperte **Recortar**.
3. Informe linha e coluna iniciais, começando em **1 no mapa atual**, e a quantidade de linhas e colunas.
4. Aperte **Aplicar recorte**.

Para reproduzir o exemplo central de 12 × 18 do original 512 × 512, informe linha inicial **251**, coluna inicial **248**, altura **12** e largura **18**. Para estudar grades 3 × 3 ou 5 × 5, altere o tamanho e documente a posição escolhida.

Um segundo recorte usa posições relativas ao recorte atual. O aplicativo soma os deslocamentos e mantém a posição da região no original. Recortes que saem da grade ou só contêm obstáculos são rejeitados.

O recorte modifica o domínio da busca: uma rota que sairia da região no original deixa de ser permitida. Portanto, a solução do recorte precisa ser recalculada. Não presumimos que ela tenha o mesmo custo da solução no mapa completo.

## 4. Carregue um cenário do dataset

1. Abra o mapa completo desejado.
2. Aperte **Carregar cenário**.
3. Escolha o arquivo correspondente, por exemplo `random512-20-0.map.scen`.
4. Informe o número do caso, começando em 1.
5. Aperte **Play** para recalcular o caminho.

Cada registro fornece um par de origem e destino. O programa confere o nome do mapa, suas dimensões e as posições. Em um recorte, o cenário só pode ser aplicado quando os dois pontos cabem na região e continuam livres. Se isso não ocorrer, abra o mapa completo ou escolha outra instância.

Os cenários publicados permitem diagonais e trazem custos para essa regra. Nosso estudo usa quatro direções, com custo 1: esses números não são usados como resultado esperado. Por exemplo, o segundo caso da série 20 tem custo publicado de aproximadamente 2,414 e custo ortogonal recalculado de **3**, verificado nesta entrega.

## 5. Salve uma instância para os experimentos

Depois de escolher o mapa ou recorte e os pontos, aperte **Salvar instância**. O arquivo JSON contém:

- a grade já convertida, incluindo paredes que você tenha editado;
- a origem definida no tabuleiro e o destino escolhido;
- as regras de quatro direções e custo 1;
- o nome e o caminho da fonte, e o SHA-256 do arquivo original;
- as dimensões originais e o deslocamento do recorte;
- um indicador de edição.

**Abrir mapa** também aceita esse JSON, permitindo repetir a mesma entrada. A origem salva é a origem definida para o percurso, não a posição intermediária da animação. Se você quiser usar a posição atual como origem de uma nova instância, reposicione a origem nessa casa antes de salvar.

Se os pontos ainda não foram selecionados, o destino poderá ser nulo. Para preparar um experimento, selecione o destino antes de exportar. Para voltar ao tabuleiro didático original de 12 × 18, use **Restaurar tabuleiro**.

Também foram incluídas **12 instâncias prontas** em `datasets/artificial_random/instancias`: recortes centrais de 3 × 3, 4 × 4, 5 × 5 e 12 × 18 para cada uma das três séries. Você pode abri-las diretamente com **Abrir mapa**. A origem é a primeira casa livre e o destino a última, em ordem de linha e coluna, sem selecionar os casos pelo resultado da busca. `indice.json` registra cada entrada e seu custo ortogonal de referência calculado por BFS.

## 6. O que a conversão faz no código

O novo módulo `mapas_movingai.py` concentra a leitura e a conversão, independentemente da janela. O fluxo é:

```text
arquivo .map → validar cabeçalho e dimensões → converter símbolos
             → Mapa → grade de '.' e '#' → grafo → Dijkstra
```

O arquivo usa um cabeçalho como:

```text
type octile
height 3
width 5
map
..@..
.T...
.....
```

Para nosso modelo, a grade convertida será:

```text
..#..
.#...
.....
```

As posições permanecem iguais. O carregamento não adiciona nem remove linhas, não redimensiona as casas e não autoriza diagonais. O grafo é criado pela função `grafo_da_grade`, que já existia no projeto.

| Função | Decisão e finalidade |
|---|---|
| `ler_mapa` | Valida o formato e traduz os símbolos para o modelo da aplicação. |
| `recortar` | Seleciona uma janela e guarda sua posição no original. |
| `ler_cenarios` | Lê os casos e converte `(x, y)` para `(linha, coluna)`. |
| `pontos_locais` | Converte pontos originais para um recorte e valida a passagem. |
| `salvar_instancia` | Registra uma entrada com regras e procedência explícitas. |
| `ler_instancia` | Reabre essa entrada e verifica as regras e os pontos. |

## 7. O que mudou na interface

As dimensões deixaram de ser usadas como constantes em todos os métodos. `self.rows` e `self.cols` agora definem o tamanho da grade carregada. A conversão de cliques, os limites do cursor e o desenho usam essas dimensões.

Para mapas acima de 6.000 células, desenhamos uma imagem de visão geral em vez de criar um objeto gráfico para cada casa. Isso evita centenas de milhares de objetos no Canvas. O limite é uma decisão de apresentação e não altera a entrada do algoritmo.

A busca em mapas grandes é executada em uma tarefa de fundo, com uma cópia da entrada. A janela consulta periodicamente se a tarefa terminou. A tarefa não acessa componentes Tkinter. Se você mudar o mapa, os pontos ou as paredes, o resultado anterior é descartado; uma tarefa já iniciada pode terminar internamente, mas não altera o novo tabuleiro.

O valor **Busca: ... ms** mede a chamada de Dijkstra, incluindo validação e reconstrução, depois de construir o grafo. Ele é informativo para uma execução. A avaliação científica precisará de repetições, ambiente documentado, registro de resultados e instrumentação equivalente da força bruta.

## 8. Como usar os dados no trabalho

O dataset público passa a fornecer matrizes de obstáculos e pares de origem/destino. Para a comparação com força bruta, use recortes pequenos e preserve os JSONs de cada instância. A família Random permite estudar mapas com diferentes estruturas locais e proporções de obstáculos observadas.

Os números nos nomes das séries são rótulos da fonte. Meça a densidade em cada mapa ou recorte. No subconjunto baixado, a série 40 apresenta aproximadamente 60% de células bloqueadas; esse valor foi observado nos arquivos, e não presumido pelo nome.

O recorte central oferecido pelo botão é um exemplo de interface, não uma amostra suficiente para concluir o estudo. O conjunto experimental deverá fixar múltiplas regiões e pares de pontos antes da coleta principal, incluindo casos sem rota. Instâncias editadas manualmente devem ser identificadas como derivadas.

Esta etapa implementa a integração do dataset e continua usando Dijkstra. A enumeração exaustiva e o executor dos experimentos serão as próximas partes do comparativo definido na proposta.

## 9. Fonte e reprodução

Consulte `datasets/artificial_random/LEIA-ME.md` para a atribuição, a licença e os números dos arquivos. `manifesto.json` registra os downloads e hashes. Os arquivos públicos não foram sobrescritos pela conversão.

Para executar as verificações da integração:

```text
python -B testes/verificar_datasets.py
```

As verificações usam os três mapas, comparam 192 buscas em recortes contra BFS, conferem importação, recortes, exportação, cenários e cancelamento de resultados antigos. Também verificam a busca em uma instância do mapa completo. Necessitam de Python com Tkinter funcional.

Fontes: [Artificial Benchmarks](https://www.movingai.com/benchmarks/grids.html), [Random maps](https://www.movingai.com/benchmarks/random/index.html), [formatos Moving AI](https://www.movingai.com/benchmarks/formats.html).
