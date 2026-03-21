# core/app.py
from config.settings import bootstrap_directories
from memory.sqlite_store import init_db
from ui.gui import AuroraGUI

class AuroraCoreApplication:
    @staticmethod
    def boot():
        print("[SYSTEM] Iniciando Check de Diretórios e File System...")
        bootstrap_directories()
        
        print("[SYSTEM] Iniciando Conexão com SQLite (RAG & Memory)...")
        init_db()
        
        print("[SYSTEM] Levantando Interface Gráfica e Motores GGUF...")
        app = AuroraGUI()
        app.mainloop()