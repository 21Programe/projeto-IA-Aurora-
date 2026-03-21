import os
import sys
import threading
import time

# 1. Garante que a raiz do Projeto IA seja a prioridade zero ANTES de importar módulos locais
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# 2. Importações Originais da Aurora
from config.settings import bootstrap_directories
from memory.sqlite_store import init_db
from llm.local_llm import iniciar_llm, LocalLLM
from ui.gui import AuroraGUI
from agents.tactical_agent import AuroraTacticalAgent

# 3. Importações do Novo Módulo de Segurança
from seguranca.visao_protetora import rotina_visao_protetora
from seguranca.cao_de_guarda import rotina_de_seguranca_invisivel
from seguranca.barramento_eventos import fila_alertas
from seguranca.defesa_ativa import iniciar_defesa
from seguranca.mensageiro_telegram import enviar_alerta_telegram
from seguranca.quarentena_edge import rotina_quarentena_web # NOVO: Importação da Quarentena

# Injeção de Ambiente CUDA
cuda_path = r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4\bin'
if os.path.exists(cuda_path):
    os.environ["PATH"] = cuda_path + os.pathsep + os.environ["PATH"]
    print(f"[SYSTEM] Matriz CUDA injetada: {cuda_path}")

def central_de_controle_seguranca():
    """Esta função lê os alertas do Cão de Guarda na velocidade da luz"""
    while True:
        alerta = fila_alertas.get() 
        
        print(f"\n[A U R O R A  C E N T R A L] 🚨 AMEAÇA RECEBIDA DA FILA!")
        print(f"-> Ameaça: {alerta['mensagem']}")
        
        # 1. Dispara o alerta blindado para o seu Telegram!
        enviar_alerta_telegram(alerta)
        
        # 2. Inicia a interface nativa do Windows para o Contra-Ataque/Defesa!
        iniciar_defesa(alerta)
        
        fila_alertas.task_done()

def boot_sequence():
    print("[SYSTEM] Iniciando Check de Diretórios...")
    bootstrap_directories()
    init_db()
    iniciar_llm()

    llm_core = LocalLLM()
    app = AuroraGUI()

    aurora_engine = AuroraTacticalAgent(
        llm_func=llm_core,
        orchestrator=app.orchestrator
    )

    app.agent = aurora_engine
    print("[SYSTEM] Aurora V2.5 Totalmente Operacional.")

    # --- INÍCIO DA ARQUITETURA DE SEGURANÇA ---
    
    # 1. Liga o Cão de Guarda (Vigia o Windows silenciosamente)
    thread_antivirus = threading.Thread(target=rotina_de_seguranca_invisivel)
    thread_antivirus.daemon = True 
    thread_antivirus.start()

    # 2. Liga a Recepção (Lê a Fila e dispara a janela de Defesa)
    thread_recepcao = threading.Thread(target=central_de_controle_seguranca)
    thread_recepcao.daemon = True
    thread_recepcao.start()
    
    # 3. Liga a Visão Computacional (Os Olhos da Aurora)
    thread_visao = threading.Thread(target=rotina_visao_protetora)
    thread_visao.daemon = True
    thread_visao.start()
    print("🔥 [SYSTEM] Sensores Visuais Online!")
    
    # 4. Liga a Quarentena de Downloads do Edge (NOVO)
    thread_quarentena = threading.Thread(target=rotina_quarentena_web)
    thread_quarentena.daemon = True
    thread_quarentena.start()
    
    print("🔥 [SYSTEM] Sistema Nervoso de Segurança Online e Operante!")
    # --- FIM DA ARQUITETURA DE SEGURANÇA ---

    # Inicia a interface gráfica da Aurora
    app.mainloop()

if __name__ == "__main__":
    boot_sequence()