"""
================================================================================
PAINEL PRINCIPAL: TRABALHO DE TEORIA DOS GRAFOS EM ARACAJU ➔ UFS
Dijkstra, BPR (Bureau of Public Roads) e MBPR (Modified BPR)
================================================================================
Menu integrador para executar e testar qualquer um dos 3 programas ou rodar
a bateria comparativa completa com simulações interativas.
================================================================================
"""

import sys
import subprocess


def menu_principal():
    while True:
        print("\n" + "=" * 75)
        print("   SISTEMA DE ROTEAMENTO E SIMULAÇÃO VIÁRIA: ARACAJU ➔ UFS")
        print("          Trabalho Acadêmico de Teoria dos Grafos")
        print("=" * 75)
        print(" [1] Executar Programa 1: Rota com Dijkstra Clássico (Menor Distância)")
        print(" [2] Executar Programa 2: Roteamento com BPR (Tempo com Congestionamento)")
        print(" [3] Executar Programa 3: Roteamento com MBPR (Tráfego + Filas + Semáforos)")
        print(" [4] Executar Todos os 3 em Sequência (Terminal)")
        print(" [5] Abrir Interface Gráfica Interativa (GUI Desktop)")
        print(" [0] Sair")
        print("=" * 75)

        opcao = input(" Escolha uma opção [0-5]: ").strip()

        if opcao == "1":
            print("\n>>> Iniciando Programa 1 (Dijkstra)...")
            subprocess.run([sys.executable, "1_dijkstra.py"])
        elif opcao == "2":
            print("\n>>> Iniciando Programa 2 (BPR)...")
            subprocess.run([sys.executable, "2_bpr.py"])
        elif opcao == "3":
            print("\n>>> Iniciando Programa 3 (MBPR)...")
            subprocess.run([sys.executable, "3_mbpr.py"])
        elif opcao == "4":
            print("\n>>> Executando todos os programas...")
            subprocess.run([sys.executable, "1_dijkstra.py"])
            subprocess.run([sys.executable, "2_bpr.py"])
            subprocess.run([sys.executable, "3_mbpr.py"])
        elif opcao == "5":
            print("\n>>> Abrindo Interface Gráfica (Tkinter)...")
            subprocess.run([sys.executable, "gui_simulador.py"])
        elif opcao == "0":
            print("\nEncerrando. Bom trabalho!")
            break
        else:
            print("[!] Opção inválida. Tente novamente.")


if __name__ == "__main__":
    menu_principal()
