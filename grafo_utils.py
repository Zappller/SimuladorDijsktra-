"""
grafo_utils.py - Módulo de Utilitários e Modelagem de Tráfego em Aracaju
Trabalho Prático de Teoria dos Grafos: Dijkstra, BPR e MBPR
"""

import math
import heapq
import re
import os
import json
import webbrowser
import networkx as nx
import matplotlib.pyplot as plt

# Coordenada padrão da UFS (Campus São Cristóvão - Entrada Principal / Reitoria)
UFS_COORDS = (-10.9252468, -37.1050639)
UFS_DEFAULT_NODE = "5556227911"
UFS_NAME = "Universidade Federal de Sergipe (UFS - São Cristóvão)"

# Pontos Notáveis de Aracaju (Pontos A pré-configurados para escolha rápida)
PONTOS_NOTAVEIS = {
    "1": {
        "nome": "Centro Histórico (Praça Fausto Cardoso / Palácio)",
        "coords": (-10.9081, -37.0515),
        "node": "954735330"
    },
    "2": {
        "nome": "Shopping Jardins (Bairro Jardins)",
        "coords": (-10.9413, -37.0681),
        "node": "1473460412"
    },
    "3": {
        "nome": "Terminal D.I.A. (Distrito Industrial de Aracaju)",
        "coords": (-10.9539, -37.0781),
        "node": "1125694869"
    },
    "4": {
        "nome": "Parque da Sementeira (Av. Beira Mar / 13 de Julho)",
        "coords": (-10.9467, -37.0608),
        "node": "5951232982"
    },
    "5": {
        "nome": "Orla de Atalaia (Passarela do Caranguejo / Arcos)",
        "coords": (-10.9695, -37.0473),
        "node": "958154915"
    },
    "6": {
        "nome": "Aeroporto Internacional de Aracaju (Santa Maria)",
        "coords": (-10.9693, -37.0698),
        "node": "1166098230"
    },
    "7": {
        "nome": "Mercado Municipal de Aracaju (Mercados Centrais)",
        "coords": (-10.9031, -37.0510),
        "node": "8954876002"
    },
    "8": {
        "nome": "Mirante do Bairro 13 de Julho (Calçadão)",
        "coords": (-10.9295, -37.0520),
        "node": "939897250"
    }
}


def _extrair_numero(val, default_val):
    """Extrai valor numérico de strings, inteiros, floats ou listas textuais."""
    if val is None:
        return default_val
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val).strip()
    matches = re.findall(r"[-+]?\d*\.\d+|\d+", val_str)
    if matches:
        try:
            return float(matches[0])
        except ValueError:
            return default_val
    return default_val


def _obter_velocidade(maxspeed_raw, highway_type):
    """Estima velocidade máxima da via em km/h com base no tipo OSM."""
    v = _extrair_numero(maxspeed_raw, None)
    if v is not None and 10 <= v <= 110:
        return v
    h = str(highway_type).lower()
    if "trunk" in h or "motorway" in h:
        return 70.0
    elif "primary" in h:
        return 60.0
    elif "secondary" in h:
        return 50.0
    elif "tertiary" in h:
        return 40.0
    else:  # residential, unclassified, living_street
        return 30.0


def _obter_faixas(lanes_raw, highway_type):
    """Estima o número de faixas de tráfego."""
    l = _extrair_numero(lanes_raw, None)
    if l is not None and 1 <= l <= 6:
        return l
    h = str(highway_type).lower()
    if "trunk" in h or "primary" in h:
        return 2.0
    elif "secondary" in h:
        return 2.0
    elif "tertiary" in h:
        return 1.5
    else:
        return 1.0


def _obter_capacidade(highway_type, faixas):
    """Calcula capacidade prática da via em veículos/hora."""
    h = str(highway_type).lower()
    if "trunk" in h or "motorway" in h:
        cap_faixa = 1800.0
    elif "primary" in h:
        cap_faixa = 1600.0
    elif "secondary" in h:
        cap_faixa = 1200.0
    elif "tertiary" in h:
        cap_faixa = 900.0
    else:
        cap_faixa = 500.0
    return faixas * cap_faixa


def carregar_grafo_aracaju(caminho="aracaju.graphml"):
    """
    Carrega o grafo de Aracaju a partir do arquivo GraphML
    e converte os atributos para formatos numéricos estritamente tipados.
    """
    if not os.path.exists(caminho):
        raise FileNotFoundError(f"Arquivo '{caminho}' não encontrado no diretório atual!")

    print(f"[*] Carregando malha viária de Aracaju ('{caminho}')...")
    G = nx.read_graphml(caminho)
    print(f"[+] Grafo carregado com sucesso: {G.number_of_nodes()} cruzamentos (nós) e {G.number_of_edges()} segmentos de rua (arestas).")

    # Identificar e normalizar dados dos nós (cruzamentos)
    traffic_signals_count = 0
    for n, d in G.nodes(data=True):
        d["y"] = float(d.get("y", 0.0))
        d["x"] = float(d.get("x", 0.0))
        is_signal = str(d.get("highway", "")).lower() == "traffic_signals"
        d["is_traffic_signal"] = is_signal
        if is_signal:
            traffic_signals_count += 1

    print(f"[+] Cruzamentos semaforizados identificados: {traffic_signals_count} semáforos.")

    # Normalizar atributos das arestas (segmentos viários)
    for u, v, k, d in G.edges(keys=True, data=True):
        length = _extrair_numero(d.get("length", 10.0), 10.0)
        d["length"] = max(length, 1.0)  # metros

        hwy = str(d.get("highway", "residential"))
        d["highway_clean"] = hwy

        # Nome da rua limpo
        name = d.get("name", "Via sem nome")
        if isinstance(name, str) and name.startswith("["):
            clean_name = re.sub(r"[\[\]']", "", name).split(",")[0].strip()
            d["name_clean"] = clean_name if clean_name else "Via sem nome"
        else:
            d["name_clean"] = str(name)

        v_kph = _obter_velocidade(d.get("maxspeed", None), hwy)
        d["speed_kph"] = v_kph
        v_mps = v_kph / 3.6
        d["speed_mps"] = v_mps

        # Tempo de fluxo livre t0 (segundos)
        d["t0"] = d["length"] / v_mps

        # Capacidade em veículos/hora
        faixas = _obter_faixas(d.get("lanes", None), hwy)
        d["lanes_clean"] = faixas
        d["capacity"] = _obter_capacidade(hwy, faixas)

        # Volume inicial
        d["volume"] = 0.0
        d["vc_ratio"] = 0.0

        # Semáforo no cruzamento destino
        d["dest_has_signal"] = G.nodes[v].get("is_traffic_signal", False)

    return G


def aplicar_trafego_realista(G, nivel_pico=1.3, seed=42):
    """
    Simula uma matriz de carregamento de tráfego realista nos horários de pico
    em Aracaju, gerando saturação severa nas principais artérias de escoamento para a UFS.
    """
    import random
    rng = random.Random(seed)

    for u, v, k, d in G.edges(keys=True, data=True):
        name = d["name_clean"].lower()
        hwy = d["highway_clean"].lower()
        cap = d["capacity"]

        # Nível basal por classificação viária
        if "primary" in hwy or "trunk" in hwy:
            base_vc = rng.uniform(0.70, 1.10)
        elif "secondary" in hwy:
            base_vc = rng.uniform(0.55, 0.90)
        elif "tertiary" in hwy:
            base_vc = rng.uniform(0.30, 0.65)
        else:
            base_vc = rng.uniform(0.10, 0.30)

        # Sobrecarga nos corredores de ligação crítica com a UFS
        termos_criticos = [
            "marcelo déda", "rondon", "tancredo", "hermes fontes",
            "adélia franco", "beira mar", "maynard", "saneamento", "rosa elze",
            "universit", "ivo do prado"
        ]
        if any(tc in name for tc in termos_criticos):
            base_vc *= rng.uniform(1.20, 1.45)

        vc_ratio = base_vc * nivel_pico
        d["volume"] = cap * vc_ratio
        d["vc_ratio"] = vc_ratio

    print(f"[+] Padrão de tráfego de Aracaju simulado (Fator de intensidade = {nivel_pico:.2f}).")


