# 🚦 Projeto de Teoria dos Grafos: Roteamento Viário em Aracaju ➔ UFS
### Dijkstra Clássico vs BPR (Bureau of Public Roads) vs MBPR (Modified BPR)

Este projeto implementa e compara três abordagens para o problema de roteamento e atribuição de tráfego urbano na malha viária real de **Aracaju - SE**, tendo como destino a **Universidade Federal de Sergipe (UFS - Campus São Cristóvão)** a partir de múltiplos pontos de origem na capital.

---

## 📁 Estrutura de Arquivos

| Arquivo | Descrição |
| :--- | :--- |
| `1_dijkstra.py` | **Programa 1:** Rota de menor distância física utilizando o Algoritmo de Dijkstra clássico com fila de prioridade (`heapq`). Inclui simulação com veículo em movimento. |
| `2_bpr.py` | **Programa 2:** Roteamento adaptativo considerando a função de atraso por volume/capacidade **BPR**. Inclui simulação comparativa (Dijkstra vs BPR). |
| `3_mbpr.py` | **Programa 3:** Roteamento avançado com a função **MBPR** (regime duplo para supersaturação + atraso de semáforos da base de Aracaju). Simulação com corrida dos 3 carros. |
| `main.py` | Menu interativo para executar qualquer um dos programas ou a bateria completa. |
| `grafo_utils.py` | Módulo com o carregamento do `aracaju.graphml`, modelagem de tráfego, cálculos de capacidade/velocidade, semáforos, simulações em Folium/Leaflet e gráficos Matplotlib. |
| `aracaju.graphml` | Grafo real da rede viária de Aracaju extraído do OpenStreetMap (7.039 nós, 17.261 arestas, 257 semáforos). |
| `simulacao_*.html` | Páginas web interativas com mapa real de Aracaju, traçados, telemetria em tempo real e veículos animados. |
| `simulacao_*.png` | Gráficos estáticos de alta resolução com métricas de distância, tempo e semáforos. |

---

## 🧠 Fundamentação Teórica

### 1. Algoritmo de Dijkstra Clássico
Resolve o problema do caminho mínimo em grafos direcionados com pesos não-negativos $G = (V, E)$.
- **Função Objetivo:** Minimiza o somatório da distância física das vias:
  $$\min \sum_{e \in \text{rota}} L_e$$
- **Limitação no Mundo Real:** É estático. Assume que vias largas e diretas (como grandes avenidas) fluem perfeitamente a qualquer hora, ignorando engarrafamentos e filas de semáforo.

---

### 2. Função BPR (*Bureau of Public Roads*, 1964)
Função de atraso utilizada mundialmente em planejamento de transportes para calcular o tempo de percurso em função do volume de tráfego:

$$t = t_0 \left[ 1 + \alpha \left(\frac{V}{C}\right)^\beta \right]$$

Onde:
- $t_0$: Tempo de viagem em fluxo livre ($t_0 = \frac{\text{distância}}{v_{\text{máx}}}$).
- $V$: Volume de tráfego na via (veículos/hora).
- $C$: Capacidade prática da via (veículos/hora), calculada com base na hierarquia viária e número de faixas.
- $\alpha = 0.15$ e $\beta = 4.0$: Parâmetros de calibração padrão.

**Comportamento:** À medida que o tráfego se aproxima da saturação ($V/C \to 1$), o tempo de viagem aumenta de forma exponencial, fazendo o algoritmo desviar de artérias congestionadas.

---

### 3. Função MBPR (*Modified Bureau of Public Roads*)
A BPR tradicional apresenta duas limitações em redes urbanas reais:
1. **Supersaturação ($V/C > 1$):** A BPR clássica não modela adequadamente a formação de filas físicas e bloqueios quando a capacidade é ultrapassada.
2. **Controle Semafórico:** A maior perda de tempo em Aracaju ocorre nos cruzamentos com semáforo, e não apenas no deslocamento contínuo.

A **MBPR** implementada combina o modelo de regime duplo (Akçelik / NCHRP 387) com atraso explícito de semáforos (Webster / HCM):

$$t_{\text{MBPR}} = t_{\text{trecho}}(V/C) + d_{\text{semáforo}}(V/C)$$

- **Atraso no Trecho ($t_{\text{trecho}}$):**
  $$t_{\text{trecho}} = \begin{cases}
  t_0 \left[ 1 + \alpha \left(\frac{V}{C}\right)^\beta \right], & \frac{V}{C} \le 1 \\[8pt]
  t_0 \left[ 1 + \alpha + \alpha \beta \left(\frac{V}{C} - 1\right) + 1.6 \left(\frac{V}{C} - 1\right)^2 \right], & \frac{V}{C} > 1
  \end{cases}$$

- **Atraso Semafórico ($d_{\text{semáforo}}$):**
  Identifica os 257 cruzamentos reais de Aracaju com atributo `highway = traffic_signals`:
  $$d_{\text{semáforo}} = \begin{cases}
  d_0 \left[ 1 + 0.4 \left(\frac{V}{C}\right)^2 \right], & \frac{V}{C} \le 1 \\[8pt]
  d_0 \left[ 1.4 + 2.2 \left(\frac{V}{C} - 1\right) \right], & \frac{V}{C} > 1
  \end{cases}$$
  *(Com tempo médio de espera no vermelho $d_0 = 25$ segundos).*

---

## 📊 Comparativo de Resultados (Exemplo: Centro ➔ UFS)

| Métrica | 1. Dijkstra | 2. BPR Tradicional | 3. MBPR Modificado |
| :--- | :---: | :---: | :---: |
| **Distância Física** | **9.17 km** (Menor) | 9.33 km | 10.26 km |
| **Tempo em Fluxo Livre ($t_0$)** | 10.5 min | 11.2 min | 13.7 min |
| **Tempo Estimado BPR** | 15.7 min | **15.3 min** | 17.5 min |
| **Tempo Real Efetivo (MBPR)** | 25.1 min | 25.3 min | **19.2 min** 🏆 *(Economia de ~6 min)* |
| **Cruzamentos com Semáforos** | 14 semáforos 🛑 | 15 semáforos 🛑 | **Apenas 3 semáforos** 🚦 |

### 💡 Diagnóstico dos Resultados:
- O **Dijkstra** escolhe o caminho geometricamente mais curto, mas cai em avenidas centrais saturadas com 14 semáforos, totalizando **25.1 minutos**.
- O **BPR Tradicional** desvia de trechos com $V/C$ alto, mas por ignorar semáforos, continua pegando avenidas com 15 semáforos.
- O **MBPR** aceita andar **1 km a mais**, porém desvia dos grandes gargalos e evita 11 semáforos, chegando à UFS em **19.2 minutos** (**23.6% mais rápido**).

---

## 🚀 Como Executar

### Pré-requisitos
As bibliotecas necessárias já estão disponíveis no ambiente Python:
```bash
pip install networkx folium matplotlib
```

### Opção 1: Executar via Menu Geral
```bash
python main.py
```

### Opção 2: Executar Programas Individuais
```bash
# Programa 1: Dijkstra Clássico
python 1_dijkstra.py

# Programa 2: Roteamento BPR
python 2_bpr.py

# Programa 3: Roteamento MBPR
python 3_mbpr.py
```

Ao executar qualquer programa, você poderá escolher o ponto de partida (Centro, Shopping Jardins, Terminal D.I.A., Sementeira, Atalaia, Aeroporto, etc.) ou digitar coordenadas personalizadas. O programa abrirá automaticamente a simulação no navegador web padrão.
