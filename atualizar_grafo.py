"""
atualizar_grafo.py - Baixa de novo a malha viaria de Aracaju do OpenStreetMap,
agora cobrindo tambem a zona sul (Aeroporto, Orla de Atalaia, Farolandia).

O aracaju.graphml antigo terminava na latitude -10.9695, cerca de 2 km ao norte
do aeroporto. Por isso as rotas que saiam de la (e da Atalaia) eram completadas
com linhas retas desenhadas a mao.

Uso (precisa de internet, roda uma vez so):
    python atualizar_grafo.py
"""

import os
import shutil
import time

import osmnx as ox

ARQUIVO = "aracaju.graphml"
BACKUP = "aracaju_antigo.graphml"

# Recorte (oeste, sul, leste, norte). O antigo ia de -10.9695 a -10.8886 de
# latitude; aqui o sul vai ate -11.000 para incluir Aeroporto e Atalaia.
OESTE, SUL, LESTE, NORTE = -37.1260, -11.0000, -37.0340, -10.8850

# Pontos que precisam estar cobertos (nome, lat, lon)
CONFERIR = [
    ("Aeroporto", -10.987693832505258, -37.071165206404004),
    ("Orla de Atalaia", -10.991985087477707, -37.051088912564325),
    ("UFS", -10.9251921, -37.1049681),
]


def baixar():
    ox.settings.use_cache = True
    ox.settings.log_console = False
    espera = 10
    for tentativa in range(1, 6):
        try:
            print(f"Baixando mapa do OpenStreetMap (tentativa {tentativa}/5)...")
            try:  # osmnx 2.x
                return ox.graph_from_bbox(bbox=(OESTE, SUL, LESTE, NORTE),
                                          network_type="drive", simplify=True)
            except TypeError:  # osmnx 1.x
                return ox.graph_from_bbox(NORTE, SUL, LESTE, OESTE,
                                          network_type="drive", simplify=True)
        except Exception as e:
            print(f"  Falhou ({type(e).__name__}: {e}). Aguardando {espera}s...")
            time.sleep(espera)
            espera *= 2
    raise SystemExit("Nao foi possivel baixar o mapa. Tente de novo mais tarde.")


def main():
    G = baixar()
    sinais = sum(1 for _, d in G.nodes(data=True)
                 if str(d.get("highway", "")).lower() == "traffic_signals")
    print(f"Mapa baixado: {G.number_of_nodes()} nos, {G.number_of_edges()} arestas, "
          f"{sinais} semaforos.")

    ok = True
    for nome, lat, lon in CONFERIR:
        no, dist = ox.distance.nearest_nodes(G, X=lon, Y=lat, return_dist=True)
        situacao = "OK" if dist <= 400 else "LONGE"
        ok &= dist <= 400
        print(f"  {nome:16s} -> no {no} a {dist:.0f} m  [{situacao}]")
    if not ok:
        raise SystemExit("Algum ponto ficou fora do mapa. Nada foi alterado.")

    if os.path.exists(ARQUIVO) and not os.path.exists(BACKUP):
        shutil.copy2(ARQUIVO, BACKUP)
        print(f"Copia do mapa antigo salva em '{BACKUP}'.")
    ox.save_graphml(G, ARQUIVO)
    print(f"Pronto! '{ARQUIVO}' atualizado. Agora rode o simulador normalmente.")


if __name__ == "__main__":
    main()
