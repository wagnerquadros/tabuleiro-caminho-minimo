# Tabuleiro de caminho mínimo

Abra **Abrir tabuleiro.bat** com um duplo clique. Mantenha os arquivos `tabuleiro.py` e `roteamento.py` na mesma pasta.

1. O ponto azul, marcado com P, é o personagem.
2. Clique em uma casa livre. O marcador amarelo D indica o destino.
3. Aperte **Play**. A linha verde mostra a rota mínima e o personagem a percorre.
4. Use **Pausar / Continuar** para observar o percurso.
5. Ao chegar, clique em outro destino. O próximo percurso parte da posição atual.

**Reiniciar percurso** devolve o personagem à origem, preservando o destino e as paredes. **Mover origem** permite escolher outra posição inicial. Em **Editar obstáculos**, cada clique adiciona ou remove uma parede; depois volte a **Marcar destino**. Uma alteração durante a animação interrompe a rota, para que ela seja recalculada com o mapa atualizado. **Restaurar tabuleiro** recupera o cenário inicial.

O teclado também funciona: clique no tabuleiro para dar foco, escolha uma casa com as setas e pressione Enter. Espaço inicia ou pausa o percurso.

## Como a solução funciona

O tabuleiro tem 12 linhas e 18 colunas. Cada casa livre vira um vértice. Casas livres vizinhas são conectadas por arestas de custo 1, nos quatro sentidos ortogonais. Não há diagonais nem movimentos através de obstáculos.

O clique converte a posição do mouse em uma célula. Ao apertar Play, a interface transforma o tabuleiro em um grafo e chama `dijkstra_heap`, implementado em `roteamento.py`. O algoritmo devolve a menor quantidade de movimentos e a sequência de casas.

A interface desenha essa sequência e anima o personagem entre as casas. A velocidade da animação serve apenas para visualizar o resultado; ela não é o tempo de processamento do algoritmo. Em caso de empate, uma das rotas mínimas é escolhida.

Se não existir caminho, o personagem permanece parado e aparece a mensagem **Sem rota**. Para demonstrar esse caso, selecione a casa da linha 10, coluna 3, dentro do pequeno recinto fechado do mapa inicial. Se origem e destino coincidirem, o custo é zero.

## Relação com a análise assintótica

Se n é a quantidade de casas livres e m é a quantidade de movimentos dirigidos permitidos, Dijkstra com heap tem limite de tempo O((n + m) log n) para este grafo simples. Como cada casa tem no máximo quatro vizinhos, m = O(n), resultando em O(n log n) para a busca. A memória auxiliar desta implementação é O(n + m), que aqui é O(n).

Ler a grade e construir o grafo também custa O(L × C), para L linhas e C colunas. O custo completo inclui essa etapa, mesmo quando muitas células são obstáculos. A animação é uma etapa de apresentação separada; se o caminho tem k movimentos, são exibidos oito quadros por movimento.

Como todos os pesos são 1, BFS também encontraria uma rota ótima em O(n + m). Mantivemos Dijkstra para conectar a interface à solução estudada e permitir uma futura extensão com custos diferentes por terreno.

Para executar pelo terminal, use `python tabuleiro.py`. Requer Python 3.10 ou posterior com Tkinter, sem bibliotecas externas. Nesta máquina, o inicializador usa a instalação Python 3.11 já disponível.