def calcular_custo_bpr(t0, volume, capacity, alpha=0.15, beta=4.0):
    """
    Função clássica de atraso BPR (Bureau of Public Roads - 1964):
    t = t0 * (1 + alpha * (V / C)^beta)
    """
    if capacity <= 0:
        return t0 * 10.0
    vc = volume / capacity
    return t0 * (1.0 + alpha * math.pow(vc, beta))


def calcular_custo_mbpr(t0, volume, capacity, dest_has_signal=False, alpha=0.15, beta=4.0):
    """
    Função MBPR (Modified Bureau of Public Roads):
    1. Regime Duplo (Dual-Regime / Piecewise) para V/C > 1.0 (Akçelik / NCHRP 387).
    2. Penalidade Semafórica e de Interseção (Webster / HCM).
    """
    if capacity <= 0:
        return t0 * 10.0

    vc = volume / capacity

    # 1. Componente de tempo de percurso na via
    if vc <= 1.0:
        t_link = t0 * (1.0 + alpha * math.pow(vc, beta))
    else:
        t_cap = t0 * (1.0 + alpha)
        atraso_fila = t0 * (alpha * beta * (vc - 1.0) + 1.6 * math.pow(vc - 1.0, 2))
        t_link = t_cap + atraso_fila

    # 2. Componente de atraso em semáforos
    d_semaforo = 0.0
    if dest_has_signal:
        t_vermelho = 25.0
        if vc <= 1.0:
            d_semaforo = t_vermelho * (1.0 + 0.4 * math.pow(vc, 2))
        else:
            d_semaforo = t_vermelho * (1.4 + 2.2 * (vc - 1.0))

    return t_link + d_semaforo


def atualizar_pesos_grafo(G, metodo="dijkstra"):
    """Atualiza o atributo 'weight' em todas as arestas de acordo com o método escolhido."""
    for u, v, k, d in G.edges(keys=True, data=True):
        t0 = d["t0"]
        vol = d.get("volume", 0.0)
        cap = d["capacity"]
        dest_signal = d["dest_has_signal"]

        if metodo == "dijkstra":
            d["weight"] = d["length"]
            d["custo_segundos"] = t0
        elif metodo == "bpr":
            custo_seg = calcular_custo_bpr(t0, vol, cap)
            d["weight"] = custo_seg
            d["custo_segundos"] = custo_seg
        elif metodo == "mbpr":
            custo_seg = calcular_custo_mbpr(t0, vol, cap, dest_has_signal=dest_signal)
            d["weight"] = custo_seg
            d["custo_segundos"] = custo_seg
        else:
            raise ValueError(f"Método desconhecido: {metodo}")


def dijkstra_algoritmo(G, origem, destino, weight_attr="weight"):
    """
    Execução explícita do Algoritmo de Dijkstra com fila de prioridade (heapq).
    Retorna: (caminho_de_nos, custo_total, metricas_execucao)
    """
    import time
    t_start = time.perf_counter()

    dist = {origem: 0.0}
    prev = {origem: None}
    pq = [(0.0, origem)]
    visitados = set()
    nos_expandidos = 0
    arestas_relaxadas = 0

    while pq:
        curr_cost, u = heapq.heappop(pq)
        if u in visitados:
            continue
        visitados.add(u)
        nos_expandidos += 1

        if u == destino:
            break

        for v in G.successors(u):
            if v in visitados:
                continue

            arestas = G.get_edge_data(u, v)
            min_k, min_d = min(arestas.items(), key=lambda item: item[1].get(weight_attr, float("inf")))
            peso_aresta = min_d.get(weight_attr, float("inf"))

            new_cost = curr_cost + peso_aresta
            arestas_relaxadas += 1

            if new_cost < dist.get(v, float("inf")):
                dist[v] = new_cost
                prev[v] = u
                heapq.heappush(pq, (new_cost, v))

    t_end = time.perf_counter()

    if destino not in dist:
        return None, float("inf"), {
            "tempo_ms": (t_end - t_start) * 1000.0,
            "nos_expandidos": nos_expandidos,
            "arestas_relaxadas": arestas_relaxadas
        }

    caminho = []
    curr = destino
    while curr is not None:
        caminho.append(curr)
        curr = prev[curr]
    caminho.reverse()

    stats = {
        "tempo_ms": (t_end - t_start) * 1000.0,
        "nos_expandidos": nos_expandidos,
        "arestas_relaxadas": arestas_relaxadas
    }
    return caminho, dist[destino], stats


def extrair_metricas_rota(G, caminho):
    """Calcula estatísticas de engenharia de tráfego e vias percorridas ao longo da rota."""
    dist_total_m = 0.0
    tempo_t0_s = 0.0
    tempo_bpr_s = 0.0
    tempo_mbpr_s = 0.0
    num_semaforos = 0
    nomes_vias = []
    detalhes_arestas = []
    coordenadas = []

    for n in caminho:
        coordenadas.append((G.nodes[n]["y"], G.nodes[n]["x"]))

    for i in range(len(caminho) - 1):
        u, v = caminho[i], caminho[i + 1]
        arestas = G.get_edge_data(u, v)
        k_best, d_best = min(arestas.items(), key=lambda item: item[1].get("weight", float("inf")))

        length = d_best["length"]
        t0 = d_best["t0"]
        vol = d_best.get("volume", 0.0)
        cap = d_best["capacity"]
        has_signal = d_best["dest_has_signal"]

        tbpr = calcular_custo_bpr(t0, vol, cap)
        tmbpr = calcular_custo_mbpr(t0, vol, cap, has_signal)

        dist_total_m += length
        tempo_t0_s += t0
        tempo_bpr_s += tbpr
        tempo_mbpr_s += tmbpr
        if has_signal:
            num_semaforos += 1

        nome = d_best["name_clean"]
        if not nomes_vias or nomes_vias[-1] != nome:
            nomes_vias.append(nome)

        detalhes_arestas.append({
            "u": u,
            "v": v,
            "nome": nome,
            "length_m": length,
            "speed_kph": d_best["speed_kph"],
            "t0_s": t0,
            "volume_vh": vol,
            "capacity_vh": cap,
            "vc_ratio": vol / cap if cap > 0 else 0,
            "tbpr_s": tbpr,
            "tmbpr_s": tmbpr,
            "has_signal": has_signal
        })

    return {
        "distancia_km": dist_total_m / 1000.0,
        "tempo_fluxo_livre_min": tempo_t0_s / 60.0,
        "tempo_bpr_min": tempo_bpr_s / 60.0,
        "tempo_mbpr_min": tempo_mbpr_s / 60.0,
        "num_semaforos": num_semaforos,
        "num_nos": len(caminho),
        "nomes_vias": nomes_vias,
        "detalhes": detalhes_arestas,
        "coordenadas": coordenadas
    }


