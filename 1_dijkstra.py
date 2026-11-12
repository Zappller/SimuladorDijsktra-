"""
================================================================================
PROGRAMA 1: ROTA COM ALGORITMO DE DIJKSTRA EM ARACAJU (PONTO A ➔ UFS)
Trabalho de Teoria dos Grafos - Roteamento Viário
================================================================================
Este programa calcula o caminho de menor distância física entre um Ponto de Partida
(Ponto A) em Aracaju e a Universidade Federal de Sergipe (UFS - Campus São Cristóvão),
utilizando o algoritmo clássico de Dijkstra sobre a malha viária real de Aracaju.
================================================================================
"""

import sys
import os
import webbrowser
import grafo_utils as gu


def imprimir_cabecalho():
    print("*" * 75)
    print("      PROGRAMA 1: ROTA DE MENOR DISTÂNCIA - ALGORITMO DE DIJKSTRA")
    print("                  MALHA VIÁRIA REAL DE ARACAJU ➔ UFS")
    print("*" * 75)


def main():
    imprimir_cabecalho()

    # 1. Carregar grafo de Aracaju
    G = gu.carregar_grafo_aracaju("aracaju.graphml")

    # 2. Selecionar Ponto A de Partida
    no_origem, nome_origem, coords_origem = gu.menu_selecao_origem(G)
    no_destino = gu.UFS_DEFAULT_NODE
    nome_destino = gu.UFS_NAME

    # 3. Configurar pesos do grafo para Dijkstra (Distância física em metros)
    gu.atualizar_pesos_grafo(G, metodo="dijkstra")

    print("\n[*] Executando Algoritmo de Dijkstra com Fila de Prioridade (Heap Binário)...")
    caminho, distancia_total, stats = gu.dijkstra_algoritmo(G, no_origem, no_destino, weight_attr="weight")

    if not caminho:
        print("[!] Erro: Nenhum caminho conectando o ponto escolhido até a UFS foi encontrado!")
        sys.exit(1)

    # 4. Extrair estatísticas da rota calculada
    metricas = gu.extrair_metricas_rota(G, caminho)

    print("\n" + "=" * 75)
    print("                   RESULTADO DA ROTA (DIJKSTRA)")
    print("=" * 75)
    print(f" Origem (Ponto A)        : {nome_origem}")
    print(f" Destino                 : {nome_destino}")
    print(f" Distância Total         : {metricas['distancia_km']:.2f} km ({distancia_total:.1f} metros)")
    print(f" Tempo em Fluxo Livre    : {metricas['tempo_fluxo_livre_min']:.1f} minutos (sem trânsito)")
    print(f" Cruzamentos Percorridos : {metricas['num_nos']} nós")
    print(f" Semáforos no Trajeto    : {metricas['num_semaforos']} cruzamentos semaforizados")
    print(f" Tempo de Execução       : {stats['tempo_ms']:.2f} ms")
    print(f" Nós Expandidos na Busca : {stats['nos_expandidos']} nós")
    print(f" Arestas Relaxadas       : {stats['arestas_relaxadas']} arestas")
    print("=" * 75)

    print("\n[*] Principais Vias e Avenidas Percorridas:")
    for idx, via in enumerate(metricas["nomes_vias"][:15], 1):
        print(f"  {idx:02d}. {via}")
    if len(metricas["nomes_vias"]) > 15:
        print(f"  ... e mais {len(metricas['nomes_vias']) - 15} trechos de acesso.")

    # 5. Gerar Simulação Visual Interativa (HTML + Leaflet + HUD)
    print("\n[*] Gerando simulação interativa no mapa de Aracaju...")
    arquivo_html = "simulacao_dijkstra.html"
    gu.gerar_simulacao_dijkstra_html(G, caminho, metricas, nome_origem, arquivo_html, coord_origem=coords_origem)

    # 6. Gerar Gráficos com Matplotlib
    arquivo_png = "simulacao_dijkstra.png"
    gu.plotar_grafico_dijkstra(G, caminho, metricas, nome_origem, arquivo_png, coord_origem=coords_origem)

    # 7. Abrir no navegador padrão
    caminho_abs = os.path.abspath(arquivo_html)
    print(f"\n[+] Abrindo a simulação interativa no seu navegador...")
    webbrowser.open(f"file:///{caminho_abs}")

    print("\n" + "=" * 75)
    print(f" Simulação gerada com sucesso!")
    print(f" - Mapa Interativo com Animação do Veículo: {arquivo_html}")
    print(f" - Perfil Gráfico de Distância e Velocidades : {arquivo_png}")
    print("=" * 75)


if __name__ == "__main__":
    main()
