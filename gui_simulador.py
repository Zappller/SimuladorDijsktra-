"""
gui_simulador.py - Interface gráfica (Tkinter) do Simulador de Rotas Aracaju -> UFS
Trabalho de Teoria dos Grafos: Dijkstra vs BPR vs MBPR

Visual inspirado nos programas de Windows dos anos 90:
cinza clássico, botões em relevo, faixa azul-marinho e barra de status.
"""

import sys
import os
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox

if getattr(sys, "frozen", False):
    os.chdir(sys._MEIPASS)

import grafo_utils as gu


# ---------------------------------------------------------------------------
# Paleta e fontes "Windows 95"
# ---------------------------------------------------------------------------
CINZA = "#c0c0c0"         # cinza das janelas
CINZA_ESCURO = "#808080"  # sombra dos relevos
BRANCO = "#ffffff"
PRETO = "#000000"
AZUL = "#000080"          # azul-marinho da barra de titulo
AZUL_CLARO = "#1084d0"

FONTE = ("MS Sans Serif", 9)
FONTE_B = ("MS Sans Serif", 9, "bold")
FONTE_TITULO = ("MS Sans Serif", 14, "bold")
FONTE_MONO = ("Courier New", 10)

ARQ_DIJKSTRA = "simulacao_dijkstra.html"
ARQ_BPR = "simulacao_bpr.html"
ARQ_MBPR = "simulacao_mbpr.html"

TEXTO_INICIAL = (
    "COMO USAR\n"
    "=========\n\n"
    "1. Escolha de onde você sai (passo 1).\n"
    "2. Ajuste a intensidade do trânsito (passo 2).\n"
    "3. Clique em 'Calcular rotas' ou aperte F5 (passo 3).\n"
    "4. Veja a tabela acima e abra as simulações animadas\n"
    "   no navegador pelos botoes do passo 4.\n\n"
    "O destino é sempre a UFS - Campus São Cristóvão.\n"
)


# ---------------------------------------------------------------------------
# Widgets auxiliares
# ---------------------------------------------------------------------------
def botao(pai, texto, comando, padrao=False, **kw):
    """Botao em relevo no estilo Win95. 'padrao' ganha a borda preta extra."""
    b = tk.Button(
        pai, text=texto, command=comando, font=FONTE_B if padrao else FONTE,
        bg=CINZA, fg=PRETO, activebackground=CINZA, activeforeground=PRETO,
        disabledforeground=CINZA_ESCURO, relief="raised", bd=2,
        padx=8, pady=3, cursor="arrow",
        highlightthickness=1 if padrao else 0,
        highlightbackground=PRETO, highlightcolor=PRETO, **kw
    )
    return b


def grupo(pai, titulo):
    """Caixa de grupo (group box) com borda entalhada."""
    return tk.LabelFrame(
        pai, text=f" {titulo} ", font=FONTE, bg=CINZA, fg=PRETO,
        relief="groove", bd=2, padx=8, pady=6
    )


class BarraProgresso(tk.Canvas):
    """Barra de progresso de blocos azuis, como nos instaladores antigos."""

    BLOCO = 9
    ESPACO = 2

    def __init__(self, pai, largura=240, altura=18):
        super().__init__(pai, width=largura, height=altura, bg=BRANCO,
                         highlightthickness=0, relief="sunken", bd=2)
        self.largura = largura
        self.altura = altura
        self.total = (largura - 4) // (self.BLOCO + self.ESPACO)
        self.pos = 0
        self.rodando = False

    def _desenhar(self, n):
        self.delete("all")
        for i in range(n):
            x = 4 + i * (self.BLOCO + self.ESPACO)
            self.create_rectangle(x, 4, x + self.BLOCO, self.altura,
                                  fill=AZUL, outline=AZUL)

    def _passo(self):
        if not self.rodando:
            return
        self.pos = (self.pos + 1) % (self.total + 1)
        self._desenhar(self.pos)
        self.after(90, self._passo)

    def iniciar(self):
        self.rodando = True
        self.pos = 0
        self._passo()

    def parar(self, cheia=True):
        self.rodando = False
        self._desenhar(self.total if cheia else 0)