def menu_selecao_origem(G):
    """Exibe menu interativo para seleção do Ponto A (Origem) em Aracaju."""
    print("=" * 70)
    print(" SELEÇÃO DO PONTO DE PARTIDA (PONTO A) EM ARACAJU")
    print(f" Destino fixado: {UFS_NAME}")
    print("=" * 70)
    for chave, dados in PONTOS_NOTAVEIS.items():
        print(f" [{chave}] {dados['nome']}")
    print(" [9] Inserir coordenadas personalizadas (Latitude, Longitude)")
    print("=" * 70)

    while True:
        opcao = input(" Escolha o Ponto de Partida [1-9] (Enter para padrão '1' - Centro): ").strip()
        if not opcao:
            opcao = "1"

        if opcao in PONTOS_NOTAVEIS:
            ponto = PONTOS_NOTAVEIS[opcao]
            print(f"\n[+] Ponto A selecionado: {ponto['nome']} (Nó: {ponto['node']})")
            return ponto["node"], ponto["nome"], ponto["coords"]
        elif opcao == "9":
            try:
                lat_str = input(" Digite a Latitude (ex: -10.920): ").strip()
                lon_str = input(" Digite a Longitude (ex: -37.070): ").strip()
                lat, lon = float(lat_str), float(lon_str)
                no_prox = encontrar_no_mais_proximo(G, lat, lon)
                nome_personalizado = f"Ponto Personalizado ({lat:.4f}, {lon:.4f})"
                print(f"[+] Ponto A localizado próximo ao Nó {no_prox}")
                return no_prox, nome_personalizado, (lat, lon)
            except Exception as e:
                print(f"[!] Erro ao interpretar coordenadas: {e}. Tente novamente.")
        else:
            print("[!] Opção inválida. Digite um número de 1 a 9.")


def encontrar_no_mais_proximo(G, lat, lon):
    """Encontra o nó da rede viária mais próximo de uma coordenada geográfica."""
    melhor_no = None
    menor_dist = float("inf")
    for n, d in G.nodes(data=True):
        y, x = d["y"], d["x"]
        dist = math.hypot(y - lat, x - lon)
        if dist < menor_dist:
            menor_dist = dist
            melhor_no = n
    return melhor_no


# ==============================================================================
# EXTRATORES DE DADOS AUXILIARES PARA MAPAS (CONGESTIONAMENTO E SEMÁFOROS)
# ==============================================================================

def _extrair_segmentos_congestionados(G, max_seg=350):
    """Extrai segmentos viários com cor correspondente ao nível de saturação (V/C)."""
    segmentos = []
    for u, v, k, d in G.edges(keys=True, data=True):
        vc = d.get("vc_ratio", 0.0)
        hwy = d.get("highway_clean", "")
        # Filtrar apenas vias arteriais ou trechos com saturação relevante
        if "primary" not in hwy and "secondary" not in hwy and "trunk" not in hwy and vc < 0.90:
            continue

        u_lat, u_lon = G.nodes[u]["y"], G.nodes[u]["x"]
        v_lat, v_lon = G.nodes[v]["y"], G.nodes[v]["x"]

        if vc < 0.70:
            cor = "#22c55e"  # Verde: fluxo livre
            peso = 2.5
        elif vc <= 1.0:
            cor = "#eab308"  # Amarelo: tráfego moderado
            peso = 3.5
        elif vc <= 1.3:
            cor = "#f97316"  # Laranja: tráfego intenso
            peso = 4.5
        else:
            cor = "#ef4444"  # Vermelho: congestionamento severo
            peso = 5.5

        segmentos.append({
            "coords": [[u_lat, u_lon], [v_lat, v_lon]],
            "cor": cor,
            "peso": peso,
            "vc": round(vc, 2),
            "nome": d.get("name_clean", "Via de Aracaju")
        })

        if len(segmentos) >= max_seg:
            break
    return segmentos


def _extrair_semaforos_rotas(G, caminhos):
    """Extrai nós com semáforos reais que intersectam os caminhos calculados."""
    semaforos = []
    nos_vistos = set()
    for caminho in caminhos:
        for n in caminho:
            if n not in nos_vistos and G.nodes[n].get("is_traffic_signal", False):
                nos_vistos.add(n)
                semaforos.append({
                    "lat": G.nodes[n]["y"],
                    "lon": G.nodes[n]["x"],
                    "node": str(n)
                })
    return semaforos


# ==============================================================================
# GERADORES DE SIMULAÇÃO VISUAL INTERATIVA (HTML AUTÔNOMO 100% FUNCIONAL)
# ==============================================================================

