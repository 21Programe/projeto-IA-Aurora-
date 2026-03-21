import os
import sys

# Garante que a raiz do Projeto IA seja a prioridade zero
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Importações Originais da Aurora
from config.settings import bootstrap_directories
from memory.sqlite_store import init_db
from llm.local_llm import iniciar_llm, LocalLLM
from ui.gui import AuroraGUI
from agents.tactical_agent import AuroraTacticalAgent

# Injeção de Ambiente CUDA
cuda_path = r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4\bin'
if os.path.exists(cuda_path):
    os.environ["PATH"] = cuda_path + os.pathsep + os.environ["PATH"]
    print(f"[SYSTEM] Matriz CUDA injetada: {cuda_path}")

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
    app.mainloop()

if __name__ == "__main__":
    boot_sequence()