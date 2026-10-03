# Projeto Python — tabuleiro de caminho mínimo

Pasta atual: `D:\algoritimos\tabuleiro`.

Abra **Abrir tabuleiro.bat**. Leia **Como usar o tabuleiro.md** e **Manual_atualizacao_mapas_zoom_animacao.md**.

A aplicação inclui os 70 mapas do `random-map.zip`, zoom com navegação, pontos automáticos nos cantos quando livres e animação com duração programada de até oito segundos em 1×. Requer Python 3.10+ com Tkinter; sem bibliotecas extras.

Código e datasets estão nesta raiz. Documentos de estudo e as etapas iniciais foram preservados. `outputs` guarda o pacote da versão atual e `work` guarda resultados de verificação. A cópia anterior em C: foi preservada.

A seção Algoritmo oferece Dijkstra selecionado e Força bruta desativada por enquanto. A interface calcula com Dijkstra. Os testes usam BFS como referência. A força bruta e o executor dos experimentos comparativos ainda não estão implementados nesta aplicação.

## Estrutura

- `tabuleiro.py`, `roteamento.py`, `mapas_movingai.py`: implementação atual.
- `datasets/artificial_random`: mapas originais, cenários anteriores, instâncias e manifestos.
- `testes`: verificações da aplicação.
- `material_do_manual`: etapas didáticas anteriores.
- `outputs`: pacote distribuível da versão atual.
- `work`: registros das verificações e logs locais.

Os documentos de proposta preservam o planejamento do estudo. A integração inicial continha três mapas; o pacote atual acrescenta os outros 67, mantendo os cenários anteriores.

O botão Mini 12 × 18 abre o tabuleiro didático original. Use Editar para habilitar as opções de destino, origem e obstáculos. O nome e a densidade do mapa efetivamente carregado aparecem em destaque abaixo da seleção de mapa.
