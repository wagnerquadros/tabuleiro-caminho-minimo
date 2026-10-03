# Tabuleiro de caminho mínimo — versão com mapas, zoom e animação rápida

O projeto atual está em `D:\algoritimos\tabuleiro`. Requer Python 3.10 ou posterior com Tkinter. Não requer instalação de bibliotecas adicionais. Nesta máquina, a versão foi verificada com Python 3.14.

## Como abrir e usar

1. Abra **Abrir tabuleiro.bat** com um duplo clique. O aplicativo inicia no mapa `random512-20-0.map`.
2. A lista **Mapa** contém os **70 mapas** do `random-map.zip` enviado. Selecione um nome e aperte **Carregar mapa** para abrir o mapa inteiro, com 512 linhas e 512 colunas. Logo abaixo, a área destacada mostra o mapa efetivamente carregado, suas dimensões, casas livres, obstáculos e percentual bloqueado, antes da seção Algoritmo.
3. Na seção **Algoritmo**, **Dijkstra** fica selecionado. **Força bruta** aparece desativada por enquanto.
4. Origem e destino são definidos automaticamente: linha 1/coluna 1 e última linha/última coluna. Se um canto for um obstáculo, usamos a célula livre mais próxima pela distância Manhattan e informamos as posições utilizadas. As paredes do dataset são preservadas. Os pontos não são escolhidos conforme a existência de uma rota.
5. Aperte **Play**. A linha verde mostra a rota e o ponto azul percorre o caminho. O número em **Menor caminho** é o custo da rota, em movimentos.
6. Use **Pausar / Continuar** para interromper e retomar o movimento. **Concluir animação** mostra imediatamente a chegada.

**Zoom:** use a roda do mouse sobre o mapa ou os botões **+ / −**. A roda aproxima a região sob o ponteiro. **Ajustar mapa** volta à visão geral. Para navegar no mapa ampliado, arraste com o botão direito ou use as barras de rolagem. Os botões **Origem / Destino** centralizam os pontos. O zoom conserva todas as células e obstáculos.

**Velocidade:** em 1×, a duração programada é 0,12 segundo por movimento, limitada a oito segundos por percurso. Em 2×, o limite é quatro segundos; em 4×, dois segundos. **Instantânea** exibe diretamente o resultado. A opção escolhida vale no próximo Play. Pausas não consomem o tempo restante. A duração real depende da capacidade da máquina de atualizar a janela.

Marque **Seguir personagem no zoom** para acompanhar o ponto azul durante o percurso ampliado. Essa opção pode deslocar a vista conforme o personagem sai da região visível.

**Mini 12 × 18** abre o tabuleiro didático original, com 41 obstáculos, origem na linha 3/coluna 3 e destino a escolher. Esse é o mapa que antes era aberto por **Restaurar tabuleiro**. Para marcar o destino, clique em **Editar**. O Mini é um mapa fixo, independente da seleção do dataset.

## Alterar pontos e obstáculos

Clique em **Editar** para habilitar **Marcar destino**, **Mover origem** e **Editar obstáculos**. Em **Marcar destino**, clique em uma célula livre para mudar o destino. **Mover origem** reposiciona o ponto inicial. **Editar obstáculos** adiciona ou remove uma parede. Uma edição interrompe a rota, para que seja recalculada com a nova entrada. **Concluir edição** desabilita essas opções e protege o tabuleiro contra alterações por clique ou Enter. Ao carregar outro mapa ou o Mini, a edição volta a ficar desabilitada.

Depois da chegada, você pode usar **Editar** para definir outro destino e iniciar a próxima busca na posição atual do personagem. **Reiniciar percurso** retorna à origem definida e preserva o destino.

Para usar o teclado, dê foco ao mapa com um clique. As setas movem o cursor, Enter seleciona a célula quando a edição está habilitada e Espaço inicia ou pausa. Ctrl+0 ajusta a visão geral.

Se aparecer **Sem rota**, origem e destino estão desconectados nas regras do estudo. O aplicativo não abre paredes para criar uma passagem. Se os pontos coincidirem, o custo é zero.

## Mapas incluídos

Use a lista **Mapa** e **Carregar mapa** para selecionar os arquivos incluídos em `datasets/artificial_random`. O ZIP enviado já foi integrado ao projeto.

Para acrescentar outro mapa compatível, coloque o arquivo `.map` nessa pasta e reabra o aplicativo. A interface apresenta o catálogo, a opção **Mini 12 × 18** e os controles do tabuleiro.

## Onde estudar o código

- `tabuleiro.py`: janela, controles, conversão de cliques, zoom e animação.
- `mapas_movingai.py`: validação e conversão dos arquivos, recortes e instâncias.
- `roteamento.py`: construção do grafo e Dijkstra com heap; inclui BFS para conferência.
- `Manual_atualizacao_mapas_zoom_animacao.md`: passo a passo da versão atual e explicação das decisões.
- `Manual_de_implementacao_do_tabuleiro.md` e PDF: material das etapas iniciais, com interface anterior.

**Busca: ... ms** mede a chamada de Dijkstra, incluindo sua validação e reconstrução, depois de construir o grafo. Não inclui carregar arquivos, construir o grafo ou animar. Esse valor isolado é demonstrativo; a avaliação experimental do trabalho exige repetições e condições documentadas.

## Verificações

Na pasta do projeto, execute:

```text
python -B testes/verificar_datasets.py
python -B testes/verificar_zoom_animacao.py
```

Foram verificados os 70 arquivos, a conversão, os pontos nos cantos, o zoom e os cliques após rolagem, a pausa e a chegada, a exportação e os cenários. As verificações comparam Dijkstra com BFS em 192 consultas de recortes e nos mapas completos das séries 10, 20 e 40. Também conferem que os objetos gráficos não são recriados a cada quadro.
