"""
gui_simulador.py - Interface Gráfica Interativa (Tkinter) para Simulação Viária em Aracaju
Trabalho de Teoria dos Grafos: Dijkstra vs BPR vs MBPR
"""

import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import os
import threading
import grafo_utils as gu


class SimuladorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simulador de Rotas: Aracaju ➔ UFS (Dijkstra | BPR | MBPR)")
        self.geometry("980x720")
        self.minsize(850, 600)
        self.configure(bg="#0f172a")

        self.G = None
        self.metricas = {}
        self.caminhos = {}
        self.ponto_selecionado = None

        self._criar_layout()
        # Carregar grafo em background
        threading.Thread(target=self._carregar_grafo, daemon=True).start()

    def _criar_layout(self):
        # Cabeçalho
        header = tk.Frame(self, bg="#1e293b", padx=20, pady=15)
        header.pack(fill="x")

        lbl_titulo = tk.Label(
            header,
            text="🚦 SIMULADOR DE ROTEAMENTO VIÁRIO: ARACAJU ➔ UFS",
            font=("Segoe UI", 16, "bold"),
            bg="#1e293b",
            fg="#38bdf8"
        )
        lbl_titulo.pack(anchor="w")

        lbl_sub = tk.Label(
            header,
            text="Comparativo Teórico-Prático: Dijkstra Clássico vs BPR vs MBPR (Tráfego, Filas e Semáforos)",
            font=("Segoe UI", 10),
            bg="#1e293b",
            fg="#94a3b8"
        )
        lbl_sub.pack(anchor="w")

        # Container Principal
        corpo = tk.Frame(self, bg="#0f172a", padx=20, pady=15)
        corpo.pack(fill="both", expand=True)

        # Painel Esquerdo: Controles
        painel_ctrl = tk.LabelFrame(
            corpo,
            text=" Configurações do Roteamento ",
            font=("Segoe UI", 11, "bold"),
            bg="#1e293b",
            fg="#e2e8f0",
            padx=15,
            pady=15
        )
        painel_ctrl.pack(side="left", fill="y", padx=(0, 15))

        # Ponto de Partida
        tk.Label(painel_ctrl, text="Ponto de Partida (Origem A):", font=("Segoe UI", 10, "bold"), bg="#1e293b", fg="#cbd5e1").pack(anchor="w", pady=(0, 4))
        self.combo_origens = ttk.Combobox(painel_ctrl, state="readonly", width=38, font=("Segoe UI", 9))
        self.opcoes_origens = [f"[{k}] {v['nome']}" for k, v in gu.PONTOS_NOTAVEIS.items()]
        self.combo_origens["values"] = self.opcoes_origens
        self.combo_origens.current(0)
        self.combo_origens.pack(anchor="w", pady=(0, 15))

        # Destino (Fixo UFS)
        tk.Label(painel_ctrl, text="Ponto de Chegada (Destino):", font=("Segoe UI", 10, "bold"), bg="#1e293b", fg="#cbd5e1").pack(anchor="w", pady=(0, 4))
        lbl_dest = tk.Label(painel_ctrl, text="🎓 UFS - Campus São Cristóvão", font=("Segoe UI", 9, "italic"), bg="#334155", fg="#f8fafc", padx=8, pady=6, relief="groove")
        lbl_dest.pack(fill="x", pady=(0, 15))

        # Fator de Pico / Tráfego
        tk.Label(painel_ctrl, text="Intensidade do Tráfego (Pico):", font=("Segoe UI", 10, "bold"), bg="#1e293b", fg="#cbd5e1").pack(anchor="w", pady=(0, 4))
        self.slider_pico = tk.Scale(painel_ctrl, from_=0.6, to=2.0, resolution=0.1, orient="horizontal", bg="#1e293b", fg="#38bdf8", highlightthickness=0)
        self.slider_pico.set(1.3)
        self.slider_pico.pack(fill="x", pady=(0, 15))

        # Botão Executar
        self.btn_executar = tk.Button(
            painel_ctrl,
            text="🚀 Executar e Comparar os 3",
            font=("Segoe UI", 11, "bold"),
            bg="#22c55e",
            fg="#ffffff",
            activebackground="#16a34a",
            cursor="hand2",
            padx=10,
            pady=10,
            command=self._iniciar_calculo
        )
        self.btn_executar.pack(fill="x", pady=(10, 15))

        # Botões de Visualização de Simulação
        tk.Label(painel_ctrl, text="Abrir Simulações no Navegador:", font=("Segoe UI", 10, "bold"), bg="#1e293b", fg="#cbd5e1").pack(anchor="w", pady=(10, 4))
        
        self.btn_sim_dijk = tk.Button(
            painel_ctrl, text="🗺️ Simulação Dijkstra (1 Carro)", font=("Segoe UI", 9), bg="#2563eb", fg="#ffffff",
            cursor="hand2", pady=5, command=lambda: self._abrir_html("simulacao_dijkstra.html")
        )
        self.btn_sim_dijk.pack(fill="x", pady=3)

        self.btn_sim_bpr = tk.Button(
            painel_ctrl, text="🏎️ Simulação BPR (2 Carros)", font=("Segoe UI", 9), bg="#d97706", fg="#ffffff",
            cursor="hand2", pady=5, command=lambda: self._abrir_html("simulacao_bpr.html")
        )
        self.btn_sim_bpr.pack(fill="x", pady=3)

        self.btn_sim_mbpr = tk.Button(
            painel_ctrl, text="🏁 Simulação MBPR (3 Carros + Semáforos)", font=("Segoe UI", 9, "bold"), bg="#059669", fg="#ffffff",
            cursor="hand2", pady=7, command=lambda: self._abrir_html("simulacao_mbpr.html")
        )
        self.btn_sim_mbpr.pack(fill="x", pady=3)

        # Status Label
        self.lbl_status = tk.Label(painel_ctrl, text="Carregando malha viária de Aracaju...", font=("Segoe UI", 9), bg="#1e293b", fg="#facc15")
        self.lbl_status.pack(side="bottom", fill="x", pady=(15, 0))

        # Painel Direito: Tabela e Diagnóstico
        painel_res = tk.LabelFrame(
            corpo,
            text=" Resultados Analíticos e Métricas Comparativas ",
            font=("Segoe UI", 11, "bold"),
            bg="#1e293b",
            fg="#e2e8f0",
            padx=15,
            pady=15
        )
        painel_res.pack(side="right", fill="both", expand=True)

        # Treeview (Tabela Comparativa)
        colunas = ("metrica", "dijkstra", "bpr", "mbpr")
        self.tabela = ttk.Treeview(painel_res, columns=colunas, show="headings", height=8)
        self.tabela.heading("metrica", text="Métrica de Engenharia de Tráfego")
        self.tabela.heading("dijkstra", text="1. Dijkstra Clássico")
        self.tabela.heading("bpr", text="2. BPR Tradicional")
        self.tabela.heading("mbpr", text="3. MBPR (Modificado)")

        self.tabela.column("metrica", width=240, anchor="w")
        self.tabela.column("dijkstra", width=120, anchor="center")
        self.tabela.column("bpr", width=120, anchor="center")
        self.tabela.column("mbpr", width=130, anchor="center")
        self.tabela.pack(fill="x", pady=(0, 15))

        # Caixa de Diagnóstico
        tk.Label(painel_res, text="Diagnóstico Científico da Comparação:", font=("Segoe UI", 10, "bold"), bg="#1e293b", fg="#cbd5e1").pack(anchor="w", pady=(0, 4))
        self.txt_diagnostico = tk.Text(painel_res, bg="#0f172a", fg="#f8fafc", font=("Consolas", 10), wrap="word", relief="flat", padx=10, pady=10)
        self.txt_diagnostico.pack(fill="both", expand=True)

    def _carregar_grafo(self):
        try:
            self.G = gu.carregar_grafo_aracaju("aracaju.graphml")
            self.lbl_status.config(text=" Pronto! Grafo de Aracaju carregado.", fg="#4ade80")
        except Exception as e:
            self.lbl_status.config(text=f" Erro ao carregar: {e}", fg="#f87171")

    def _iniciar_calculo(self):
        if self.G is None:
            messagebox.showwarning("Aguarde", "O grafo de Aracaju ainda está sendo carregado na memória!")
            return

        self.btn_executar.config(state="disabled", text="Calculando...")
        self.lbl_status.config(text="Executando Dijkstra, BPR e MBPR...", fg="#38bdf8")
        threading.Thread(target=self._processar_calculo, daemon=True).start()

    def _processar_calculo(self):
        try:
            # Identificar origem
            idx_selecionado = str(self.combo_origens.current() + 1)
            origem_info = gu.PONTOS_NOTAVEIS[idx_selecionado]
            no_origem = origem_info["node"]
            nome_origem = origem_info["nome"]
            no_destino = gu.UFS_DEFAULT_NODE

            # Aplicar Tráfego com o fator do slider
            nivel_pico = float(self.slider_pico.get())
            gu.aplicar_trafego_realista(self.G, nivel_pico=nivel_pico)

            # 1. Dijkstra
            gu.atualizar_pesos_grafo(self.G, "dijkstra")
            p_dijk, _, _ = gu.dijkstra_algoritmo(self.G, no_origem, no_destino, "weight")
            m_dijk = gu.extrair_metricas_rota(self.G, p_dijk)

            # 2. BPR
            gu.atualizar_pesos_grafo(self.G, "bpr")
            p_bpr, _, _ = gu.dijkstra_algoritmo(self.G, no_origem, no_destino, "weight")
            m_bpr = gu.extrair_metricas_rota(self.G, p_bpr)

            # 3. MBPR
            gu.atualizar_pesos_grafo(self.G, "mbpr")
            p_mbpr, _, _ = gu.dijkstra_algoritmo(self.G, no_origem, no_destino, "weight")
            m_mbpr = gu.extrair_metricas_rota(self.G, p_mbpr)

            # Gerar arquivos de simulação
            gu.gerar_simulacao_dijkstra_html(self.G, p_dijk, m_dijk, nome_origem, "simulacao_dijkstra.html")
            gu.gerar_simulacao_bpr_html(self.G, p_dijk, m_dijk, p_bpr, m_bpr, nome_origem, "simulacao_bpr.html")
            gu.gerar_simulacao_mbpr_html(self.G, p_dijk, m_dijk, p_bpr, m_bpr, p_mbpr, m_mbpr, nome_origem, "simulacao_mbpr.html")

            # Atualizar Interface (Thread Principal)
            self.after(0, lambda: self._atualizar_resultados(m_dijk, m_bpr, m_mbpr, nome_origem))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Erro", str(e)))
        finally:
            self.after(0, lambda: self.btn_executar.config(state="normal", text="🚀 Executar e Comparar os 3"))

    def _atualizar_resultados(self, m_dijk, m_bpr, m_mbpr, nome_origem):
        # Limpar tabela
        for item in self.tabela.get_children():
            self.tabela.delete(item)

        # Inserir métricas
        linhas = [
            ("Distância Total (km)", f"{m_dijk['distancia_km']:.2f} km", f"{m_bpr['distancia_km']:.2f} km", f"{m_mbpr['distancia_km']:.2f} km"),
            ("Tempo Fluxo Livre t0 (min)", f"{m_dijk['tempo_fluxo_livre_min']:.1f} min", f"{m_bpr['tempo_fluxo_livre_min']:.1f} min", f"{m_mbpr['tempo_fluxo_livre_min']:.1f} min"),
            ("Tempo BPR sem Semáforo (min)", f"{m_dijk['tempo_bpr_min']:.1f} min", f"{m_bpr['tempo_bpr_min']:.1f} min", f"{m_mbpr['tempo_bpr_min']:.1f} min"),
            ("Tempo Efetivo Real MBPR (min)", f"{m_dijk['tempo_mbpr_min']:.1f} min", f"{m_bpr['tempo_mbpr_min']:.1f} min", f"{m_mbpr['tempo_mbpr_min']:.1f} min 🏆"),
            ("Cruzamentos com Semáforos", f"{m_dijk['num_semaforos']} 🛑", f"{m_bpr['num_semaforos']} 🛑", f"{m_mbpr['num_semaforos']} 🚦"),
            ("Quantidade de Cruzamentos", f"{m_dijk['num_nos']} nós", f"{m_bpr['num_nos']} nós", f"{m_mbpr['num_nos']} nós")
        ]
        for l in linhas:
            self.tabela.insert("", "end", values=l)

        # Diagnóstico textual
        diff = m_dijk["tempo_mbpr_min"] - m_mbpr["tempo_mbpr_min"]
        pct = (diff / m_dijk["tempo_mbpr_min"]) * 100 if m_dijk["tempo_mbpr_min"] > 0 else 0
        sem_evitados = m_dijk["num_semaforos"] - m_mbpr["num_semaforos"]

        diag = (
            f"=== ANÁLISE COMPARATIVA ({nome_origem} ➔ UFS) ===\n\n"
            f"1. DIJKSTRA CLÁSSICO:\n"
            f"   - Prioriza estritamente a menor distância física ({m_dijk['distancia_km']:.2f} km).\n"
            f"   - Como ignora o congestionamento e os semáforos, o veículo passa por {m_dijk['num_semaforos']} cruzamentos\n"
            f"     semaforizados, levando {m_dijk['tempo_mbpr_min']:.1f} minutos para chegar à UFS.\n\n"
            f"2. BPR TRADICIONAL:\n"
            f"   - Desvia das vias com maior saturação veicular (V/C > 1.0).\n"
            f"   - Contudo, por não penalizar semáforos, ainda atravessa {m_bpr['num_semaforos']} cruzamentos semaforizados.\n\n"
            f"3. MBPR (MODIFICADO - VENCEDOR):\n"
            f"   - O MBPR equilibra distância, filas em supersaturação e tempo perdido nos semáforos.\n"
            f"   - Economia de {diff:.1f} minutos ({pct:.1f}% mais rápido que o Dijkstra)!\n"
            f"   - Evitou {sem_evitados} semáforos no percurso.\n\n"
            f"💡 Clique nos botões à esquerda para abrir as simulações animadas no seu navegador!"
        )

        self.txt_diagnostico.delete("1.0", "end")
        self.txt_diagnostico.insert("1.0", diag)
        self.lbl_status.config(text=" Cálculo concluído com sucesso!", fg="#4ade80")

    def _abrir_html(self, nome_arquivo):
        caminho = os.path.abspath(nome_arquivo)
        if os.path.exists(caminho):
            webbrowser.open(f"file:///{caminho}")
        else:
            messagebox.showinfo("Arquivo não gerado", f"Execute o cálculo primeiro para gerar '{nome_arquivo}'.")


if __name__ == "__main__":
    app = SimuladorApp()
    app.mainloop()
