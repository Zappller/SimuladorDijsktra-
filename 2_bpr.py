"""
================================================================================
PROGRAMA 2: ROTEAMENTO DINÂMICO COM FUNÇÃO BPR EM ARACAJU (PONTO A ➔ UFS)
Trabalho de Teoria dos Grafos - Roteamento Viário com Congestionamento
================================================================================
A função BPR (Bureau of Public Roads - 1964) é o modelo clássico de engenharia de
transportes para calcular o tempo de viagem de um trecho viário considerando o
volume de veículos (V) e a capacidade da via (C):

       t = t0 * [ 1 + alpha * (V / C)^beta ]

Onde:
  - t0: Tempo de viagem em fluxo livre (distância / velocidade regulamentar)
  - V : Volume de veículos por hora na via
  - C : Capacidade prática da via em veículos por hora
  - alpha = 0.15, beta = 4.0 (parâmetros de calibração padrão)

Este programa simula o tráfego nos horários de pico de Aracaju e compara a rota
ingênua de menor distância (Dijkstra) com a rota adaptativa (BPR), demonstrando
como o BPR desvia de artérias saturadas para reduzir o tempo de chegada à UFS.
================================================================================
"""

import sys
import os
import webbrowser
import matplotlib.pyplot as plt
import grafo_utils as gu


def imprimir_cabecalho():
    print("*" * 75)
    print("       PROGRAMA 2: ROTEAMENTO COM FUNÇÃO BPR (BUREAU OF PUBLIC ROADS)")
    print("               MODELAGEM DE CONGESTIONAMENTO EM ARACAJU ➔ UFS")
    print("*" * 75)


def menu_nivel_trafego():
    print("\n Escolha o Nível de Intensidade do Tráfego:")
    print(" [1] Horário de Pico da Manhã/Tarde (Intensidade 1.3x - Padrão)")
    print(" [2] Horário de Pico Severo (Intensidade 1.6x - Engarrafamentos Críticos)")
    print(" [3] Fluxo Moderado (Intensidade 0.9x)")
    opcao = input(" Escolha [1-3] (Enter para '1'): ").strip()
    if opcao == "2":
        return 1.6
    elif opcao == "3":
        return 0.9
    else:
        return 1.3


