import threading

from agents.tactical_agent import AuroraTacticalAgent
from config.settings import bootstrap_directories
from llm.local_llm import LocalLLM, iniciar_llm
from memory.sqlite_store import init_db
from seguranca.barramento_eventos import fila_alertas
from seguranca.cao_de_guarda import rotina_de_seguranca_invisivel
from seguranca.defesa_ativa import iniciar_defesa
from seguranca.mensageiro_telegram import enviar_alerta_telegram
from seguranca.quarentena_edge import rotina_quarentena_web
from seguranca.visao_protetora import rotina_visao_protetora
from ui.gui import AuroraGUI


def central_de_controle_seguranca():
    """Processa alertas da fila central de eventos de segurança."""
    while True:
        alerta = fila_alertas.get()
        try:
            print("\n[AURORA CENTRAL] Alerta recebido.")
            print(f"-> {alerta.get('mensagem', 'Evento sem descrição')}")
            enviar_alerta_telegram(alerta)
            iniciar_defesa(alerta)
        finally:
            fila_alertas.task_done()


def iniciar_thread(target, nome):
    thread = threading.Thread(target=target, name=nome, daemon=True)
    thread.start()
    return thread


def boot_sequence():
    print("[SYSTEM] Iniciando Aurora AI...")
    bootstrap_directories()
    init_db()
    iniciar_llm()

    llm_core = LocalLLM()
    app = AuroraGUI()

    app.agent = AuroraTacticalAgent(
        llm_func=llm_core,
        orchestrator=app.orchestrator,
    )

    print("[SYSTEM] Núcleo Aurora inicializado.")

    iniciar_thread(rotina_de_seguranca_invisivel, "aurora-watchdog")
    iniciar_thread(central_de_controle_seguranca, "aurora-alert-router")
    iniciar_thread(rotina_visao_protetora, "aurora-vision")
    iniciar_thread(rotina_quarentena_web, "aurora-quarantine")

    print("[SYSTEM] Sensores e componentes de segurança iniciados.")
    app.mainloop()


if __name__ == "__main__":
    boot_sequence()
