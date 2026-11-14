# Grafos

Projeto da disciplina **Introdução à Teoria dos Grafos (UFS)**. Tem dois exemplos simples de grafos e dois programas que calculam a rota de carro entre **Casa (A)** e a **UFS (B)** no mapa real de Aracaju.

## Arquivos

| Arquivo | O que faz |
|---|---|
| `Grafo Simples.py` | Desenha um grafo simples e conexo com 3 vértices (1 ligado a 2 e a 3). |
| `Caminho.py` | Desenha o mesmo grafo e destaca em vermelho o caminho de 2 até 3. |
| `Dijkstra/Dijkstra.py` | Rota mais **curta em distância** (Dijkstra, peso = comprimento da rua). |
| `BPR/BPR.py` | Rota mais **rápida com congestionamento simulado** (função BPR). |
| `aracaju.graphml` | Mapa das ruas de Aracaju já baixado, para não precisar baixar de novo. |

## Instalação

Precisa de Python 3.10 ou mais novo. Na pasta `Grafos`:

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS
pip install -r requirements.txt
```

## Como usar

**Rode sempre de dentro da pasta `Grafos`**, porque os programas procuram o `aracaju.graphml` na pasta onde o comando é executado.

### Exemplos de grafo

```bash
python "Grafo Simples.py"
python Caminho.py
```

Abre uma janela com o desenho do grafo.

### Rota Casa → UFS

```bash
python Dijkstra/Dijkstra.py
python BPR/BPR.py
```

Cada programa:

1. Carrega o mapa de `aracaju.graphml` (se o arquivo não existir, baixa do OpenStreetMap; precisa de internet e pode demorar).
2. Calcula a rota e mostra no terminal a distância (o BPR também mostra o tempo com congestionamento e o tempo em fluxo livre).
3. Salva o mapa interativo em `rota.html` e abre no navegador.
4. Salva a imagem da rota em `rota.png` e mostra numa janela.

Os dois programas gravam no mesmo `rota.html` e `rota.png`, então o último que rodar sobrescreve o anterior.

### Trocar origem e destino

No começo de `Dijkstra.py` e `BPR.py`, altere as coordenadas (latitude, longitude):

```python
casa = (-10.968831195960583, -37.0856515783314)   # A
ufs  = (-10.924758256888392, -37.10505198873507)  # B
```

Os pontos precisam estar dentro da área do mapa salvo (raio de 4,5 km em volta do ponto médio). Para uma área diferente, apague `aracaju.graphml` e rode de novo para baixar um mapa novo.

## Sobre o BPR

O tempo de cada rua é calculado pela fórmula do *Bureau of Public Roads*:

```
T = T0 · (1 + α · (V / C)^β)     com α = 0,15 e β = 4
```

- `T0`: tempo em fluxo livre (comprimento ÷ velocidade da via)
- `C`: capacidade da via (veículos/hora por faixa × número de faixas)
- `V`: volume de carros, **simulado** aleatoriamente entre 30% e 120% da capacidade (com `random.seed(42)`, então o resultado é sempre o mesmo)
