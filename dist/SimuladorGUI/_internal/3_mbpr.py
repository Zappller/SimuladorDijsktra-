"""
================================================================================
PROGRAMA 3: ROTEAMENTO COM FUNÇÃO MBPR (MODIFIED BPR) EM ARACAJU (PONTO A ➔ UFS)
Trabalho de Teoria dos Grafos - Roteamento com Tráfego, Filas e Semáforos
================================================================================
A função MBPR (Modified Bureau of Public Roads) aprimora a função BPR tradicional
para resolver duas limitações críticas da BPR clássica em redes viárias urbanas:

1. REGIME DUPLO DE SUPERSATURAÇÃO (Dual-Regime / Akçelik / NCHRP 387):
   Quando a demanda de tráfego excede a capacidade (V/C > 1.0), a BPR padrão
   subestima a formação de filas estagnadas. A MBPR incorpora o atraso físico de
   acumulação e dispersão de filas veiculares.

2. PENALIDADE DE INTERSEÇÃO E SEMÁFOROS (Webster / HCM Delay Model):
   Em cidades reais como Aracaju, a maior parte do atraso urbano não ocorre no
   meio do quarteirão, mas sim nos cruzamentos semaforizados (fase vermelha).
   A MBPR consulta a base cadastral de semáforos de Aracaju (traffic_signals) e
   soma o atraso de ciclo semafórico dependente da taxa de saturação.

                      t_MBPR = t_trecho(V/C) + d_semaforo(V/C)

Este programa executa simultaneamente as 3 metodologias (Dijkstra, BPR e MBPR)
e produz uma simulação comparativa com uma corrida de 3 veículos até a UFS.
================================================================================
"""

import sys
import os
import webbrowser
import grafo_utils as gu


def imprimir_cabecalho():
    print("*" * 78)
    print("      PROGRAMA 3: ROTEAMENTO COM FUNÇÃO MBPR (MODIFIED BPR)")
    print("     MODELAGEM AVANÇADA COM TRÁFEGO, FILAS E SEMÁFOROS EM ARACAJU")
    print("*" * 78)