# ---------------------------------------------------------------------------
# Janela principal
# ---------------------------------------------------------------------------
class SimuladorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simulador de Rotas - Aracaju -> UFS")
        self.geometry("1000x700")
        self.minsize(860, 600)
        self.configure(bg=CINZA)
        self.option_add("*Font", FONTE)

        self.G = None
        self.calculando = False
        self.chaves_origem = list(gu.PONTOS_NOTAVEIS.keys())

        self._estilo_ttk()
        self._criar_menu()
        self._criar_layout()

        self.bind("<F5>", lambda e: self._iniciar_calculo())
        self.bind("<Return>", lambda e: self._iniciar_calculo())

        self._set_status("Carregando a malha viária de Aracaju. Aguarde...")
        self.barra.iniciar()
        threading.Thread(target=self._carregar_grafo, daemon=True).start()

    # ---------------- Estilo ----------------
    def _estilo_ttk(self):
        st = ttk.Style(self)
        st.theme_use("classic")
        st.configure(".", background=CINZA, foreground=PRETO, font=FONTE)
        st.configure("Treeview", background=BRANCO, fieldbackground=BRANCO,
                     foreground=PRETO, rowheight=22, font=FONTE, borderwidth=0)
        st.configure("Treeview.Heading", background=CINZA, foreground=PRETO,
                     relief="raised", borderwidth=2, font=FONTE_B)
        st.map("Treeview", background=[("selected", AZUL)],
               foreground=[("selected", BRANCO)])
        st.map("Treeview.Heading", background=[("active", CINZA)])
        st.configure("TCombobox", fieldbackground=BRANCO, background=CINZA,
                     arrowsize=15, borderwidth=2)
        st.map("TCombobox",
               fieldbackground=[("readonly", BRANCO)],
               selectbackground=[("readonly", AZUL)],
               selectforeground=[("readonly", BRANCO)])
        self.option_add("*TCombobox*Listbox.background", BRANCO)
        self.option_add("*TCombobox*Listbox.selectBackground", AZUL)
        self.option_add("*TCombobox*Listbox.selectForeground", BRANCO)
        self.option_add("*TCombobox*Listbox.font", FONTE)

    # ---------------- Menu ----------------
    def _criar_menu(self):
        barra = tk.Menu(self, tearoff=0)

        m_arq = tk.Menu(barra, tearoff=0)
        m_arq.add_command(label="Calcular rotas", accelerator="F5",
                          command=self._iniciar_calculo)
        m_arq.add_separator()
        m_arq.add_command(label="Sair", accelerator="Alt+F4",
                          command=self.destroy)
        barra.add_cascade(label="Arquivo", menu=m_arq, underline=0)

        self.m_sim = tk.Menu(barra, tearoff=0)
        self.m_sim.add_command(label="Simulação Dijkstra (1 carro)",
                               command=lambda: self._abrir_html(ARQ_DIJKSTRA))
        self.m_sim.add_command(label="Simulação BPR (2 carros)",
                               command=lambda: self._abrir_html(ARQ_BPR))
        self.m_sim.add_command(label="Simulação MBPR (3 carros + semáforos)",
                               command=lambda: self._abrir_html(ARQ_MBPR))
        barra.add_cascade(label="Simulação", menu=self.m_sim, underline=0)

        m_ajuda = tk.Menu(barra, tearoff=0)
        m_ajuda.add_command(label="Como usar...", command=self._ajuda)
        m_ajuda.add_separator()
        m_ajuda.add_command(label="Sobre...", command=self._sobre)
        barra.add_cascade(label="Ajuda", menu=m_ajuda, underline=1)

        self.config(menu=barra)

    # ---------------- Layout ----------------
    def _criar_layout(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Faixa azul de titulo (estilo instalador dos anos 90)
        faixa = tk.Frame(self, bg=AZUL, padx=14, pady=8)
        faixa.grid(row=0, column=0, sticky="ew")
        tk.Label(faixa, text="Simulador de Rotas  -  Aracaju -> UFS",
                 font=FONTE_TITULO, bg=AZUL, fg=BRANCO).pack(anchor="w")
        tk.Label(faixa,
                 text="Dijkstra clássico  x  BPR  x  MBPR (trânsito, filas e semáforos)",
                 font=FONTE, bg=AZUL, fg=CINZA).pack(anchor="w")

        corpo = tk.Frame(self, bg=CINZA, padx=8, pady=8)
        corpo.grid(row=1, column=0, sticky="nsew")
        corpo.columnconfigure(1, weight=1)
        corpo.rowconfigure(0, weight=1)

        self._painel_controles(corpo)
        self._painel_resultados(corpo)
        self._barra_status()

    def _painel_controles(self, pai):
        esq = tk.Frame(pai, bg=CINZA, width=300)
        esq.grid(row=0, column=0, sticky="ns", padx=(0, 8))

        # Passo 1 - origem
        g1 = grupo(esq, "1. De onde você sai?")
        g1.pack(fill="x", pady=(0, 8))
        tk.Label(g1, text="Origem:", bg=CINZA).pack(anchor="w")
        self.combo_origens = ttk.Combobox(g1, state="readonly", width=40)
        self.combo_origens["values"] = [
            f"{k}. {gu.PONTOS_NOTAVEIS[k]['nome']}" for k in self.chaves_origem]
        self.combo_origens.current(0)
        self.combo_origens.pack(fill="x", pady=(2, 6))

        tk.Label(g1, text="Destino (fixo):", bg=CINZA).pack(anchor="w")
        tk.Label(g1, text="UFS - Campus São Cristóvão", bg=BRANCO, fg=PRETO,
                 relief="sunken", bd=2, anchor="w", padx=4, pady=2
                 ).pack(fill="x", pady=(2, 0))

        # Passo 2 - trânsito
        g2 = grupo(esq, "2. Quanto trânsito?")
        g2.pack(fill="x", pady=(0, 8))
        self.lbl_pico = tk.Label(g2, text="", bg=CINZA, font=FONTE_B)
        self.lbl_pico.pack(anchor="w")
        self.slider_pico = tk.Scale(
            g2, from_=0.6, to=2.0, resolution=0.1, orient="horizontal",
            showvalue=False, bg=CINZA, fg=PRETO, troughcolor=CINZA_ESCURO,
            activebackground=CINZA, highlightthickness=0, relief="flat",
            sliderrelief="raised", bd=2, sliderlength=22,
            command=self._atualizar_lbl_pico)
        self.slider_pico.set(1.3)
        self.slider_pico.pack(fill="x")
        legenda = tk.Frame(g2, bg=CINZA)
        legenda.pack(fill="x")
        tk.Label(legenda, text="Leve", bg=CINZA).pack(side="left")
        tk.Label(legenda, text="Pico", bg=CINZA).pack(side="right")
        tk.Label(legenda, text="Normal", bg=CINZA).pack()
        self._atualizar_lbl_pico()

        # Passo 3 - calcular
        g3 = grupo(esq, "3. Calcular")
        g3.pack(fill="x", pady=(0, 8))
        self.btn_executar = botao(g3, "Calcular rotas  (F5)",
                                  self._iniciar_calculo, padrao=True)
        self.btn_executar.pack(fill="x", ipady=4)
        self.barra = BarraProgresso(g3, largura=250)
        self.barra.pack(fill="x", pady=(8, 2))

        # Passo 4 - simulações
        g4 = grupo(esq, "4. Ver no mapa (abre o navegador)")
        g4.pack(fill="x")
        self.btns_sim = [
            botao(g4, "Dijkstra  -  1 carro",
                  lambda: self._abrir_html(ARQ_DIJKSTRA)),
            botao(g4, "BPR  -  2 carros",
                  lambda: self._abrir_html(ARQ_BPR)),
            botao(g4, "MBPR  -  3 carros + semáforos",
                  lambda: self._abrir_html(ARQ_MBPR)),
        ]
        for b in self.btns_sim:
            b.pack(fill="x", pady=2)
        self._liberar_simulacoes(False)

    def _painel_resultados(self, pai):
        dir_ = tk.PanedWindow(pai, orient="vertical", bg=CINZA,
                              sashrelief="raised", sashwidth=6, bd=0)
        dir_.grid(row=0, column=1, sticky="nsew")

        # Tabela
        g_tab = grupo(dir_, "Resultados")
        moldura = tk.Frame(g_tab, bg=BRANCO, relief="sunken", bd=2)
        moldura.pack(fill="both", expand=True)
        colunas = ("metrica", "dijkstra", "bpr", "mbpr")
        self.tabela = ttk.Treeview(moldura, columns=colunas,
                                   show="headings", height=7)
        self.tabela.heading("metrica", text="Métrica")
        self.tabela.heading("dijkstra", text="Dijkstra")
        self.tabela.heading("bpr", text="BPR")
        self.tabela.heading("mbpr", text="MBPR")
        self.tabela.column("metrica", width=240, anchor="w")
        for c in ("dijkstra", "bpr", "mbpr"):
            self.tabela.column(c, width=120, anchor="center")
        self.tabela.pack(fill="both", expand=True)
        dir_.add(g_tab, minsize=190, stretch="always")

        # Análise em texto
        g_txt = grupo(dir_, "Análise")
        caixa = tk.Frame(g_txt, bg=CINZA)
        caixa.pack(fill="both", expand=True)
        scroll = tk.Scrollbar(caixa, orient="vertical")
        scroll.pack(side="right", fill="y")
        self.txt_diagnostico = tk.Text(
            caixa, bg=BRANCO, fg=PRETO, font=FONTE_MONO, wrap="word",
            relief="sunken", bd=2, padx=8, pady=6,
            selectbackground=AZUL, selectforeground=BRANCO,
            yscrollcommand=scroll.set)
        self.txt_diagnostico.pack(side="left", fill="both", expand=True)
        scroll.config(command=self.txt_diagnostico.yview)
        self._escrever_analise(TEXTO_INICIAL)
        dir_.add(g_txt, minsize=180, stretch="always")

    def _barra_status(self):
        sb = tk.Frame(self, bg=CINZA, pady=2, padx=2)
        sb.grid(row=2, column=0, sticky="ew")
        self.lbl_status = tk.Label(sb, text="", bg=CINZA, anchor="w",
                                   relief="sunken", bd=1, padx=4)
        self.lbl_status.pack(side="left", fill="x", expand=True)
        self.lbl_grafo = tk.Label(sb, text="Grafo: --", bg=CINZA, anchor="w",
                                  relief="sunken", bd=1, padx=4, width=26)
        self.lbl_grafo.pack(side="right", padx=(2, 0))

    # ---------------- Utilitarios de interface ----------------
    def _set_status(self, texto):
        self.lbl_status.config(text=texto)

    def _escrever_analise(self, texto):
        self.txt_diagnostico.config(state="normal")
        self.txt_diagnostico.delete("1.0", "end")
        self.txt_diagnostico.insert("1.0", texto)
        self.txt_diagnostico.config(state="disabled")

    def _atualizar_lbl_pico(self, _=None):
        v = float(self.slider_pico.get())
        if v < 0.9:
            desc = "leve"
        elif v <= 1.4:
            desc = "normal"
        else:
            desc = "horário de pico"
        self.lbl_pico.config(text=f"Fator {v:.1f}x  ({desc})")

    def _liberar_simulacoes(self, liberar):
        estado = "normal" if liberar else "disabled"
        for b in self.btns_sim:
            b.config(state=estado)
        for i in range(3):
            self.m_sim.entryconfig(i, state=estado)

    # ---------------- Carregamento do grafo ----------------
    def _carregar_grafo(self):
        try:
            G = gu.carregar_grafo_aracaju("aracaju.graphml")
            self.after(0, lambda: self._grafo_pronto(G))
        except Exception as e:
            msg = str(e)
            self.after(0, lambda: self._grafo_erro(msg))

    def _grafo_pronto(self, G):
        self.G = G
        self.barra.parar(cheia=False)
        self._set_status("Pronto. Escolha a origem e clique em 'Calcular rotas'.")
        self.lbl_grafo.config(
            text=f"Grafo: {G.number_of_nodes()} nós, {G.number_of_edges()} arestas")

    def _grafo_erro(self, msg):
        self.barra.parar(cheia=False)
        self._set_status("Erro ao carregar o grafo.")
        self.lbl_grafo.config(text="Grafo: erro")
        messagebox.showerror("Erro", f"Não foi possível carregar o mapa:\n\n{msg}")

    # ---------------- Cálculo ----------------
    def _iniciar_calculo(self):
        if self.calculando:
            return
        if self.G is None:
            messagebox.showwarning(
                "Aguarde", "O mapa de Aracaju ainda está sendo carregado.")
            return

        # Le os controles aqui, na thread principal
        chave = self.chaves_origem[self.combo_origens.current()]
        nivel_pico = float(self.slider_pico.get())

        self.calculando = True
        self.btn_executar.config(state="disabled", text="Calculando...")
        self._liberar_simulacoes(False)
        self._set_status("Calculando Dijkstra, BPR e MBPR. Isso pode levar alguns segundos...")
        self.barra.iniciar()
        threading.Thread(target=self._processar_calculo,
                         args=(chave, nivel_pico), daemon=True).start()

    def _processar_calculo(self, chave, nivel_pico):
        try:
            origem_info = gu.PONTOS_NOTAVEIS[chave]
            no_origem = origem_info["node"]
            nome_origem = origem_info["nome"]
            no_destino = gu.UFS_DEFAULT_NODE

            gu.aplicar_trafego_realista(self.G, nivel_pico=nivel_pico)

            gu.atualizar_pesos_grafo(self.G, "dijkstra")
            p_dijk, _, _ = gu.dijkstra_algoritmo(self.G, no_origem, no_destino, "weight")
            m_dijk = gu.extrair_metricas_rota(self.G, p_dijk)

            gu.atualizar_pesos_grafo(self.G, "bpr")
            p_bpr, _, _ = gu.dijkstra_algoritmo(self.G, no_origem, no_destino, "weight")
            m_bpr = gu.extrair_metricas_rota(self.G, p_bpr)

            gu.atualizar_pesos_grafo(self.G, "mbpr")
            p_mbpr, _, _ = gu.dijkstra_algoritmo(self.G, no_origem, no_destino, "weight")
            m_mbpr = gu.extrair_metricas_rota(self.G, p_mbpr)

            coords = origem_info["coords"]
            gu.gerar_simulacao_dijkstra_html(
                self.G, p_dijk, m_dijk, nome_origem, ARQ_DIJKSTRA, coord_origem=coords)
            gu.gerar_simulacao_bpr_html(
                self.G, p_dijk, m_dijk, p_bpr, m_bpr, nome_origem, ARQ_BPR,
                coord_origem=coords)
            gu.gerar_simulacao_mbpr_html(
                self.G, p_dijk, m_dijk, p_bpr, m_bpr, p_mbpr, m_mbpr,
                nome_origem, ARQ_MBPR, coord_origem=coords)

            self.after(0, lambda: self._calculo_ok(m_dijk, m_bpr, m_mbpr, nome_origem))
        except Exception as e:
            msg = str(e)
            self.after(0, lambda: self._calculo_erro(msg))

    def _fim_calculo(self):
        self.calculando = False
        self.btn_executar.config(state="normal", text="Calcular rotas  (F5)")

    def _calculo_erro(self, msg):
        self._fim_calculo()
        self.barra.parar(cheia=False)
        self._set_status("Erro durante o cálculo.")
        messagebox.showerror("Erro", f"Ocorreu um erro no cálculo:\n\n{msg}")

    def _calculo_ok(self, m_dijk, m_bpr, m_mbpr, nome_origem):
        self._fim_calculo()
        self.barra.parar(cheia=True)

        for item in self.tabela.get_children():
            self.tabela.delete(item)

        def lin(rotulo, chave, fmt):
            return (rotulo, fmt.format(m_dijk[chave]),
                    fmt.format(m_bpr[chave]), fmt.format(m_mbpr[chave]))

        linhas = [
            lin("Distância total", "distancia_km", "{:.2f} km"),
            lin("Tempo em fluxo livre", "tempo_fluxo_livre_min", "{:.1f} min"),
            lin("Tempo BPR (sem semáforo)", "tempo_bpr_min", "{:.1f} min"),
            lin("Tempo real (MBPR)", "tempo_mbpr_min", "{:.1f} min"),
            lin("Semaforos no caminho", "num_semaforos", "{}"),
            lin("Cruzamentos (nós)", "num_nos", "{}"),
        ]
        for l in linhas:
            self.tabela.insert("", "end", values=l)

        diff = m_dijk["tempo_mbpr_min"] - m_mbpr["tempo_mbpr_min"]
        pct = (diff / m_dijk["tempo_mbpr_min"]) * 100 if m_dijk["tempo_mbpr_min"] > 0 else 0
        sem_evitados = m_dijk["num_semaforos"] - m_mbpr["num_semaforos"]

        if diff > 0:
            conclusao = (f"   - Economia de {diff:.1f} min ({pct:.1f}% mais rápido "
                         f"que o Dijkstra).\n"
                         f"   - Evitou {sem_evitados} semáforo(s) no percurso.\n")
        else:
            conclusao = (f"   - Neste cenário o MBPR não ganhou do Dijkstra "
                         f"(diferença de {abs(diff):.1f} min).\n")

        diag = (
            f"ANÁLISE: {nome_origem} -> UFS\n"
            f"{'=' * 50}\n\n"
            f"1. DIJKSTRA CLÁSSICO\n"
            f"   - Busca só a menor distância ({m_dijk['distancia_km']:.2f} km).\n"
            f"   - Ignora trânsito e semáforos: passa por {m_dijk['num_semaforos']}\n"
            f"     semáforo(s) e leva {m_dijk['tempo_mbpr_min']:.1f} min.\n\n"
            f"2. BPR TRADICIONAL\n"
            f"   - Desvia das vias mais saturadas (V/C > 1).\n"
            f"   - Não penaliza semáforos: ainda passa por {m_bpr['num_semaforos']}.\n\n"
            f"3. MBPR (MODIFICADO)\n"
            f"   - Equilibra distância, filas e tempo parado em semáforo.\n"
            f"{conclusao}\n"
            f"Use o passo 4 (ou o menu Simulação) para ver os carros no mapa."
        )
        self._escrever_analise(diag)
        self._liberar_simulacoes(True)
        self._set_status(f"Cálculo concluído: {nome_origem} -> UFS.")

    # ---------------- Simulacoes e ajuda ----------------
    def _abrir_html(self, nome_arquivo):
        caminho = os.path.abspath(nome_arquivo)
        if os.path.exists(caminho):
            webbrowser.open(f"file:///{caminho}")
            self._set_status(f"Abrindo {nome_arquivo} no navegador...")
        else:
            messagebox.showinfo(
                "Arquivo não encontrado",
                f"Calcule as rotas primeiro para gerar '{nome_arquivo}'.")

    def _ajuda(self):
        messagebox.showinfo("Como usar", TEXTO_INICIAL)

    def _sobre(self):
        messagebox.showinfo(
            "Sobre",
            "Simulador de Rotas - Aracaju -> UFS\n\n"
            "Trabalho de Introdução à Teoria dos Grafos (UFS)\n"
            "Compara Dijkstra, BPR e MBPR na malha viária real de Aracaju.")


if __name__ == "__main__":
    app = SimuladorApp()
    app.mainloop()
