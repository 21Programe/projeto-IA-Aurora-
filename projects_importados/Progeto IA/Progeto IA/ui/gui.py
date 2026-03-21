# ui/gui.py
import os
import re
import time
import queue
import sqlite3
import threading
import webbrowser
import psutil
import subprocess
from datetime import datetime
import speech_recognition as sr
import customtkinter as ctk
from tkinter import ttk, filedialog

# ==========================================
# IMPORTAÇÕES DA ARQUITETURA MODULAR
# ==========================================
from config.settings import DB_PATH, KNOWLEDGE_SUBDIRS
from memory.sqlite_store import obter_historico_para_ia, salvar_interacao_bd
from memory.rag_engine import gerenciador_rag, gerenciador_memoria_longa, AutoKnowledgeIngestor
from core.orchestrator import RedTeamTaskOrchestrator
from services.sentinel import SystemSentinel
from services.monitor import AuroraMonitorAndEvasion
from voice.tts import AuroraVoiceSystem
from vision.image_analyzer import AuroraVisionSystem
from agents.tactical_agent import AuroraTacticalAgent
from llm.local_llm import consultar_ia_local
from tools.web_search import WebReconTools
from tools.automation_tools import AuroraPentestAutomation
from tools.exif_tool import AuroraForensics
from tools.project_importer import ProjectImporter
# Importações dos Componentes Visuais Extraídos
from ui.components import TechStackPanel, FontesRAGPanel
from ui.windows import SandboxWindow

class AuroraGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AURORA IA - Cyber Security OS (Terminal Root)")
        self.geometry("1600x850")
        ctk.set_appearance_mode("dark")
        self.configure(fg_color="#000000")

        self.grid_columnconfigure(1, weight=3) 
        self.grid_columnconfigure(2, weight=2) 
        self.grid_rowconfigure(0, weight=1)

        # ---------------------------------------------------------
        # INICIALIZAÇÃO DOS MOTORES GLOBAIS
        # ---------------------------------------------------------
        self.fila_mensagens = queue.Queue()
        self.orchestrator = RedTeamTaskOrchestrator(self.fila_mensagens, max_workers=8)
        self.sentinel = SystemSentinel(self.orchestrator)
        self.monitor_evasao = AuroraMonitorAndEvasion(self.fila_mensagens, self.log_na_tela)
        self.voice_sys = AuroraVoiceSystem()
        self.auto_knowledge = AutoKnowledgeIngestor(gerenciador_rag, lambda m: self.log_na_tela(m, autor="KNOWLEDGE"))
        self.agente_tatico = AuroraTacticalAgent(consultar_ia_local, self.orchestrator)
        
        # ---------------------------------------------------------
        # CONSTRUÇÃO DA BARRA LATERAL (SIDEBAR)
        # ---------------------------------------------------------
        self.sidebar = ctk.CTkFrame(self, width=220, fg_color="#000000", corner_radius=0, border_width=1, border_color="#1f232e")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(6, weight=1) 
        
        self.logo_frame = ctk.CTkFrame(self.sidebar, width=200, height=100, fg_color="transparent")
        self.logo_frame.grid(row=0, column=0, pady=(35, 35), padx=10)
        self.logo_frame.grid_propagate(False)

        # Efeitos de Neon do Logo
        for dx, dy in [(-2,0), (2,0), (0,-2), (0,2)]: ctk.CTkLabel(self.logo_frame, text="AURORA IA", font=("Consolas", 26, "bold"), text_color="#004488", fg_color="transparent").place(x=100+dx, y=35+dy, anchor="center")
        for dx, dy in [(-1,-1), (1,-1), (-1,1), (1,1)]: ctk.CTkLabel(self.logo_frame, text="AURORA IA", font=("Consolas", 26, "bold"), text_color="#00aaff", fg_color="transparent").place(x=100+dx, y=35+dy, anchor="center")
        ctk.CTkLabel(self.logo_frame, text="AURORA IA", font=("Consolas", 26, "bold"), text_color="#00ffcc", fg_color="transparent").place(x=100, y=35, anchor="center")
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]: ctk.CTkLabel(self.logo_frame, text="[ c o r e ]", font=("Consolas", 14, "bold"), text_color="#005500", fg_color="transparent").place(x=100+dx, y=70+dy, anchor="center")
        ctk.CTkLabel(self.logo_frame, text="[ c o r e ]", font=("Consolas", 14, "bold"), text_color="#39ff14", fg_color="transparent").place(x=100, y=70, anchor="center")

        btn_style = {"fg_color": "transparent", "border_width": 2, "font": ("Consolas", 14, "bold"), "anchor": "center", "height": 45, "corner_radius": 0}

        # Botões
        self.btn_chat = ctk.CTkButton(self.sidebar, text="[ TERMINAL TÁTICO ]", hover_color="#003322", border_color="#00ffcc", text_color="#00ffcc", command=self.mostrar_chat, **btn_style)
        self.btn_chat.grid(row=1, column=0, pady=10, padx=20, sticky="ew")
        self.btn_vuln = ctk.CTkButton(self.sidebar, text="[ DB AMEAÇAS ]", hover_color="#332200", border_color="#ffcc00", text_color="#ffcc00", command=self.mostrar_relatorios, **btn_style)
        self.btn_vuln.grid(row=2, column=0, pady=10, padx=20, sticky="ew")
        self.btn_rag = ctk.CTkButton(self.sidebar, text="[ RAG VETORIAL ]", hover_color="#001133", border_color="#0066ff", text_color="#0066ff", command=self.acao_ingerir_pdf, **btn_style)
        self.btn_rag.grid(row=3, column=0, pady=10, padx=20, sticky="ew")
        self.btn_sandbox = ctk.CTkButton(self.sidebar, text="[ SANDBOX ISOLADO ]", hover_color="#330033", border_color="#cc00ff", text_color="#cc00ff", command=self.acao_abrir_sandbox, **btn_style)
        self.btn_sandbox.grid(row=4, column=0, pady=10, padx=20, sticky="ew")
        self.btn_blockchain = ctk.CTkButton(self.sidebar, text="[ PENTEST BLOCKCHAIN ]", hover_color="#1a1a1a", border_color="#ff3399", text_color="#ff3399", command=self.acao_blockchain_pentest, **btn_style)
        self.btn_blockchain.grid(row=5, column=0, pady=10, padx=20, sticky="ew")
        self.btn_reader = ctk.CTkButton(self.sidebar, text="[ LEITOR TÁTICO ]", hover_color="#001a1a", border_color="#00ffff", text_color="#00ffff", command=self.mostrar_leitor_documentos, **btn_style)
        self.btn_reader.grid(row=6, column=0, pady=10, padx=20, sticky="ew")
        self.btn_clear = ctk.CTkButton(self.sidebar, text="[ PURGAR RAM ]", hover_color="#440000", border_color="#ff0033", text_color="#ff0033", command=self.acao_limpar_banco, **btn_style)
        self.btn_clear.grid(row=7, column=0, pady=(10, 30), padx=20, sticky="ew")
       # (Código existente)
        self.btn_dashboard = ctk.CTkButton(self.sidebar, text="[ DASHBOARD IA ]", hover_color="#113300", border_color="#66ff66", text_color="#66ff66", command=self.mostrar_dashboard_knowledge, **btn_style)
        self.btn_dashboard.grid(row=8, column=0, pady=10, padx=20, sticky="ew") # Mudei o pady aqui
        
        # COLE ESTAS DUAS LINHAS:
        self.btn_import_zip = ctk.CTkButton(self.sidebar, text="[ IMPORTAR ZIP ]", hover_color="#2b4c1e", border_color="#39ff14", text_color="#39ff14", command=self.acao_importar_zip, **btn_style)
        self.btn_import_zip.grid(row=9, column=0, pady=(0, 30), padx=20, sticky="ew")
        
        # ---------------------------------------------------------
        # FRAMES PRINCIPAIS
        # ---------------------------------------------------------
        self.main_frame = ctk.CTkFrame(self, fg_color="#000000", corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=2)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1) 

        self.code_frame = ctk.CTkFrame(self, fg_color="#000000", corner_radius=0, border_width=1, border_color="#1f232e")
        self.code_frame.grid(row=0, column=2, sticky="nsew")
        self.code_frame.grid_columnconfigure(0, weight=1)
        self.code_frame.grid_rowconfigure(1, weight=0)
        self.code_frame.grid_rowconfigure(2, weight=1)

        self.code_header = ctk.CTkLabel(self.code_frame, text="</> PAINEL DE ANÁLISE E EXTRAÇÃO", font=("Consolas", 14, "bold"), text_color="#39ff14", fg_color="#0a0c10", height=40)
        self.code_header.grid(row=0, column=0, sticky="ew")

        self.code_display = ctk.CTkTextbox(self.code_frame, state="disabled", fg_color="#000000", text_color="#39ff14", font=("Consolas", 14), border_width=0, corner_radius=0)
        self.code_display.grid(row=2, column=0, sticky="nsew", padx=2, pady=2)

        # CHAMA A TELA DE LOGIN ANTES DE TUDO
        self.construir_tela_login()

    # ==========================================
    # UTILITÁRIOS DA INTERFACE
    # ==========================================
    def limpar_area_principal(self):
        for widget in self.main_frame.winfo_children(): widget.destroy()
    
   

    def construir_tela_login(self):
        """Cria o portão de segurança do sistema."""
        self.frame_login = ctk.CTkFrame(self, fg_color="#000000", corner_radius=0)
        self.frame_login.place(relx=0, rely=0, relwidth=1, relheight=1)

        ctk.CTkLabel(self.frame_login, text="AURORA SYSTEM KERNEL", font=("Consolas", 45, "bold"), text_color="#00ffcc").pack(pady=(200, 10))
        ctk.CTkLabel(self.frame_login, text="ACESSO RESTRITO - INSIRA A CREDENCIAL DE ADMINISTRADOR", font=("Consolas", 18), text_color="#ff0033").pack(pady=20)

        self.entry_senha = ctk.CTkEntry(self.frame_login, show="*", width=350, height=50, font=("Consolas", 24), fg_color="#0a0c10", border_color="#00ffcc", justify="center")
        self.entry_senha.pack(pady=20)
        self.entry_senha.focus() 
        self.entry_senha.bind("<Return>", lambda e: self.verificar_login())

        ctk.CTkButton(self.frame_login, text="[ AUTENTICAR ]", width=200, height=50, font=("Consolas", 18, "bold"), fg_color="#003322", hover_color="#00ffcc", text_color="#ffffff", command=self.verificar_login).pack(pady=20)

        self.label_erro_login = ctk.CTkLabel(self.frame_login, text="", font=("Consolas", 16, "bold"), text_color="#ff0000")
        self.label_erro_login.pack(pady=10)

    def verificar_login(self):
        """Valida a credencial e destrava o sistema."""
        senha_digitada = self.entry_senha.get()
        senha_correta = "root2026" 
        
        if senha_digitada == senha_correta:
            self.frame_login.destroy()
            self.mostrar_chat()
            self.after(100, self.verificar_fila_de_mensagens)
            self.iniciar_sequencia_de_boot()
        else:
            self.entry_senha.delete(0, "end")
            self.label_erro_login.configure(text="❌ ACESSO NEGADO. TENTATIVA REGISTRADA NO LOG.")

    

    def atualizar_painel_codigo(self, texto):
        if hasattr(self, "frame_top_panel") and self.frame_top_panel.winfo_exists():
            self.frame_top_panel.destroy()
        self.code_display.grid(row=2, column=0, sticky="nsew", padx=2, pady=2)
        self.code_display.configure(state="normal")
        self.code_display.delete("1.0", "end")
        self.code_display.insert("1.0", texto)
        self.code_display.configure(state="disabled")

    def log_na_tela(self, texto, autor="Aurora"):
        self.fila_mensagens.put((autor, texto))
        print(f"{autor}: {texto}")

    def falar_e_logar(self, texto):
        self.log_na_tela(texto, autor="Aurora")
        import subprocess, pygame, os, time, threading

        def disparar_voz_neural_estavel():
            try:
                proc = subprocess.run(["python", "voice/aurora_voz.py", texto], capture_output=True, text=True, check=True, cwd=os.getcwd())
                caminho_audio_gerado = proc.stdout.strip()
                
                if not caminho_audio_gerado or not caminho_audio_gerado.endswith(".mp3"):
                    return

                if not pygame.mixer.get_init(): pygame.mixer.init()
                
                pygame.mixer.music.load(caminho_audio_gerado)
                pygame.mixer.music.play()

                while pygame.mixer.music.get_busy():
                    time.sleep(0.05)

                pygame.mixer.music.unload()
                
                try: os.remove(caminho_audio_gerado)
                except: pass
            except Exception: pass

        threading.Thread(target=disparar_voz_neural_estavel, daemon=True).start()

    # ==========================================
    # CONSTRUÇÃO DE JANELAS E PAINÉIS
    # ==========================================
    def mostrar_chat(self):
        self.limpar_area_principal()

        status_frame = ctk.CTkFrame(self.main_frame, fg_color="#0a0c10", height=35, corner_radius=0)
        status_frame.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(status_frame, text="🟢 AUTO-CURA ATIVA | 🟢 WATCHDOG ONLINE", font=("Consolas", 12), text_color="#00ffcc").pack(side="right", padx=15, pady=5)
        ctk.CTkLabel(status_frame, text="root@aurora-core:~# logs_operacionais", font=("Consolas", 12, "bold"), text_color="#a9b1d6").pack(side="left", padx=15, pady=5)

        self.chat_display = ctk.CTkTextbox(self.main_frame, state="disabled", fg_color="#000000", text_color="#00ffcc", font=("Consolas", 15), border_width=0, corner_radius=0)
        self.chat_display.grid(row=1, column=0, sticky="nsew", padx=1, pady=1)
        self.chat_display.tag_config("usuario", foreground="#a9b1d6") 
        self.chat_display.tag_config("aurora", foreground="#00ffcc") 
        self.chat_display.tag_config("sistema", foreground="#ffcc00")

        historico = obter_historico_para_ia(limite=20)
        self.chat_display.configure(state="normal")
        for msg in historico:
            if msg.get("role") == "user": self.chat_display.insert("end", f"\n>_ [HISTÓRICO]\n{msg.get('content')}\n", "usuario")
            elif msg.get("role") == "assistant": self.chat_display.insert("end", f"\n[AURORA - MEMÓRIA]\n{msg.get('content')}\n", "aurora")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

        input_frame = ctk.CTkFrame(self.main_frame, fg_color="#0a0c10", height=60, corner_radius=0)
        input_frame.grid(row=2, column=0, sticky="ew")
        input_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(input_frame, text=">_", font=("Consolas", 20, "bold"), text_color="#00ffcc").grid(row=0, column=0, padx=(15, 5), pady=15)
        self.entry_msg = ctk.CTkEntry(input_frame, placeholder_text="Aguardando diretrizes táticas...", font=("Consolas", 15), fg_color="transparent", border_width=0, text_color="#ffffff")
        self.entry_msg.grid(row=0, column=1, sticky="ew", padx=5, pady=15)
        
        self.entry_msg.unbind("<Return>")
        self.entry_msg.bind("<Return>", lambda e: self.receber_texto())
        
        self.btn_voice = ctk.CTkButton(input_frame, text="🎙️ AUDIO UPLINK", width=120, height=40, fg_color="transparent", border_color="#00ffcc", border_width=2, text_color="#00ffcc", hover_color="#003322", font=("Consolas", 12, "bold"), command=self.receber_voz, corner_radius=0)
        self.btn_voice.grid(row=0, column=2, padx=(10, 15), pady=15)
        self.btn_vision = ctk.CTkButton(input_frame, text="👁️ VISION UPLINK", width=120, height=40, fg_color="transparent", border_color="#cc00ff", border_width=2, text_color="#cc00ff", hover_color="#330033", font=("Consolas", 12, "bold"), command=self.acao_analise_visual, corner_radius=0)
        self.btn_vision.grid(row=0, column=3, padx=(10, 15), pady=15)
        self.btn_forensic = ctk.CTkButton(input_frame, text="🔍 EXIF FORENSICS", width=120, height=40, fg_color="transparent", border_color="#ffcc00", border_width=2, text_color="#ffcc00", hover_color="#332200", font=("Consolas", 12, "bold"), command=self.acao_analise_forense, corner_radius=0)
        self.btn_forensic.grid(row=0, column=4, padx=(10, 15), pady=15)
        self.btn_face = ctk.CTkButton(input_frame, text="👤 FACE OSINT", width=120, height=40, fg_color="transparent", border_color="#ff3399", border_width=2, text_color="#ff3399", hover_color="#33001a", font=("Consolas", 12, "bold"), command=self.acao_selecionar_alvo_biometrico, corner_radius=0)
        self.btn_face.grid(row=0, column=5, padx=(10, 15), pady=15)

    def mostrar_dashboard_knowledge(self):
        self.limpar_area_principal() 
        ctk.CTkLabel(self.main_frame, text="📚 Centro de Inteligência e Biblioteca IA", font=("Consolas", 20, "bold"), text_color="#66ff66").pack(pady=20)
        
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#0a0c10", foreground="#66ff66", fieldbackground="#0a0c10", borderwidth=0, font=("Consolas", 10))
        style.configure("Treeview.Heading", background="#003311", foreground="#66ff66", font=("Consolas", 11, "bold"), borderwidth=1, relief="flat")
        style.map("Treeview", background=[("selected", "#005522")])

        colunas = ("id", "titulo", "autores", "categoria", "fonte", "status")
        tree = ttk.Treeview(self.main_frame, columns=colunas, show="headings", height=15)
        
        cabecalhos = ["ID", "Título do Artefato", "Autor(es)", "Categoria", "Fonte", "Status"]
        tamanhos = [40, 350, 150, 100, 100, 100]
        
        for col, texto, tam in zip(colunas, cabecalhos, tamanhos):
            tree.heading(col, text=texto)
            tree.column(col, width=tam, anchor="w" if col in ["titulo", "autores"] else "center")
            
        try:
            import sqlite3
            from config.settings import DB_PATH
            conn = sqlite3.connect(DB_PATH, timeout=20, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("SELECT id_item, titulo, autores, categoria, fonte, status FROM knowledge_catalog ORDER BY id_item DESC")
            linhas_osint = cursor.fetchall()

            try:
                cursor.execute("SELECT id_chunk, origem, 'Desconhecido', categoria, 'LOCAL', 'INDEXADO' FROM base_conhecimento_rag GROUP BY origem")
                linhas_locais = cursor.fetchall()
            except:
                linhas_locais = []
                
            conn.close()
            
            for linha in linhas_locais:
                tree.insert("", "end", values=linha, tags=('local',))
            for linha in linhas_osint:
                tree.insert("", "end", values=linha)
                
            tree.tag_configure('local', foreground="#00ccff")
            if not linhas_osint and not linhas_locais:
                tree.insert("", "end", values=("", "Nenhum artefato catalogado ainda.", "", "", "", ""))
                
        except Exception as e:
            self.log_na_tela(f"Erro ao carregar catálogo: {e}", autor="SISTEMA")

        tree.pack(expand=True, fill="both", padx=20, pady=(0, 20))
        
        frame_comando = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        frame_comando.pack(pady=(0, 20))

        self.entrada_alvo = ctk.CTkEntry(frame_comando, placeholder_text="Alvo de busca (ex: Python, Kali Linux...)", width=300, font=("Consolas", 12))
        self.entrada_alvo.pack(side="left", padx=10)

        def disparar_busca():
            tema = self.entrada_alvo.get().strip()
            if tema:
                self.log_na_tela(f"🎯 Ordem recebida: Caçar conhecimento sobre '{tema}'", autor="SISTEMA")
                self.auto_knowledge.adicionar_job(tema)
                self.orchestrator.submit_job("AutoKnowledge", lambda: self.auto_knowledge.rodada_descoberta(termos=[tema]))
                self.entrada_alvo.delete(0, "end")
            else:
                self.log_na_tela("📡 Iniciando varredura geral por novos manuais...", autor="SISTEMA")
                self.orchestrator.submit_job("AutoKnowledge", self.auto_knowledge.rodada_descoberta)

        ctk.CTkButton(frame_comando, text="[ EXECUTAR OSINT ]", command=disparar_busca, fg_color="#003311", text_color="#66ff66", border_color="#66ff66", border_width=1).pack(side="left", padx=5)
        ctk.CTkButton(frame_comando, text="[ ATUALIZAR LISTA ]", command=self.mostrar_dashboard_knowledge, fg_color="#1a1a1a", border_color="#0088ff", border_width=1).pack(side="left", padx=5)

    def mostrar_relatorios(self):
        self.limpar_area_principal()
        titulo = ctk.CTkLabel(self.main_frame, text="🛡️ Cluster SQL: Anotações de Risco", font=("Consolas", 18, "bold"), text_color="#ffcc00")
        titulo.pack(pady=10)
        tree = ttk.Treeview(self.main_frame, columns=("id", "alvo", "tipo", "descricao", "data"), show="headings")
        for col, txt in zip(("id", "alvo", "tipo", "descricao", "data"), ("Identificador Hex", "Alvo", "Categoria CVSS", "Análise", "Timestamp")):
            tree.heading(col, text=txt)
        conn = sqlite3.connect(DB_PATH, timeout=20, check_same_thread=False)
        for row in conn.cursor().execute("SELECT * FROM relatorios_vuln ORDER BY id_relatorio DESC").fetchall():
            tree.insert("", "end", values=row)
        conn.close()
        tree.pack(expand=True, fill="both", padx=10, pady=10)

    def mostrar_leitor_documentos(self):
        self.limpar_area_principal()
        ctk.CTkLabel(self.main_frame, text="📖 Leitor Tático de Artefatos", font=("Consolas", 20, "bold"), text_color="#00ffff").pack(pady=20)
        container = ctk.CTkScrollableFrame(self.main_frame, fg_color="#0a0c10", border_width=1, border_color="#00ffff")
        container.pack(expand=True, fill="both", padx=20, pady=10)
        for pasta in KNOWLEDGE_SUBDIRS.values():
            for arquivo in os.listdir(pasta):
                if arquivo.lower().endswith((".pdf", ".txt")):
                    frame_arq = ctk.CTkFrame(container, fg_color="transparent")
                    frame_arq.pack(fill="x", pady=5, padx=10)
                    ctk.CTkLabel(frame_arq, text=f"• {arquivo[:50]}...", font=("Consolas", 12), text_color="#a9b1d6").pack(side="left")
                    btn_ler = ctk.CTkButton(frame_arq, text="ANALISAR", width=80, height=24, fg_color="#00ffff", text_color="#000000", font=("Consolas", 10, "bold"), command=lambda a=arquivo: self.orchestrator.submit_job("Reader", self.processar_comando_mestre, f"Aurora, faça uma análise técnica profunda do arquivo {a}"))
                    btn_ler.pack(side="right", padx=5)

    def acao_abrir_sandbox(self):
        SandboxWindow(self, self.orchestrator, self.log_na_tela)

    # ==========================================
    # LÓGICA DE AÇÕES E COMANDOS
    # ==========================================
    def executar_comandos_locais(self, comando):
        comando_min = comando.lower().strip()
        
        # --- ATALHOS DO PILOTO AUTOMÁTICO ---
        # --- ATALHOS DO PILOTO AUTOMÁTICO E BIBLIOTECA ---
        if comando_min == "ativar auto biblioteca":
            self.log_na_tela("📡 Comando aceito. Iniciando rastreador autônomo de conhecimento em background...", autor="SISTEMA")
            self.orchestrator.submit_job("AutoKnowledge", self.auto_knowledge.rodada_descoberta)
            return True
            
        elif comando_min == "parar auto biblioteca":
            self.log_na_tela("🛑 Cancelando rastreador autônomo.", autor="SISTEMA")
            if hasattr(self.auto_knowledge, 'parar_loop'):
                self.auto_knowledge.parar_loop()
            return True

        elif comando_min.startswith("adicionar tema "):
            tema = comando_min.replace("adicionar tema ", "").strip()
            self.log_na_tela(f"📚 Novo tema adicionado à matriz de estudos: {tema}", autor="SISTEMA")
            if hasattr(self.auto_knowledge, 'adicionar_job'):
                self.auto_knowledge.adicionar_job(tema)
            return True

        elif comando_min.startswith("remover tema "):
            tema = comando_min.replace("remover tema ", "").strip()
            self.log_na_tela(f"🗑️ Tema removido da matriz de estudos: {tema}", autor="SISTEMA")
            if hasattr(self.auto_knowledge, 'remover_job'):
                self.auto_knowledge.remover_job(tema)
            return True

        elif comando_min.startswith("buscar livros sobre "):
            tema = comando_min.replace("buscar livros sobre ", "").strip()
            self.log_na_tela(f"🎯 Ordem recebida: Caçar conhecimento sobre '{tema}'", autor="SISTEMA")
            if hasattr(self.auto_knowledge, 'adicionar_job'):
                self.auto_knowledge.adicionar_job(tema)
            self.orchestrator.submit_job("AutoKnowledge", lambda: self.auto_knowledge.rodada_descoberta(termos=[tema]))
            return True

        elif comando_min == "indexar abertos agora":
            self.log_na_tela("🧠 Iniciando ingestão vetorial (RAG) dos artefatos pendentes...", autor="SISTEMA")
            # Dependendo do nome exato da sua função no ingestor, geralmente é algo como processar_downloads
            if hasattr(self.auto_knowledge, 'processar_downloads_pendentes'):
                self.orchestrator.submit_job("RAG_Indexer", self.auto_knowledge.processar_downloads_pendentes)
            return True

        # --- LIGAÇÃO COM TOOLS DE OSINT E PENTEST ---
        if "auditar seguranca" in comando_min or "auditar segurança" in comando_min:
            url = comando_min.replace("auditar seguranca", "").replace("auditar segurança", "").strip()
            if not url.startswith("http"): url = "http://" + url
            threading.Thread(target=WebReconTools.scan_cabecalhos, args=(url, self.log_na_tela, self.atualizar_painel_codigo), daemon=True).start()
            return True

        elif comando_min.startswith("inspecionar site "):
            url = comando_min.replace("inspecionar site ", "").strip()
            if not url.startswith("http"): url = "http://" + url
            threading.Thread(target=WebReconTools.inspecionar_web, args=(url, self.log_na_tela, self.atualizar_painel_codigo), daemon=True).start()
            return True
      
        # --- MOTOR OSINT FACIAL REAL ---
        elif comando_min.startswith("cacar face "):
            input_cru = comando_min.replace("cacar face ", "").strip()
            
            if not hasattr(self, 'alvo_biometrico') or not self.alvo_biometrico:
                self.log_na_tela("⚠️ ERRO: Nenhum rosto carregado! Clique em [FACE OSINT] primeiro.", autor="SISTEMA")
                return True

            if " " in input_cru:
                self.log_na_tela(f"⚠️ ERRO OSINT: '{input_cru}' não é um username válido. Não use espaços.", autor="SISTEMA")
                self.falar_e_logar("Erro tático. O nome de usuário informado é inválido.")
                return True
            
            alvo_rede = input_cru 
        
        # --- MOTOR DE AUDITORIA DE CÓDIGO (LÊ A PASTA IMPORTADA) ---
        elif comando_min.startswith("auditar projeto "):
            alvo = comando_min.replace("auditar projeto ", "").strip()
            caminho_projeto = os.path.join("projects_importados", alvo)
            
            if not os.path.exists(caminho_projeto):
                self.log_na_tela(f"❌ Erro: O projeto '{alvo}' não foi encontrado em projects_importados.", autor="SISTEMA")
                return True
                
            self.log_na_tela(f"🔍 Extraindo código-fonte de '{alvo}' para a memória da IA...", autor="SISTEMA")
            
            def task_auditoria():
                codigo_compilado = ""
                arquivos_lidos = 0
                
                # Varre a pasta e junta o texto dos códigos
                for root, dirs, files in os.walk(caminho_projeto):
                    for file in files:
                        if file.endswith(('.py', '.html', '.js', '.json')):
                            try:
                                with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                                    # Pega um pedaço de cada arquivo para não explodir a memória
                                    conteudo = f.read()[:1500] 
                                    codigo_compilado += f"\n\n--- ARQUIVO: {file} ---\n{conteudo}"
                                    arquivos_lidos += 1
                            except: pass
                            
                # Limite de segurança para a RTX 2060 (aprox. 15.000 caracteres de contexto)
                codigo_compilado = codigo_compilado[:15000]
                
                self.log_na_tela(f"🧠 {arquivos_lidos} arquivos injetados no córtex. Iniciando análise...", autor="SISTEMA")
                
                comando_oculto = f"[DIRETRIZ DE AUDITORIA DE CÓDIGO SÊNIOR]\nAcabei de importar este projeto de software. Leia a arquitetura abaixo:\n\n{codigo_compilado}\n\nResponda: 1. Do que se trata este projeto exatamente? 2. O que você mudaria ou melhoraria nele?"
                
                # Envia para a IA pensar
                self.orchestrator.submit_job("CodeAudit", self.processar_comando_mestre, comando_oculto)
                
            threading.Thread(target=task_auditoria, daemon=True).start()
            return True

 

            def iniciar_cacada_biometrica_real():
                import subprocess, os
                self.falar_e_logar(f"Iniciando infiltração e coleta tática no alvo {alvo_rede}.")
                self.atualizar_painel_codigo(f"--- 👁️ RELATÓRIO DE CAÇADA BIOMÉTRICA ---\n\nAlvo de Rede: @{alvo_rede}\nFoto Base: {os.path.basename(self.alvo_biometrico)}\n\n[1] 🕷️ Acionando Scraper do Instagram... (Aguarde)")
                
                try:
                    subprocess.run(["python", "coleta_insta.py", alvo_rede], capture_output=True, text=True)
                    self.log_na_tela(f"Coleta em @{alvo_rede} finalizada.", autor="OSINT")

                    self.atualizar_painel_codigo(f"--- 👁️ RELATÓRIO DE CAÇADA BIOMÉTRICA ---\n\nAlvo de Rede: @{alvo_rede}\n\n✅ Coleta finalizada.\n[2] 🔍 Iniciando Motor de Reconhecimento Facial...")
                    
                    caminho_pasta_suspeitos = os.path.join("suspeitos", alvo_rede)
                    proc_biometria = subprocess.run(["python", "biometria_osint.py", self.alvo_biometrico, caminho_pasta_suspeitos], capture_output=True, text=True)
                    
                    relatorio_final = proc_biometria.stdout
                    self.atualizar_painel_codigo(relatorio_final)
                    
                    if "🚨 MATCH CONFIRMADO" in relatorio_final:
                        self.falar_e_logar("Caçada concluída. Alvo localizado com sucesso.")
                    else:
                        self.falar_e_logar("Caçada concluída. Alvo não encontrado na rede informada.")
                        
                except Exception as e:
                    self.log_na_tela(f"Falha no Pipeline OSINT: {e}", autor="SISTEMA")
                    self.atualizar_painel_codigo(f"❌ ERRO CRÍTICO NO PIPELINE:\n{e}")

            threading.Thread(target=iniciar_cacada_biometrica_real, daemon=True).start()
            return True

        elif comando_min.startswith("atacar site "):
            url = comando_min.replace("atacar site ", "").strip()
            if not url.startswith("http"): url = "http://" + url
            threading.Thread(target=AuroraPentestAutomation.explorar_alvo, args=(url, self.log_na_tela, self.atualizar_painel_codigo), daemon=True).start()
            return True

        elif comando_min.startswith("cacar vazamentos "):
            alvo = comando_min.replace("cacar vazamentos ", "").strip()
            threading.Thread(target=WebReconTools.osint_dorking, args=(alvo, self.log_na_tela, self.atualizar_painel_codigo), daemon=True).start()
            return True
            
        elif comando_min.startswith("varrer portas "):
            host = comando_min.replace("varrer portas ", "").strip()
            threading.Thread(target=AuroraPentestAutomation.scan_portas, args=(host, self.log_na_tela, self.atualizar_painel_codigo), daemon=True).start()
            return True
            
        elif comando_min.startswith("mapear diretorios "):
            url = comando_min.replace("mapear diretorios ", "").strip()
            if not url.startswith("http"): url = "http://" + url
            threading.Thread(target=AuroraPentestAutomation.dir_brute, args=(url, self.log_na_tela, self.atualizar_painel_codigo), daemon=True).start()
            return True

        # --- LIGAÇÃO COM MONITOR DE EVASÃO ---
        elif comando_min == "aplicar vacina":
            self.monitor_evasao.vacina_desativar_persistencia()
            return True
        elif comando_min == "ativar persistencia":
            self.monitor_evasao.persistencia_fantasma_sia()
            return True
        elif comando_min == "ativar gatilho panico":
            def monitor_anti_forense():
                PROCESSOS_HOSTIS = ["x64dbg.exe", "wireshark.exe", "processhacker.exe", "ida64.exe", "ollydbg.exe", "ghidra.exe"]
                self.log_na_tela("👁️ GATILHO DE PÂNICO: Escudo anti-forense ativado.", autor="SISTEMA")
                while True:
                    time.sleep(5) 
                    for proc in psutil.process_iter(['name']):
                        try:
                            nome_proc = proc.info['name'].lower()
                            if nome_proc in PROCESSOS_HOSTIS:
                                self.log_na_tela(f"🚨 TENTATIVA DE PERÍCIA: {nome_proc} detectado!", autor="SISTEMA")
                                self.monitor_evasao.exfiltrar_camuflado("ALERTA_DE_CAPTURA_EM_CURSO")
                                self.monitor_evasao.protocolo_scorched_earth()
                                self.log_na_tela("💀 PROTOCOLO SCORCHED EARTH FINALIZADO. Encerrando Kernel...", autor="SISTEMA")
                                time.sleep(2)
                                os._exit(0) 
                        except: continue
            threading.Thread(target=monitor_anti_forense, daemon=True).start()
            return True

        # Comandos básicos do sistema
        elif "que horas" in comando_min:
            self.falar_e_logar(f"Exatas {datetime.now().strftime('%H:%M')}")
            return True
        elif "abrir youtube" in comando_min: webbrowser.open("https://www.youtube.com"); return True
        # --- COMANDO PARA LIMPAR A TELA DO TERMINAL ---
        elif comando_min in ["limpar tela", "clear", "cls"]:
            self.chat_display.configure(state="normal")
            self.chat_display.delete("1.0", "end") # Apaga todo o texto
            self.chat_display.configure(state="disabled")
            
            # Recria o cabeçalho padrão
            self.chat_display.configure(state="normal")
            self.chat_display.insert("end", "\n[LOG INTERNO - SISTEMA]\nTerminal purgado pelo administrador.\n", "sistema")
            self.chat_display.configure(state="disabled")
            return True
        elif "abrir meu github" in comando_min: webbrowser.open("https://github.com/21Programe"); return True
        elif "pesquisar por" in comando_min: webbrowser.open(f"https://www.google.com/search?q={comando_min.replace('pesquisar por', '').strip()}"); return True
        elif "limpar memória" in comando_min: self.acao_limpar_banco(); return True
        return False

    def processar_comando_mestre(self, comando):
        if "sair" in comando:
            self.fila_mensagens.put(("COMANDO_SISTEMA", "sair"))
            return

        if not self.executar_comandos_locais(comando):
            try:
                arquitetura = self.agente_tatico.inferir_arquitetura_tecnologica(comando)
                if arquitetura: self.fila_mensagens.put(("TECH_STACK", arquitetura))

                ctx = gerenciador_rag.recuperar_contexto(comando, limiar_top_k=2)
                fontes_rag = getattr(gerenciador_rag, 'ultimas_fontes', [])
                mem = gerenciador_memoria_longa.resgatar_lembrancas(comando, limiar_top_k=2)

                contexto_oculto = ""
                if mem: contexto_oculto += f"-- LEMBRANÇAS --\n{mem}\n"
                if ctx: contexto_oculto += f"-- MANUAIS --\n{ctx}\n"

                resposta = self.agente_tatico.pensar_e_agir(comando_usuario=comando, historico=obter_historico_para_ia(6), contexto_oculto=contexto_oculto)

                marcadores = chr(96) * 3
                padrao_codigo = marcadores + r"[^\n]*\n(.*?)" + marcadores
                codigos_encontrados = re.findall(padrao_codigo, resposta, re.DOTALL)

                if codigos_encontrados:
                    self.fila_mensagens.put(("CÓDIGO_PAYLOAD", "\n\n".join(codigos_encontrados)))
                    resposta = re.sub(padrao_codigo, "\n\n[⚙️ SCRIPT EXTRAÍDO PARA O PAINEL DE PAYLOAD]\n", resposta, flags=re.DOTALL)
                elif fontes_rag: 
                    self.fila_mensagens.put(("FONTES_RAG", fontes_rag))

                self.falar_e_logar(resposta)
                salvar_interacao_bd(comando, resposta)
            except Exception as e:
                self.log_na_tela(f"Erro no Kernel: {e}", autor="SISTEMA")

    # ==========================================
    # LÓGICA DE EVENTOS (INPUT/OUTPUT)
    # ==========================================
    def iniciar_sequencia_de_boot(self):
        logs_boot = ["Iniciando Kernel Aurora Core...", "Carregando matriz de tensores (Qwen2.5-Coder-7B-Abliterated)... [OK]", "Estabelecendo link FAISS (Memória Vetorial L2)... [OK]", "Iniciando Sandbox de execução efêmera e Sentinela térmico...", "SISTEMA OPERACIONAL PRONTO. Aguardando diretrizes do administrador."]
        for i, log in enumerate(logs_boot): self.after((i + 1) * 1500, lambda l=log: self.fila_mensagens.put(("SISTEMA", l)))
        self.after((len(logs_boot) + 1) * 1500, self.monitor_evasao.camuflar_identidade_sia)
        self.after((len(logs_boot) + 2) * 1500, self.monitor_evasao.enviar_beacon_c2)

    def verificar_fila_de_mensagens(self):
        try:
            if not hasattr(self, "animando") or getattr(self, "animando") == False:
                autor, texto = self.fila_mensagens.get_nowait()
                
                if autor == "COMANDO_SISTEMA" and texto == "sair":
                    self.orchestrator.shutdown()
                    self.quit()
                    return
                if autor == "TECH_STACK":
                    if hasattr(self, "frame_top_panel") and self.frame_top_panel.winfo_exists(): self.frame_top_panel.destroy()
                    self.frame_top_panel = TechStackPanel(self.code_frame, texto)
                    self.frame_top_panel.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
                    self.after(10, self.verificar_fila_de_mensagens)
                    return
                if autor == "FONTES_RAG":
                    if hasattr(self, "frame_top_panel") and self.frame_top_panel.winfo_exists(): self.frame_top_panel.destroy()
                    self.code_display.grid_remove()
                    self.frame_top_panel = FontesRAGPanel(self.code_frame, texto)
                    self.frame_top_panel.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
                    self.after(10, self.verificar_fila_de_mensagens)
                    return
                if autor == "CÓDIGO_PAYLOAD":
                    self.atualizar_painel_codigo(f"# PAYLOAD EXTRAÍDO COM SUCESSO\n# ==========================================\n\n{texto}")
                    self.after(10, self.verificar_fila_de_mensagens)
                    return

                if hasattr(self, "chat_display") and self.chat_display.winfo_exists():
                    if "Usuário" in autor: estilo, prefixo, vel = "usuario", f"\n>_ [{autor}]\n", 5 
                    elif "Aurora" in autor: estilo, prefixo, vel = "aurora", f"\n[RESPOSTA DO SISTEMA - {autor}]\n", 20
                    else: estilo, prefixo, vel = "sistema", f"\n[LOG INTERNO - {autor}]\n", 10
                    self.chat_display.configure(state="normal")
                    self.chat_display.insert("end", prefixo, estilo)
                    self.chat_display.configure(state="disabled")
                    self.chat_display.see("end")
                    self.animando = True
                    self._escrever_letra_por_letra(texto, estilo, vel, 0)
        except queue.Empty: pass
        self.after(100, self.verificar_fila_de_mensagens)

    def _escrever_letra_por_letra(self, texto, estilo, velocidade, index):
        try:
            if not self.chat_display.winfo_exists():
                return
            if index < len(texto):
                self.chat_display.configure(state="normal")
                self.chat_display.insert("end", texto[index], estilo)
                self.chat_display.configure(state="disabled")
                self.chat_display.see("end")
                self.after(velocidade, self._escrever_letra_por_letra, texto, estilo, velocidade, index + 1)
            else:
                self.chat_display.configure(state="normal")
                self.chat_display.insert("end", "\n", estilo)
                self.chat_display.configure(state="disabled")
                self.animando = False
        except Exception:
            self.animando = False

    def receber_texto(self):
        comando = self.entry_msg.get().strip()
        if comando:
            self.entry_msg.delete(0, "end")
            self.log_na_tela(comando, autor="Usuário Terminal")
            self.orchestrator.submit_job("CmdProcessor", self.processar_comando_mestre, comando)

    def receber_voz(self):
        def task_audicao():
            with sr.Microphone() as source:
                self.log_na_tela("🎙️ Escutando...", autor="SISTEMA")
                try:
                    query = sr.Recognizer().recognize_google(sr.Recognizer().listen(source, timeout=5), language="pt-BR").lower()
                    self.log_na_tela(query, autor="Usuário Acústico")
                    self.processar_comando_mestre(query)
                except Exception: self.log_na_tela("Ruído limitando inferência verbal.", autor="SISTEMA")
        self.orchestrator.submit_job("AudioListener", task_audicao)

    def acao_analise_visual(self):
        arq = filedialog.askopenfilename(title="Selecionar Imagem para Análise Visual", filetypes=(("Imagens", "*.png *.jpg *.jpeg"),))
        if not arq: return
        self.log_na_tela(f"Imagem '{os.path.basename(arq)}' enviada para análise...", autor="SISTEMA")
        def task():
            if not hasattr(self, "vision_sys"): self.vision_sys = AuroraVisionSystem()
            if not self.vision_sys.ativo:
                self.log_na_tela("Dando boot no córtex visual GGUF...", autor="SISTEMA")
                self.log_na_tela(self.vision_sys.carregar_modelo(), autor="SISTEMA")
            if not self.vision_sys.ativo: return
            res = self.vision_sys.analisar_imagem(arq, pergunta="Describe this image in detail.")
            if not res or len(res.strip()) < 5: res = self.vision_sys.analisar_imagem(arq, pergunta="What is this?")
            self.log_na_tela(f"[SENSOR VISUAL - LOG BRUTO]:\n{res}", autor="SISTEMA")
            comando_oculto = (f"[DIRETRIZ DE ANÁLISE VISUAL - MODO UNIVERSAL]\nO meu sensor visual extraiu os seguintes detalhes em inglês:\n'''\n{res}\n'''\nAja em Português do Brasil com base neste texto. Se contiver código, audite. Se for geral, traduza e comente intelectualmente.")
            self.orchestrator.submit_job("VisualAnalysis", self.processar_comando_mestre, comando_oculto)
        threading.Thread(target=task, daemon=True).start()

    def acao_analise_forense(self):
        arq = filedialog.askopenfilename(title="Selecionar Imagem para Perícia EXIF", filetypes=(("Imagens", "*.png *.jpg *.jpeg"),))
        if not arq: return
        self.log_na_tela(f"Iniciando perícia digital na imagem '{os.path.basename(arq)}'...", autor="SISTEMA")
        
        def task():
            dados_ocultos = AuroraForensics.extrair_metadados(arq)
            self.log_na_tela(f"[DADOS BRUTOS EXTRAÍDOS]:\n{dados_ocultos}", autor="SISTEMA")
            if not dados_ocultos or str(dados_ocultos).strip() in ["None", "{}", ""]:
                self.log_na_tela("⚠️ [ALERTA FORENSE] Missão Abortada: Nenhum metadado EXIF foi encontrado nesta imagem. Os rastros podem ter sido removidos.", autor="SISTEMA")
                return 
            comando_oculto = (f"[DIRETRIZ DE INVESTIGAÇÃO OSINT]\nExtraí metadados EXIF:\n'''\n{dados_ocultos}\n'''\nAja como Analista Forense e apresente profissionalmente.")
            self.orchestrator.submit_job("EXIFForensics", self.processar_comando_mestre, comando_oculto)
            
        threading.Thread(target=task, daemon=True).start()

    def acao_selecionar_alvo_biometrico(self):
        arq = filedialog.askopenfilename(title="Selecionar Rosto do Alvo", filetypes=(("Imagens", "*.png *.jpg *.jpeg"),))
        if not arq: return
        self.alvo_biometrico = arq 
        self.log_na_tela(f"🎯 ALVO BIOMÉTRICO TRAVADO: '{os.path.basename(arq)}'.", autor="SISTEMA")
        self.falar_e_logar("Rosto alvo cravado na matriz. Aguardando comando de caçada.")

    def acao_blockchain_pentest(self):
        diretriz = "Aurora, assuma o papel de Auditora de Smart Contracts. Gere um script de teste para verificar vulnerabilidades de Reentrancy ou falhas de controle de acesso em um contrato fictício."
        self.log_na_tela("Iniciando Protocolo de Auditoria Blockchain...", autor="SISTEMA")
        self.orchestrator.submit_job("BlockchainPentest", self.processar_comando_mestre, diretriz)

    def acao_ingerir_pdf(self):
        arq = filedialog.askopenfilename(title="Importar Artefato", filetypes=(("Matriz PDF", "*.pdf"),))
        if arq: self.orchestrator.submit_job("RAG_Ingestion", gerenciador_rag.ingerir_arquivo_generico, arq, "geral", "local", lambda m: self.log_na_tela(m, autor="SISTEMA"))

    def acao_limpar_banco(self):
        conn = sqlite3.connect(DB_PATH, timeout=20, check_same_thread=False)
        for t in ["historico", "base_conhecimento_rag", "memoria_contexto_longo"]: conn.cursor().execute(f"DELETE FROM {t}")
        conn.commit()
        conn.close()
        gerenciador_rag.indice_faiss = None
        gerenciador_memoria_longa.indice_faiss = None
        self.log_na_tela("Memória purgada.", autor="SISTEMA")

    def acao_importar_zip(self):
        arq = filedialog.askopenfilename(title="Importar Projeto (ZIP)", filetypes=(("Arquivos ZIP", "*.zip"),))
        if not arq: return
        
        self.log_na_tela(f"Iniciando extração e limpeza tática do arquivo '{os.path.basename(arq)}'...", autor="SISTEMA")
        
        def task_extracao():
            try:
                importer = ProjectImporter()
                resultado = importer.extrair_zip(arq)
                self.log_na_tela(resultado, autor="EXTRATOR ZIP")
                self.falar_e_logar("Projeto importado e limpo com sucesso. Código pronto para auditoria.")
            except Exception as e:
                self.log_na_tela(f"Falha ao extrair ZIP: {e}", autor="SISTEMA")
                
        # Usa o seu próprio Orchestrator para rodar em segundo plano sem travar o painel!
        self.orchestrator.submit_job("ImportZIP", task_extracao)    