def main():
    imprimir_cabecalho()

    # 1. Carregar grafo de Aracaju
    G = gu.carregar_grafo_aracaju("aracaju.graphml")

    # 2. Selecionar Ponto A de Partida
    no_origem, nome_origem, coords_origem = gu.menu_selecao_origem(G)
    no_destino = gu.UFS_DEFAULT_NODE
    nome_destino = gu.UFS_NAME

    # 3. Aplicar Carregamento de Tráfego Realista em Aracaju
    nivel_pico = menu_nivel_trafego()
    gu.aplicar_trafego_realista(G, nivel_pico=nivel_pico)

    # 4. Rota 1: Dijkstra Clássico (Menor Distância Física, ignora congestionamento)
    print("\n[*] [1/2] Calculando Rota de Dijkstra Clássico (Distância Mínima)...")
    gu.atualizar_pesos_grafo(G, metodo="dijkstra")
    caminho_dijk, _, stats_dijk = gu.dijkstra_algoritmo(G, no_origem, no_destino, weight_attr="weight")
    metricas_dijk = gu.extrair_metricas_rota(G, caminho_dijk)

    # 5. Rota 2: BPR (Otimização considerando tempo de viagem congestionado)
    print("[*] [2/2] Calculando Rota com Função BPR (Minimização de Tempo com Tráfego)...")
    gu.atualizar_pesos_grafo(G, metodo="bpr")
    caminho_bpr, _, stats_bpr = gu.dijkstra_algoritmo(G, no_origem, no_destino, weight_attr="weight")
    metricas_bpr = gu.extrair_metricas_rota(G, caminho_bpr)

    # 6. Exibir Análise Comparativa
    print("\n" + "=" * 78)
    print("               QUADRO COMPARATIVO: DIJKSTRA vs BPR")
    print("=" * 78)
    print(f" {'Métrica':<35} | {'Dijkstra (Distância)':<18} | {'BPR (Tempo/Tráfego)':<18}")
    print("-" * 78)
    print(f" {'Distância Física Total':<35} | {metricas_dijk['distancia_km']:>14.2f} km | {metricas_bpr['distancia_km']:>14.2f} km")
    print(f" {'Tempo em Fluxo Livre (t0)':<35} | {metricas_dijk['tempo_fluxo_livre_min']:>14.1f} min | {metricas_bpr['tempo_fluxo_livre_min']:>14.1f} min")
    print(f" {'Tempo com Trânsito (BPR)':<35} | {metricas_dijk['tempo_bpr_min']:>14.1f} min | {metricas_bpr['tempo_bpr_min']:>14.1f} min")
    print(f" {'Atraso Médio por Congestionamento':<35} | {metricas_dijk['tempo_bpr_min'] - metricas_dijk['tempo_fluxo_livre_min']:>14.1f} min | {metricas_bpr['tempo_bpr_min'] - metricas_bpr['tempo_fluxo_livre_min']:>14.1f} min")
    print(f" {'Cruzamentos Percorridos':<35} | {metricas_dijk['num_nos']:>14d} nós | {metricas_bpr['num_nos']:>14d} nós")
    print(f" {'Semáforos Encontrados':<35} | {metricas_dijk['num_semaforos']:>14d}     | {metricas_bpr['num_semaforos']:>14d}    ")
    print("=" * 78)

    diff_tempo = metricas_dijk["tempo_bpr_min"] - metricas_bpr["tempo_bpr_min"]
    if diff_tempo > 0.05:
        print(f"\n[+] ANÁLISE BPR: A rota BPR economiza {diff_tempo:.1f} minutos em relação ao Dijkstra!")
        print("    Embora o trajeto do BPR possa ser ligeiramente mais longo em distância física,")
        print("    ele desviou estrategicamente de eixos altamente saturados (V/C > 1.0), chegando mais rápido à UFS.")
    else:
        print("\n[+] ANÁLISE BPR: Em condições de baixa saturação, a rota de menor distância coincide com a de menor tempo.")

    # 7. Gerar Simulação Visual Interativa (HTML + Leaflet + Corrida de Veículos)
    print("\n[*] Gerando simulação interativa com corrida de dois veículos em tempo real...")
    arquivo_html = "simulacao_bpr.html"
    gu.gerar_simulacao_bpr_html(G, caminho_dijk, metricas_dijk, caminho_bpr, metricas_bpr, nome_origem, arquivo_html)

    # 8. Gerar Gráfico Estático com Matplotlib
    arquivo_png = "simulacao_bpr.png"
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Gráfico 1: Distância x Tempo BPR
    labels = ["Dijkstra Clássico", "Rota BPR"]
    tempos = [metricas_dijk["tempo_bpr_min"], metricas_bpr["tempo_bpr_min"]]
    distancias = [metricas_dijk["distancia_km"], metricas_bpr["distancia_km"]]

    cores = ["#e74c3c", "#3498db"]
    bars = ax1.bar(labels, tempos, color=cores, width=0.5)
    ax1.set_title("Tempo de Viagem no Congestionamento (BPR)", fontsize=12, fontweight="bold")
    ax1.set_ylabel("Minutos")
    for bar in bars:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2.0, yval + 0.3, f"{yval:.1f} min", ha="center", va="bottom", fontweight="bold")
    ax1.grid(axis="y", linestyle="--", alpha=0.5)

    # Gráfico 2: Distância
    bars2 = ax2.bar(labels, distancias, color=cores, width=0.5)
    ax2.set_title("Distância Física Percorrida", fontsize=12, fontweight="bold")
    ax2.set_ylabel("Quilômetros")
    for bar in bars2:
        yval = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2.0, yval + 0.1, f"{yval:.2f} km", ha="center", va="bottom", fontweight="bold")
    ax2.grid(axis="y", linestyle="--", alpha=0.5)

    plt.suptitle("Impacto do Tráfego: Rota mais Curta (Dijkstra) vs Rota mais Rápida (BPR)", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(arquivo_png, dpi=150)
    plt.close()
    print(f"[+] Gráfico comparativo salvo em: {os.path.abspath(arquivo_png)}")

    # 9. Abrir navegador
    caminho_abs = os.path.abspath(arquivo_html)
    print(f"\n[+] Abrindo simulação no navegador...")
    webbrowser.open(f"file:///{caminho_abs}")

    print("\n" + "=" * 78)
    print(f" Simulação BPR concluída com sucesso!")
    print(f" - Mapa Interativo com Corrida de 2 Carros: {arquivo_html}")
    print(f" - Gráfico Comparativo: {arquivo_png}")
    print("=" * 78)


if __name__ == "__main__":
    main()
