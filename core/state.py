# core/state.py
from dataclasses import dataclass
import threading

@dataclass
class AuroraSystemState:
    is_busy: bool = False
    llm_online: bool = False
    vision_online: bool = False
    stealth_mode_active: bool = False
    current_operation: str = "Aguardando diretrizes táticas."

# Instância global protegida para threads (Thread-safe)
global_state = AuroraSystemState()
state_lock = threading.Lock()

def update_system_state(**kwargs):
    """Atualiza o estado global do sistema de forma segura entre threads."""
    with state_lock:
        for key, value in kwargs.items():
            if hasattr(global_state, key):
                setattr(global_state, key, value)