def gerar_simulacao_dijkstra_html(G, caminho, metricas, nome_origem, arquivo_saida="simulacao_dijkstra.html"):
    """
    Gera página HTML independente, com Leaflet 1.9 e OpenStreetMap garantidos,
    sem erros de injeção, sem dependência de plugins frágeis e com animação suave de veículo.
    """
    coords = metricas["coordenadas"]
    centro_lat = sum(c[0] for c in coords) / len(coords)
    centro_lon = sum(c[1] for c in coords) / len(coords)
    vias = [d["nome"] for d in metricas["detalhes"]]

    coords_json = json.dumps(coords)
    vias_json = json.dumps(vias)

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simulação: Rota Dijkstra (Aracaju ➔ UFS)</title>
    <!-- Leaflet CSS & JS Oficiais (CDN cdnjs) -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css" />
    <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"></script>
    <style>
        * {{ box-sizing: border-box; }}
        html, body {{
            width: 100%;
            height: 100%;
            margin: 0;
            padding: 0;
            overflow: hidden;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #e2e8f0;
        }}
        #map {{
            position: absolute;
            top: 0;
            bottom: 0;
            left: 0;
            right: 0;
            width: 100%;
            height: 100%;
            z-index: 1;
        }}
        /* Animação SVG nativa para a linha de rota */
        .rota-animada {{
            stroke-dasharray: 12, 12;
            animation: dashRota 1.2s linear infinite;
        }}
        @keyframes dashRota {{
            to {{ stroke-dashoffset: -24; }}
        }}
        /* HUD Flutuante */
        .hud-painel {{
            position: fixed;
            bottom: 25px;
            right: 25px;
            z-index: 1000;
            background: rgba(15, 23, 42, 0.96);
            color: #f8fafc;
            padding: 20px 24px;
            border-radius: 14px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.5);
            min-width: 330px;
            max-width: 420px;
            border: 1px solid rgba(255,255,255,0.12);
            backdrop-filter: blur(10px);
        }}
        .hud-titulo {{
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 12px;
            color: #38bdf8;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .hud-metricas {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-bottom: 14px;
        }}
        .hud-caixa {{
            background: rgba(255,255,255,0.06);
            padding: 8px 12px;
            border-radius: 8px;
            border: 1px solid rgba(255,255,255,0.05);
        }}
        .hud-caixa .label {{
            font-size: 11px;
            color: #94a3b8;
            text-transform: uppercase;
            font-weight: 600;
        }}
        .hud-caixa .valor {{
            font-size: 16px;
            font-weight: 700;
            color: #4ade80;
            margin-top: 2px;
        }}
        .hud-controles {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 12px;
        }}
        .hud-btn {{
            background: #2563eb;
            color: #fff;
            border: none;
            padding: 10px 18px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            font-size: 14px;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .hud-btn:hover {{
            background: #1d4ed8;
            transform: translateY(-1px);
        }}
        .hud-btn-reset {{
            background: #475569;
        }}
        .hud-btn-reset:hover {{
            background: #334155;
        }}
        .hud-select {{
            background: #1e293b;
            color: #f8fafc;
            border: 1px solid #475569;
            padding: 9px 12px;
            border-radius: 8px;
            font-size: 13px;
            outline: none;
        }}
        .hud-progresso {{
            width: 100%;
            height: 6px;
            background: #334155;
            border-radius: 3px;
            margin-top: 14px;
            overflow: hidden;
        }}
        .hud-barra {{
            width: 0%;
            height: 100%;
            background: #38bdf8;
            transition: width 0.15s ease-out;
        }}
        .car-marker {{
            font-size: 30px;
            line-height: 1;
            filter: drop-shadow(0 4px 6px rgba(0,0,0,0.6));
            transition: transform 0.1s linear;
        }}
    </style>
</head>
<body>
    <div id="map"></div>

    <div class="hud-painel">
        <div class="hud-titulo">
            <span>🚗 SIMULAÇÃO: DIJKSTRA</span>
            <span style="font-size: 13px; color: #94a3b8;">{metricas['distancia_km']:.2f} km</span>
        </div>
        
        <div class="hud-metricas">
            <div class="hud-caixa">
                <div class="label">Distância Percorrida</div>
                <div class="valor" id="dist-atual">0.00 km</div>
            </div>
            <div class="hud-caixa">
                <div class="label">Tempo Estimado</div>
                <div class="valor" id="tempo-atual">{metricas['tempo_fluxo_livre_min']:.1f} min</div>
            </div>
            <div class="hud-caixa" style="grid-column: span 2;">
                <div class="label">Via Atual</div>
                <div class="valor" id="via-atual" style="font-size: 13px; color: #f8fafc; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                    Clique em Iniciar para começar...
                </div>
            </div>
        </div>

        <div class="hud-controles">
            <button class="hud-btn" id="btn-play">▶️ Iniciar</button>
            <button class="hud-btn hud-btn-reset" id="btn-reset">🔄 Reset</button>
            <select class="hud-select" id="sel-vel">
                <option value="1">1x</option>
                <option value="3" selected>3x</option>
                <option value="8">8x</option>
                <option value="15">15x</option>
            </select>
        </div>

        <div class="hud-progresso">
            <div class="hud-barra" id="hud-barra"></div>
        </div>
    </div>

    <script>
        var coords = {coords_json};
        var vias = {vias_json};
        var totalDistKm = {metricas['distancia_km']};
        var totalTempoMin = {metricas['tempo_fluxo_livre_min']};

        // 1. Inicializar Mapa Leaflet
        var map = L.map('map', {{
            center: [{centro_lat}, {centro_lon}],
            zoom: 13,
            zoomControl: true
        }});

        // 2. Camadas de Mapa Base (Sem erro 403 do OpenStreetMap)
        var mapaRuas = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
            maxZoom: 19,
            attribution: 'Tiles &copy; Esri &mdash; Street Map'
        }}).addTo(map);

        var mapaSatelite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
            maxZoom: 19,
            attribution: 'Tiles &copy; Esri &mdash; Satellite'
        }});

        var mapaCarto = L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png', {{
            maxZoom: 19,
            subdomains: 'abcd',
            attribution: '&copy; CARTO'
        }});

        L.control.layers({{
            "🗺️ Mapa de Ruas (Esri)": mapaRuas,
            "🛰️ Imagem de Satélite": mapaSatelite,
            "🏙️ Mapa Carto": mapaCarto
        }}, null, {{ position: 'topright' }}).addTo(map);

        // 3. Traçado da Rota com Classe CSS Animada
        var polyline = L.polyline(coords, {{
            color: '#2563eb',
            weight: 6,
            opacity: 0.9,
            className: 'rota-animada'
        }}).addTo(map);

        map.fitBounds(polyline.getBounds(), {{ padding: [60, 60] }});

        // 4. Marcador Origem (Ponto A)
        var iconOrigem = L.divIcon({{
            className: 'custom-pin',
            html: '<div style=\"background:#22c55e; color:#fff; border-radius:50%; width:34px; height:34px; display:flex; align-items:center; justify-content:center; font-weight:bold; font-size:16px; box-shadow:0 3px 8px rgba(0,0,0,0.5); border:2px solid #fff;\">A</div>',
            iconSize: [34, 34],
            iconAnchor: [17, 17]
        }});
        L.marker(coords[0], {{ icon: iconOrigem }}).addTo(map).bindPopup('<b>Ponto A (Origem):</b><br>{nome_origem}');

        // 5. Marcador Destino (UFS)
        var iconDestino = L.divIcon({{
            className: 'custom-pin',
            html: '<div style=\"background:#ef4444; color:#fff; border-radius:50%; width:34px; height:34px; display:flex; align-items:center; justify-content:center; font-weight:bold; font-size:18px; box-shadow:0 3px 8px rgba(0,0,0,0.5); border:2px solid #fff;\">🎓</div>',
            iconSize: [34, 34],
            iconAnchor: [17, 17]
        }});
        L.marker(coords[coords.length - 1], {{ icon: iconDestino }}).addTo(map).bindPopup('<b>Destino:</b><br>{UFS_NAME}');

        // 6. Veículo Animado (Emoji de Carro com Rotação)
        var carIcon = L.divIcon({{
            className: 'car-marker',
            html: '<div id=\"car-emoji\">🚗</div>',
            iconSize: [32, 32],
            iconAnchor: [16, 16]
        }});
        var carMarker = L.marker(coords[0], {{ icon: carIcon, zIndexOffset: 1000 }}).addTo(map);

        // 7. Lógica de Simulação e Controle de Reprodução
        var currentIndex = 0;
        var isRunning = false;
        var timerId = null;

        var btnPlay = document.getElementById('btn-play');
        var btnReset = document.getElementById('btn-reset');
        var selVel = document.getElementById('sel-vel');
        var distAtual = document.getElementById('dist-atual');
        var viaAtual = document.getElementById('via-atual');
        var hudBarra = document.getElementById('hud-barra');

        function step() {{
            if (!isRunning) return;

            if (currentIndex < coords.length - 1) {{
                currentIndex++;
                var pAtual = coords[currentIndex];
                carMarker.setLatLng(pAtual);

                var pct = (currentIndex / (coords.length - 1)) * 100;
                hudBarra.style.width = pct + '%';

                var dKm = (currentIndex / (coords.length - 1)) * totalDistKm;
                distAtual.innerText = dKm.toFixed(2) + ' km';

                if (currentIndex - 1 < vias.length) {{
                    viaAtual.innerText = vias[currentIndex - 1];
                }}

                var velMult = parseFloat(selVel.value);
                var delayMs = Math.max(25, 260 / velMult);
                timerId = setTimeout(step, delayMs);
            }} else {{
                isRunning = false;
                btnPlay.innerText = '▶️ Reiniciar';
                viaAtual.innerText = 'Chegada: UFS (Campus São Cristóvão) 🎓';
                hudBarra.style.width = '100%';
            }}
        }}

        btnPlay.onclick = function() {{
            if (isRunning) {{
                isRunning = false;
                clearTimeout(timerId);
                btnPlay.innerText = '▶️ Continuar';
            }} else {{
                if (currentIndex >= coords.length - 1) {{
                    currentIndex = 0;
                }}
                isRunning = true;
                btnPlay.innerText = '⏸️ Pausar';
                step();
            }}
        }};

        btnReset.onclick = function() {{
            isRunning = false;
            clearTimeout(timerId);
            currentIndex = 0;
            carMarker.setLatLng(coords[0]);
            hudBarra.style.width = '0%';
            distAtual.innerText = '0.00 km';
            viaAtual.innerText = 'Iniciando trajeto...';
            btnPlay.innerText = '▶️ Iniciar';
        }};
    </script>
