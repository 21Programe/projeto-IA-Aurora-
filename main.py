import threading
import uvicorn
import os
import sys
import traceback
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Garante que a raiz do Projeto IA seja a prioridade zero
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# ==========================================
# 🕵️ DIAGNÓSTICO DE ARQUIVOS (VERIFICAÇÃO)
# ==========================================
builder_file = os.path.join(BASE_DIR, "api", "builder_routes.py")
if not os.path.exists(builder_file):
    print("\n" + "!"*60)
    print("🚨 ALERTA: ARQUIVO DESAPARECIDO 🚨")
    print(f"O sistema não encontrou o ficheiro onde devia estar:\n-> {builder_file}")
    print("\nComo resolver:")
    print("Verifique se o ficheiro 'builder_routes.py' está fisicamente")
    print("dentro da pasta 'api' na raiz do seu projeto. Ele pode ter")
    print("ficado esquecido dentro da pasta 'src/api' antiga!")
    print("!"*60 + "\n")

# Importações Originais da Aurora
from config.settings import bootstrap_directories
from memory.sqlite_store import init_db
from llm.local_llm import iniciar_llm, LocalLLM 
from ui.gui import AuroraGUI
from agents.tactical_agent import AuroraTacticalAgent

# Importação do Módulo Builder com Revelador de Erros
try:
    from api.builder_routes import router as builder_router
except Exception as e:
    print("\n" + "="*60)
    print("[ERRO REVELADO] O motivo exato da falha na importação:")
    traceback.print_exc()
    print("="*60 + "\n")
    builder_router = None

# Injeção de Ambiente CUDA
cuda_path = r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4\bin' 
if os.path.exists(cuda_path):
    os.environ["PATH"] = cuda_path + os.pathsep + os.environ["PATH"]
    print(f"[SYSTEM] Matriz CUDA injetada: {cuda_path}")

def start_builder_server():
    if builder_router is None:
        print("[AVISO] Servidor Builder desativado devido a erro (veja o log acima).")
        return

    app = FastAPI(title="Aurora Builder Engine")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(builder_router)
    
    print("[SYSTEM] Motor de Construção (Porta 8000) - Online")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")

def boot_sequence():
    threading.Thread(target=start_builder_server, daemon=True).start()

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
    app.mainloop() 

if __name__ == "__main__":
    boot_sequence()