# Tabuleiro de caminho mínimo

Aplicação didática em Python para estudar caminhos mínimos em grafos, com um tabuleiro visto de cima, obstáculos e animação da rota. O projeto faz parte de um estudo de Otimização e Complexidade de Algoritmos inspirado em *The Algorithm Design Manual*, de Steven Skiena.

## Estado atual

- Dijkstra com fila de prioridade baseada em heap.
- Opção Força bruta visível e desativada; implementação prevista para a próxima etapa.
- 70 mapas Random de 512 × 512 do Moving AI Lab.
- Zoom, deslocamento do mapa e animação com velocidade ajustável.
- Botão Mini 12 × 18 para o tabuleiro didático original.
- Botão Editar para habilitar alterações de destino, origem e obstáculos.
- Informações do mapa carregado e percentual de células bloqueadas em destaque.

Cada célula livre corresponde a um vértice. Movimentos ortogonais entre células vizinhas custam 1; não há diagonais. Os mapas do dataset usam origem e destino nos cantos quando livres. Se um canto estiver bloqueado, a aplicação informa a célula livre mais próxima utilizada. As paredes originais são preservadas.

## Executar

Requer **Python 3.10 ou posterior com Tkinter**. Não há bibliotecas externas a instalar.

Na pasta do projeto:

```text
python tabuleiro.py
```

No Windows, também é possível abrir **Abrir tabuleiro.bat** com um duplo clique.

Selecione um mapa e aperte **Carregar mapa**, ou abra o tabuleiro fixo com **Mini 12 × 18**. Use **Editar** para habilitar os três modos de alteração. Aperte **Play** para calcular e percorrer a rota. A roda do mouse aplica zoom; o botão direito arrasta a vista.

## Estrutura

| Caminho | Conteúdo |
|---|---|
| `tabuleiro.py` | Interface, controles, zoom e animação. |
| `roteamento.py` | Grafo da grade, Dijkstra e BFS para conferência. |
| `mapas_movingai.py` | Importação e validação de mapas e instâncias. |
| `datasets/artificial_random/` | Mapas originais, atribuição, manifestos e cenários anteriores. |
| `testes/` | Verificações dos dados, interface, zoom e animação. |
| `material_do_manual/` | Etapas didáticas da construção inicial. |

`work/` e `outputs/` são pastas locais de arquivos gerados e ficam fora do histórico Git. O código, os mapas e os manuais da raiz são versionados.

## Documentação

- [Guia de uso](Como%20usar%20o%20tabuleiro.md).
- [Manual da versão atual](Manual_atualizacao_mapas_zoom_animacao.md).
- [Manual da construção inicial](Manual_de_implementacao_do_tabuleiro.md).
- [Proposta do estudo](Proposta_Python_Dijkstra_Forca_Bruta.md).
- [Resumo do primeiro entregável](Resumo_Entregavel_1_Dijkstra_Forca_Bruta.md).

## Verificações

```text
python -B testes/verificar_datasets.py
python -B testes/verificar_zoom_animacao.py
```

As verificações exigem Tkinter funcional e podem abrir janelas. Incluem importação, hashes dos 70 mapas, comparação de custos entre Dijkstra e BFS, casos sem rota, cliques após zoom e controles da animação.

O tempo mostrado como **Busca** mede Dijkstra após construir o grafo. A animação é uma etapa separada. Como os pesos são 1, BFS também encontra o caminho mínimo; aqui é usada como referência de validação.

## Dados e referências

Os mapas pertencem à família [Random maps do Moving AI Lab](https://www.movingai.com/benchmarks/random/index.html). A atribuição e as condições de uso dos dados estão em [datasets/artificial_random/LEIA-ME.md](datasets/artificial_random/LEIA-ME.md). Os manifestos registram os hashes dos arquivos originais.

Referência do estudo: SKIENA, Steven S. *The Algorithm Design Manual*. 2. ed. Springer, 2008, capítulo 6, caminhos mínimos e Dijkstra.