</body>
</html>
"""
    with open(arquivo_saida, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[+] Mapa e Simulação Dijkstra gerados com sucesso: {os.path.abspath(arquivo_saida)}")
    return arquivo_saida


def gerar_simulacao_bpr_html(G, caminho_dijkstra, metricas_dijkstra,
                            caminho_bpr, metricas_bpr,
                            nome_origem, arquivo_saida="simulacao_bpr.html"):
    """
    Gera página HTML com corrida entre dois carros:
    🚗 Carro 1 (Dijkstra - Preso no trânsito) vs 🚙 Carro 2 (BPR - Desvia do congestionamento).
    """
    coords_dijk = metricas_dijkstra["coordenadas"]
    coords_bpr = metricas_bpr["coordenadas"]
    segmentos_vc = _extrair_segmentos_congestionados(G)

    coords_dijk_json = json.dumps(coords_dijk)
    coords_bpr_json = json.dumps(coords_bpr)
    seg_json = json.dumps(segmentos_vc)

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simulação BPR vs Dijkstra (Aracaju ➔ UFS)</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css" />
    <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"></script>
    <style>
        * {{ box-sizing: border-box; }}
        html, body {{
            width: 100%;
            height: 100%;
            margin: 0;
            padding: 0;
            overflow: hidden;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #e2e8f0;
        }}
        #map {{
            position: absolute;
            top: 0;
            bottom: 0;
            left: 0;
            right: 0;
            width: 100%;
            height: 100%;
            z-index: 1;
        }}
        .rota-bpr-animada {{
            stroke-dasharray: 12, 12;
            animation: dashBpr 1s linear infinite;
        }}
        @keyframes dashBpr {{
            to {{ stroke-dashoffset: -24; }}
        }}
        .hud-painel {{
            position: fixed;
            bottom: 25px;
            right: 25px;
            z-index: 1000;
            background: rgba(15, 23, 42, 0.96);
            color: #f8fafc;
            padding: 20px 24px;
            border-radius: 14px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.5);
            min-width: 370px;
            max-width: 440px;
            border: 1px solid rgba(255,255,255,0.12);
            backdrop-filter: blur(10px);
        }}
        .hud-titulo {{
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 12px;
            color: #38bdf8;
        }}
        .card-rota {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 14px;
            border-radius: 8px;
            margin-bottom: 8px;
            font-size: 13px;
        }}
        .card-dijkstra {{
            background: rgba(239, 68, 68, 0.15);
            border-left: 4px solid #ef4444;
        }}
        .card-bpr {{
            background: rgba(56, 189, 248, 0.18);
            border-left: 4px solid #38bdf8;
        }}
        .hud-controles {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 14px;
        }}
        .hud-btn {{
            background: #22c55e;
            color: #fff;
            border: none;
            padding: 10px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            font-size: 14px;
            transition: all 0.2s;
        }}
        .hud-btn:hover {{ background: #16a34a; }}
        .hud-btn-reset {{ background: #475569; }}
        .hud-btn-reset:hover {{ background: #334155; }}
        .hud-select {{
            background: #1e293b;
            color: #f8fafc;
            border: 1px solid #475569;
            padding: 9px 12px;
            border-radius: 8px;
            font-size: 13px;
        }}
        .legenda-trafego {{
            font-size: 11px;
            color: #cbd5e1;
            margin-top: 8px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .dot {{ width: 9px; height: 9px; border-radius: 50%; display: inline-block; }}
    </style>
</head>
<body>
    <div id="map"></div>

    <div class="hud-painel">
        <div class="hud-titulo">🏎️ SIMULAÇÃO DE TRÁFEGO: BPR vs DIJKSTRA</div>
        
        <div class="card-rota card-dijkstra">
            <div>
                <b>🚗 Dijkstra Clássico</b><br>
                <small>{metricas_dijkstra['distancia_km']:.2f} km (Via mais congestionada)</small>
            </div>
            <div style="text-align: right; color: #ef4444; font-weight: 700; font-size: 15px;">
                {metricas_dijkstra['tempo_bpr_min']:.1f} min
            </div>
        </div>

        <div class="card-rota card-bpr">
            <div>
                <b>🚙 Rota BPR (Adaptativa)</b> 🏆<br>
                <small>{metricas_bpr['distancia_km']:.2f} km (Desvia de gargalos)</small>
            </div>
            <div style="text-align: right; color: #38bdf8; font-weight: 700; font-size: 15px;">
                {metricas_bpr['tempo_bpr_min']:.1f} min
            </div>
        </div>

        <div class="legenda-trafego">
            <span>Trânsito:</span>
            <span><span class="dot" style="background:#22c55e;"></span> Livre</span>
            <span><span class="dot" style="background:#eab308;"></span> Médio</span>
            <span><span class="dot" style="background:#ef4444;"></span> Congestionado</span>
        </div>

        <div class="hud-controles">
            <button class="hud-btn" id="btn-play">▶️ Iniciar Corrida</button>
            <button class="hud-btn hud-btn-reset" id="btn-reset">🔄 Reset</button>
            <select class="hud-select" id="sel-vel">
                <option value="1">1x</option>
                <option value="3" selected>3x</option>
                <option value="8">8x</option>
            </select>
        </div>
    </div>

    <script>
        var coordsDijk = {coords_dijk_json};
        var coordsBpr = {coords_bpr_json};
        var segmentos = {seg_json};

        var map = L.map('map', {{ zoomControl: true }});

        // Camadas de Mapa Base (Sem erro 403 do OpenStreetMap)
        var mapaRuas = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
            maxZoom: 19,
            attribution: 'Tiles &copy; Esri &mdash; Street Map'
        }}).addTo(map);

        var mapaSatelite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
            maxZoom: 19,
            attribution: 'Tiles &copy; Esri &mdash; Satellite'
        }});

        var mapaCarto = L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png', {{
            maxZoom: 19,
            subdomains: 'abcd',
            attribution: '&copy; CARTO'
        }});

        L.control.layers({{
            "🗺️ Mapa de Ruas (Esri)": mapaRuas,
            "🛰️ Imagem de Satélite": mapaSatelite,
            "🏙️ Mapa Carto": mapaCarto
        }}, null, {{ position: 'topright' }}).addTo(map);

        // Adicionar Camada de Tráfego Congestionado
        segmentos.forEach(function(s) {{
            L.polyline(s.coords, {{
                color: s.cor,
                weight: s.peso,
                opacity: 0.65
            }}).addTo(map).bindTooltip(s.nome + ' (V/C: ' + s.vc + ')');
        }});

        // Rota 1: Dijkstra (Vermelho)
        var polyDijk = L.polyline(coordsDijk, {{
            color: '#ef4444',
            weight: 5,
            opacity: 0.8,
            dashArray: '8, 8'
        }}).addTo(map);

        // Rota 2: BPR (Azul Celeste com animação)
        var polyBpr = L.polyline(coordsBpr, {{
            color: '#38bdf8',
            weight: 6,
            opacity: 0.95,
            className: 'rota-bpr-animada'
        }}).addTo(map);

        map.fitBounds(polyBpr.getBounds(), {{ padding: [60, 60] }});

        // Marcadores Origem e Destino
        var iconOrigem = L.divIcon({{
            html: '<div style=\"background:#22c55e; color:#fff; border-radius:50%; width:32px; height:32px; display:flex; align-items:center; justify-content:center; font-weight:bold; border:2px solid #fff; box-shadow:0 3px 6px rgba(0,0,0,0.4);\">A</div>',
            iconSize: [32, 32], iconAnchor: [16, 16]
        }});
        L.marker(coordsDijk[0], {{ icon: iconOrigem }}).addTo(map).bindPopup('<b>Origem:</b> {nome_origem}');

        var iconDestino = L.divIcon({{
            html: '<div style=\"background:#ef4444; color:#fff; border-radius:50%; width:32px; height:32px; display:flex; align-items:center; justify-content:center; font-weight:bold; border:2px solid #fff; box-shadow:0 3px 6px rgba(0,0,0,0.4);\">🎓</div>',
            iconSize: [32, 32], iconAnchor: [16, 16]
        }});
        L.marker(coordsDijk[coordsDijk.length - 1], {{ icon: iconDestino }}).addTo(map).bindPopup('<b>Destino:</b> {UFS_NAME}');

        // Carros
        var carDijkIcon = L.divIcon({{ html: '<div style=\"font-size:28px;\">🚗</div>', iconSize: [28,28], iconAnchor: [14,14] }});
        var carBprIcon = L.divIcon({{ html: '<div style=\"font-size:28px;\">🚙</div>', iconSize: [28,28], iconAnchor: [14,14] }});

        var carDijk = L.marker(coordsDijk[0], {{ icon: carDijkIcon, zIndexOffset: 900 }}).addTo(map);
        var carBpr = L.marker(coordsBpr[0], {{ icon: carBprIcon, zIndexOffset: 1000 }}).addTo(map);

        var idxDijk = 0, idxBpr = 0;
        var isRunning = false;
        var timerId = null;

        var btnPlay = document.getElementById('btn-play');
        var btnReset = document.getElementById('btn-reset');
        var selVel = document.getElementById('sel-vel');

        function stepRace() {{
            if (!isRunning) return;

            var finDijk = (idxDijk >= coordsDijk.length - 1);
            var finBpr = (idxBpr >= coordsBpr.length - 1);

            if (!finDijk) {{ idxDijk++; carDijk.setLatLng(coordsDijk[idxDijk]); }}
            if (!finBpr) {{ idxBpr++; carBpr.setLatLng(coordsBpr[idxBpr]); }}

            if (!finDijk || !finBpr) {{
                var mult = parseFloat(selVel.value);
                timerId = setTimeout(stepRace, Math.max(25, 240 / mult));
            }} else {{
                isRunning = false;
                btnPlay.innerText = '▶️ Reiniciar';
            }}
        }}

        btnPlay.onclick = function() {{
            if (isRunning) {{
                isRunning = false;
                clearTimeout(timerId);
                btnPlay.innerText = '▶️ Continuar';
            }} else {{
                if (idxDijk >= coordsDijk.length - 1 && idxBpr >= coordsBpr.length - 1) {{
                    idxDijk = 0; idxBpr = 0;
                }}
                isRunning = true;
                btnPlay.innerText = '⏸️ Pausar';
                stepRace();
            }}
        }};

        btnReset.onclick = function() {{
            isRunning = false;
            clearTimeout(timerId);
            idxDijk = 0; idxBpr = 0;
            carDijk.setLatLng(coordsDijk[0]);
            carBpr.setLatLng(coordsBpr[0]);
            btnPlay.innerText = '▶️ Iniciar Corrida';
        }};
    </script>
</body>
</html>
"""
    with open(arquivo_saida, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[+] Mapa e Simulação BPR gerados com sucesso: {os.path.abspath(arquivo_saida)}")
    return arquivo_saida


def gerar_simulacao_mbpr_html(G, caminho_dijkstra, metricas_dijkstra,
                             caminho_bpr, metricas_bpr,
                             caminho_mbpr, metricas_mbpr,
                             nome_origem, arquivo_saida="simulacao_mbpr.html"):
    """
    Gera página HTML completa com o Grande Prêmio das 3 Rotas:
    🚗 Carro 1 (Dijkstra) vs 🚙 Carro 2 (BPR) vs 🏎️ Carro 3 (MBPR).
    Inclui semáforos interativos mapeados na malha de Aracaju.
    """
    coords_dijk = metricas_dijkstra["coordenadas"]
    coords_bpr = metricas_bpr["coordenadas"]
    coords_mbpr = metricas_mbpr["coordenadas"]

    segmentos_vc = _extrair_segmentos_congestionados(G)
    semaforos = _extrair_semaforos_rotas(G, [caminho_dijkstra, caminho_bpr, caminho_mbpr])

    coords_dijk_json = json.dumps(coords_dijk)
    coords_bpr_json = json.dumps(coords_bpr)
    coords_mbpr_json = json.dumps(coords_mbpr)
    seg_json = json.dumps(segmentos_vc)
    sem_json = json.dumps(semaforos)

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Grande Prêmio das Rotas: Dijkstra vs BPR vs MBPR (Aracaju ➔ UFS)</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css" />
    <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"></script>
    <style>
        * {{ box-sizing: border-box; }}
        html, body {{
            width: 100%;
            height: 100%;
            margin: 0;
            padding: 0;
            overflow: hidden;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #e2e8f0;
        }}
        #map {{
            position: absolute;
            top: 0;
            bottom: 0;
            left: 0;
            right: 0;
            width: 100%;
            height: 100%;
            z-index: 1;
        }}
        .rota-mbpr-animada {{
            stroke-dasharray: 14, 14;
            animation: dashMbpr 0.8s linear infinite;
        }}
        @keyframes dashMbpr {{
            to {{ stroke-dashoffset: -28; }}
        }}
        .hud-painel {{
            position: fixed;
            bottom: 25px;
            right: 25px;
            z-index: 1000;
            background: rgba(15, 23, 42, 0.96);
            color: #f8fafc;
            padding: 20px 24px;
            border-radius: 14px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.6);
            min-width: 400px;
            max-width: 460px;
            border: 1px solid rgba(255,255,255,0.12);
            backdrop-filter: blur(10px);
        }}
        .hud-titulo {{
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 12px;
            color: #38bdf8;
        }}
        .card-rota {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 12px;
            border-radius: 8px;
            margin-bottom: 8px;
            font-size: 13px;
        }}
        .card-dijkstra {{ background: rgba(239, 68, 68, 0.15); border-left: 4px solid #ef4444; }}
        .card-bpr {{ background: rgba(245, 158, 11, 0.15); border-left: 4px solid #f59e0b; }}
        .card-mbpr {{ background: rgba(34, 197, 94, 0.2); border-left: 4px solid #22c55e; }}
        .hud-controles {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 14px;
        }}
        .hud-btn {{
            background: #22c55e;
            color: #fff;
            border: none;
            padding: 10px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            font-size: 14px;
        }}
        .hud-btn:hover {{ background: #16a34a; }}
        .hud-btn-reset {{ background: #475569; }}
        .hud-btn-reset:hover {{ background: #334155; }}
        .hud-select {{
            background: #1e293b;
            color: #f8fafc;
            border: 1px solid #475569;
            padding: 9px 12px;
            border-radius: 8px;
            font-size: 13px;
        }}
        .explicacao-mbpr {{
            font-size: 12px;
            color: #38bdf8;
            margin-top: 8px;
            line-height: 1.4;
        }}
    </style>
</head>
<body>
    <div id="map"></div>

    <div class="hud-painel">
        <div class="hud-titulo">🏁 GRANDE PRÊMIO DE ROTAS: ARACAJU ➔ UFS</div>

        <div class="card-rota card-dijkstra">
            <div>
                <b>🚗 Dijkstra Clássico</b><br>
                <small>{metricas_dijkstra['distancia_km']:.2f} km | 🛑 {metricas_dijkstra['num_semaforos']} semáforos</small>
            </div>
            <div style="text-align: right; color: #ef4444; font-weight: 700;">
                {metricas_dijkstra['tempo_mbpr_min']:.1f} min
            </div>
        </div>

        <div class="card-rota card-bpr">
            <div>
                <b>🚙 BPR Tradicional</b><br>
                <small>{metricas_bpr['distancia_km']:.2f} km | 🛑 {metricas_bpr['num_semaforos']} semáforos</small>
            </div>
            <div style="text-align: right; color: #f59e0b; font-weight: 700;">
                {metricas_bpr['tempo_mbpr_min']:.1f} min
            </div>
        </div>

        <div class="card-rota card-mbpr">
            <div>
                <b>🏎️ MBPR (Modificado)</b> 🏆<br>
                <small>{metricas_mbpr['distancia_km']:.2f} km | 🛑 {metricas_mbpr['num_semaforos']} semáforos</small>
            </div>
            <div style="text-align: right; color: #22c55e; font-weight: 700; font-size: 15px;">
                {metricas_mbpr['tempo_mbpr_min']:.1f} min
            </div>
        </div>

        <div class="explicacao-mbpr">
            💡 <b>Por que o MBPR vence?</b> O MBPR desviou de {metricas_dijkstra['num_semaforos'] - metricas_mbpr['num_semaforos']} semáforos e das vias com filas em supersaturação, economizando {metricas_dijkstra['tempo_mbpr_min'] - metricas_mbpr['tempo_mbpr_min']:.1f} minutos!
        </div>

        <div class="hud-controles">
            <button class="hud-btn" id="btn-play">▶️ Iniciar Simulação dos 3</button>
            <button class="hud-btn hud-btn-reset" id="btn-reset">🔄 Reset</button>
            <select class="hud-select" id="sel-vel">
                <option value="1">1x</option>
                <option value="3" selected>3x</option>
                <option value="8">8x</option>
                <option value="15">15x</option>
            </select>
        </div>
    </div>

    <script>
        var coordsDijk = {coords_dijk_json};
        var coordsBpr = {coords_bpr_json};
        var coordsMbpr = {coords_mbpr_json};
        var segmentos = {seg_json};
        var semaforos = {sem_json};

        var map = L.map('map', {{ zoomControl: true }});

        // Camadas de Mapa Base (Sem erro 403 do OpenStreetMap)
        var mapaRuas = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
            maxZoom: 19,
            attribution: 'Tiles &copy; Esri &mdash; Street Map'
        }}).addTo(map);

        var mapaSatelite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
            maxZoom: 19,
            attribution: 'Tiles &copy; Esri &mdash; Satellite'
        }});

        var mapaCarto = L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png', {{
            maxZoom: 19,
            subdomains: 'abcd',
            attribution: '&copy; CARTO'
        }});

        L.control.layers({{
            "🗺️ Mapa de Ruas (Esri)": mapaRuas,
            "🛰️ Imagem de Satélite": mapaSatelite,
            "🏙️ Mapa Carto": mapaCarto
        }}, null, {{ position: 'topright' }}).addTo(map);

        // Camada de tráfego
        segmentos.forEach(function(s) {{
            L.polyline(s.coords, {{ color: s.cor, weight: s.peso, opacity: 0.6 }}).addTo(map);
        }});

        // Camada de Semáforos Reais
        semaforos.forEach(function(sem) {{
            L.circleMarker([sem.lat, sem.lon], {{
                radius: 6,
                color: '#c0392b',
                fillColor: '#e74c3c',
                fillOpacity: 0.9,
                weight: 2
            }}).addTo(map).bindTooltip('🚦 Semáforo (Cruzamento ' + sem.node + ')');
        }});

        // Rota 1: Dijkstra (Vermelho)
        L.polyline(coordsDijk, {{ color: '#ef4444', weight: 4, opacity: 0.7, dashArray: '6, 6' }}).addTo(map);

        // Rota 2: BPR (Laranja)
        L.polyline(coordsBpr, {{ color: '#f59e0b', weight: 5, opacity: 0.8, dashArray: '8, 8' }}).addTo(map);

        // Rota 3: MBPR (Verde Esmeralda Animado)
        var polyMbpr = L.polyline(coordsMbpr, {{
            color: '#22c55e',
            weight: 7,
            opacity: 0.95,
            className: 'rota-mbpr-animada'
        }}).addTo(map);

        map.fitBounds(polyMbpr.getBounds(), {{ padding: [60, 60] }});

        // Marcadores Origem e Destino
        var iconOrigem = L.divIcon({{
            html: '<div style=\"background:#22c55e; color:#fff; border-radius:50%; width:32px; height:32px; display:flex; align-items:center; justify-content:center; font-weight:bold; border:2px solid #fff; box-shadow:0 3px 6px rgba(0,0,0,0.4);\">A</div>',
            iconSize: [32, 32], iconAnchor: [16, 16]
        }});
        L.marker(coordsDijk[0], {{ icon: iconOrigem }}).addTo(map).bindPopup('<b>Origem:</b> {nome_origem}');

        var iconDestino = L.divIcon({{
            html: '<div style=\"background:#ef4444; color:#fff; border-radius:50%; width:32px; height:32px; display:flex; align-items:center; justify-content:center; font-weight:bold; border:2px solid #fff; box-shadow:0 3px 6px rgba(0,0,0,0.4);\">🎓</div>',
            iconSize: [32, 32], iconAnchor: [16, 16]
        }});
        L.marker(coordsDijk[coordsDijk.length - 1], {{ icon: iconDestino }}).addTo(map).bindPopup('<b>Destino:</b> {UFS_NAME}');

        // Carros
        var carDijk = L.marker(coordsDijk[0], {{ icon: L.divIcon({{ html: '<div style=\"font-size:26px;\">🚗</div>', iconSize: [26,26], iconAnchor: [13,13] }}), zIndexOffset: 900 }}).addTo(map);
        var carBpr = L.marker(coordsBpr[0], {{ icon: L.divIcon({{ html: '<div style=\"font-size:26px;\">🚙</div>', iconSize: [26,26], iconAnchor: [13,13] }}), zIndexOffset: 950 }}).addTo(map);
        var carMbpr = L.marker(coordsMbpr[0], {{ icon: L.divIcon({{ html: '<div style=\"font-size:28px;\">🏎️</div>', iconSize: [28,28], iconAnchor: [14,14] }}), zIndexOffset: 1000 }}).addTo(map);

        var iDijk = 0, iBpr = 0, iMbpr = 0;
        var isRunning = false;
        var timerId = null;

        var btnPlay = document.getElementById('btn-play');
        var btnReset = document.getElementById('btn-reset');
        var selVel = document.getElementById('sel-vel');

        function stepRace3() {{
            if (!isRunning) return;

            var finDijk = (iDijk >= coordsDijk.length - 1);
            var finBpr = (iBpr >= coordsBpr.length - 1);
            var finMbpr = (iMbpr >= coordsMbpr.length - 1);

            if (!finDijk) {{ iDijk++; carDijk.setLatLng(coordsDijk[iDijk]); }}
            if (!finBpr) {{ iBpr++; carBpr.setLatLng(coordsBpr[iBpr]); }}
            if (!finMbpr) {{ iMbpr++; carMbpr.setLatLng(coordsMbpr[iMbpr]); }}

            if (!finDijk || !finBpr || !finMbpr) {{
                var vel = parseFloat(selVel.value);
                timerId = setTimeout(stepRace3, Math.max(20, 220 / vel));
            }} else {{
                isRunning = false;
                btnPlay.innerText = '▶️ Reiniciar';
            }}
        }}

        btnPlay.onclick = function() {{
            if (isRunning) {{
                isRunning = false;
                clearTimeout(timerId);
                btnPlay.innerText = '▶️ Continuar';
            }} else {{
                if (iDijk >= coordsDijk.length - 1 && iMbpr >= coordsMbpr.length - 1) {{
                    iDijk = 0; iBpr = 0; iMbpr = 0;
                }}
                isRunning = true;
                btnPlay.innerText = '⏸️ Pausar';
                stepRace3();
            }}
        }};

        btnReset.onclick = function() {{
            isRunning = false;
            clearTimeout(timerId);
            iDijk = 0; iBpr = 0; iMbpr = 0;
            carDijk.setLatLng(coordsDijk[0]);
            carBpr.setLatLng(coordsBpr[0]);
            carMbpr.setLatLng(coordsMbpr[0]);
            btnPlay.innerText = '▶️ Iniciar Simulação dos 3';
        }};
    </script>
</body>
</html>
"""
    with open(arquivo_saida, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[+] Mapa e Simulação MBPR gerados com sucesso: {os.path.abspath(arquivo_saida)}")
    return arquivo_saida


# ==============================================================================
# GERADORES DE GRÁFICOS ESTATÍSTICOS COM MATPLOTLIB
# ==============================================================================

def plotar_grafico_dijkstra(G, caminho, metricas, nome_origem, arquivo_png="simulacao_dijkstra.png"):
    """Gera visualização gráfica do trajeto de Dijkstra com perfil de velocidades e distâncias."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # 1. Mapa de nós e arestas no plano (Longitude x Latitude)
    coords = metricas["coordenadas"]
    lons = [c[1] for c in coords]
    lats = [c[0] for c in coords]

    # Amostra de fundo das ruas da cidade
    for u, v in list(G.edges())[:2000]:
        ux, uy = G.nodes[u]["x"], G.nodes[u]["y"]
        vx, vy = G.nodes[v]["x"], G.nodes[v]["y"]
        ax1.plot([ux, vx], [uy, vy], color="#d1d8e0", lw=0.6, alpha=0.5)

    ax1.plot(lons, lats, color="#2563eb", lw=3.5, label="Rota Dijkstra (Menor Distância)", zorder=5)
    ax1.scatter([lons[0]], [lats[0]], color="#16a34a", s=120, label=f"Origem: {nome_origem}", zorder=6)
    ax1.scatter([lons[-1]], [lats[-1]], color="#dc2626", s=140, marker="*", label="Destino: UFS", zorder=6)

    ax1.set_title("Traçado Geográfico da Rota (Aracaju ➔ UFS)", fontsize=12, fontweight="bold")
    ax1.set_xlabel("Longitude")
    ax1.set_ylabel("Latitude")
    ax1.legend(loc="upper left", fontsize=9)
    ax1.grid(True, linestyle="--", alpha=0.5)

    # 2. Perfil de Velocidades e Extensão acumulada
    dist_acumulada = [0.0]
    vels = []
    for d in metricas["detalhes"]:
        dist_acumulada.append(dist_acumulada[-1] + d["length_m"] / 1000.0)
        vels.append(d["speed_kph"])
    vels.append(vels[-1] if vels else 40.0)

    ax2.plot(dist_acumulada, vels, color="#7c3aed", lw=2, marker="o", markersize=3)
    ax2.fill_between(dist_acumulada, vels, color="#7c3aed", alpha=0.2)
    ax2.set_title("Perfil de Velocidade Regulamentar ao Longo da Rota", fontsize=12, fontweight="bold")
    ax2.set_xlabel("Distância Percorrida (km)")
    ax2.set_ylabel("Velocidade (km/h)")
    ax2.grid(True, linestyle="--", alpha=0.5)

    plt.suptitle(f"Simulação Dijkstra: {metricas['distancia_km']:.2f} km | Tempo Fluxo Livre: {metricas['tempo_fluxo_livre_min']:.1f} min",
                 fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(arquivo_png, dpi=150)
    plt.close()
    print(f"[+] Gráfico estático gerado em: {os.path.abspath(arquivo_png)}")


def plotar_grafico_comparativo(metricas_dijkstra, metricas_bpr, metricas_mbpr, arquivo_png="simulacao_mbpr.png"):
    """Gera gráfico de barras comparativo de desempenho entre Dijkstra, BPR e MBPR."""
    metodos = ["Dijkstra Clássico", "BPR Padrão", "MBPR Modificado"]
    distancias = [metricas_dijkstra["distancia_km"], metricas_bpr["distancia_km"], metricas_mbpr["distancia_km"]]
    tempos_reais = [metricas_dijkstra["tempo_mbpr_min"], metricas_bpr["tempo_mbpr_min"], metricas_mbpr["tempo_mbpr_min"]]
    semaforos = [metricas_dijkstra["num_semaforos"], metricas_bpr["num_semaforos"], metricas_mbpr["num_semaforos"]]

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))

    # 1. Distância Total (km)
    cores1 = ["#ef4444", "#f59e0b", "#22c55e"]
    bars1 = ax1.bar(metodos, distancias, color=cores1, width=0.55)
    ax1.set_title("Distância Física (km)", fontsize=12, fontweight="bold")
    ax1.set_ylabel("Quilômetros")
    for bar in bars1:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2.0, yval + 0.1, f"{yval:.2f} km", ha="center", va="bottom", fontweight="bold")
    ax1.grid(axis="y", linestyle="--", alpha=0.5)

    # 2. Tempo de Viagem Real com Atrasos (minutos)
    bars2 = ax2.bar(metodos, tempos_reais, color=cores1, width=0.55)
    ax2.set_title("Tempo Efetivo de Viagem (min)", fontsize=12, fontweight="bold")
    ax2.set_ylabel("Minutos")
    for bar in bars2:
        yval = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2.0, yval + 0.3, f"{yval:.1f} min", ha="center", va="bottom", fontweight="bold")
    ax2.grid(axis="y", linestyle="--", alpha=0.5)

    # 3. Semáforos Enfrentados
    bars3 = ax3.bar(metodos, semaforos, color=cores1, width=0.55)
    ax3.set_title("Cruzamentos com Semáforos", fontsize=12, fontweight="bold")
    ax3.set_ylabel("Quantidade de Semáforos")
    for bar in bars3:
        yval = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2.0, yval + 0.2, f"{int(yval)}", ha="center", va="bottom", fontweight="bold")
    ax3.grid(axis="y", linestyle="--", alpha=0.5)

    plt.suptitle("Comparativo de Desempenho no Trânsito de Aracaju: Dijkstra vs BPR vs MBPR", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(arquivo_png, dpi=150)
    plt.close()
    print(f"[+] Gráfico comparativo gerado em: {os.path.abspath(arquivo_png)}")