def menu_nivel_trafego():
    print("\n Escolha o Nível de Intensidade do Tráfego:")
    print(" [1] Horário de Pico da Manhã/Tarde (Intensidade 1.3x - Padrão)")
    print(" [2] Horário de Pico Severo (Intensidade 1.6x - Gargalos Críticos)")
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

    # 4. Rota 1: Dijkstra Clássico
    print("\n[*] [1/3] Calculando Rota com Dijkstra Clássico (Distância Pura)...")
    gu.atualizar_pesos_grafo(G, metodo="dijkstra")
    caminho_dijk, _, stats_dijk = gu.dijkstra_algoritmo(G, no_origem, no_destino, weight_attr="weight")
    metricas_dijk = gu.extrair_metricas_rota(G, caminho_dijk)

    # 5. Rota 2: BPR Tradicional
    print("[*] [2/3] Calculando Rota com BPR Tradicional (Considera V/C mas ignora semáforos)...")
    gu.atualizar_pesos_grafo(G, metodo="bpr")
    caminho_bpr, _, stats_bpr = gu.dijkstra_algoritmo(G, no_origem, no_destino, weight_attr="weight")
    metricas_bpr = gu.extrair_metricas_rota(G, caminho_bpr)

    # 6. Rota 3: MBPR Modificado (Atraso de trecho + Filas de supersaturação + Semáforos)
    print("[*] [3/3] Calculando Rota com MBPR (Otimização Completa: V/C + Filas + Semáforos)...")
    gu.atualizar_pesos_grafo(G, metodo="mbpr")
    caminho_mbpr, _, stats_mbpr = gu.dijkstra_algoritmo(G, no_origem, no_destino, weight_attr="weight")
    metricas_mbpr = gu.extrair_metricas_rota(G, caminho_mbpr)

    # 7. Exibir Tabela Analítica Completa
    print("\n" + "=" * 84)
    print("                     QUADRO COMPARATIVO DAS 3 METODOLOGIAS")
    print("=" * 84)
    header = f" {'Métrica':<32} | {'1. Dijkstra':<13} | {'2. BPR Trad.':<13} | {'3. MBPR (Ótimo)':<15}"
    print(header)
    print("-" * 84)
    print(f" {'Distância Física Total':<32} | {metricas_dijk['distancia_km']:>10.2f} km | {metricas_bpr['distancia_km']:>10.2f} km | {metricas_mbpr['distancia_km']:>12.2f} km")
    print(f" {'Tempo em Fluxo Livre (t0)':<32} | {metricas_dijk['tempo_fluxo_livre_min']:>10.1f} min | {metricas_bpr['tempo_fluxo_livre_min']:>10.1f} min | {metricas_mbpr['tempo_fluxo_livre_min']:>12.1f} min")
    print(f" {'Tempo BPR (Sem Semáforo)':<32} | {metricas_dijk['tempo_bpr_min']:>10.1f} min | {metricas_bpr['tempo_bpr_min']:>10.1f} min | {metricas_mbpr['tempo_bpr_min']:>12.1f} min")
    print(f" {'Tempo Efetivo MBPR (Real)':<32} | {metricas_dijk['tempo_mbpr_min']:>10.1f} min | {metricas_bpr['tempo_mbpr_min']:>10.1f} min | {metricas_mbpr['tempo_mbpr_min']:>12.1f} min 🏆")
    print(f" {'Cruzamentos com Semáforos':<32} | {metricas_dijk['num_semaforos']:>10d}     | {metricas_bpr['num_semaforos']:>10d}     | {metricas_mbpr['num_semaforos']:>12d} 🚦")
    print(f" {'Total de Nós Percorridos':<32} | {metricas_dijk['num_nos']:>10d} nós | {metricas_bpr['num_nos']:>10d} nós | {metricas_mbpr['num_nos']:>12d} nós")
    print("=" * 84)

    economia_dijk = metricas_dijk["tempo_mbpr_min"] - metricas_mbpr["tempo_mbpr_min"]
    economia_bpr = metricas_bpr["tempo_mbpr_min"] - metricas_mbpr["tempo_mbpr_min"]
    semaforos_evitados = metricas_dijk["num_semaforos"] - metricas_mbpr["num_semaforos"]

    print("\n[+] DIAGNÓSTICO CIENTÍFICO DA SIMULAÇÃO:")
    print(f"  1. O algoritmo MBPR economizou {economia_dijk:.1f} minutos em comparação ao Dijkstra Clássico")
    print(f"     (uma redução de {(economia_dijk / metricas_dijk['tempo_mbpr_min']) * 100:.1f}% no tempo total de viagem).")
    print(f"  2. O MBPR evitou {semaforos_evitados} cruzamentos com semáforos em relação ao caminho mais curto.")
    print("  3. Enquanto o BPR tradicional tende a escolher avenidas principais com alta capacidade")
    print("     (mas repletas de semáforos que atrasam a viagem), o MBPR equilibra perfeitamente")
    print("     a capacidade da via com o atraso de controle semafórico.")

    # 8. Gerar Simulação Visual Interativa (HTML + Leaflet + Corrida de 3 Veículos)
    print("\n[*] Gerando simulação interativa completa (Grande Prêmio das 3 Rotas)...")
    arquivo_html = "simulacao_mbpr.html"
    gu.gerar_simulacao_mbpr_html(
        G,
        caminho_dijk, metricas_dijk,
        caminho_bpr, metricas_bpr,
        caminho_mbpr, metricas_mbpr,
        nome_origem, arquivo_html,
        coord_origem=coords_origem
    )

    # 9. Gerar Gráficos Estatísticos com Matplotlib
    arquivo_png = "simulacao_mbpr.png"
    gu.plotar_grafico_comparativo(metricas_dijk, metricas_bpr, metricas_mbpr, arquivo_png)

    # 10. Abrir navegador
    caminho_abs = os.path.abspath(arquivo_html)
    print(f"\n[+] Abrindo simulação no navegador...")
    webbrowser.open(f"file:///{caminho_abs}")

    print("\n" + "=" * 84)
    print(f" Simulação MBPR concluída com sucesso!")
    print(f" - Mapa Interativo com Corrida dos 3 Carros: {arquivo_html}")
    print(f" - Gráfico Comparativo Triplo: {arquivo_png}")
    print("=" * 84)


if __name__ == "__main__":
    main()
