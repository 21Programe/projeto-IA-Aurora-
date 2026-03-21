# core/orchestrator.py
import concurrent.futures
import threading
from datetime import datetime

class RedTeamTaskOrchestrator:
    def __init__(self, message_queue=None, max_workers=10):
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.message_queue = message_queue
        
        # Estruturas necessárias para a GUI e o Sentinela
        self.active_jobs = {}
        self.job_counter = 0
        self.lock = threading.Lock()
        
        # Esses agentes serão injetados depois, mas o orquestrador os prevê
        self.memory_agent = None
        self.research_agent = None
        self.executor_agent = None
        self.safety_agent = None
        self.tactical_agent = None

    def log_status(self, msg):
        if self.message_queue:
            self.message_queue.put(("SYSTEM", f"[ORCHESTRATOR] {msg}"))
        print(f"[ORCHESTRATOR] {msg}")

    def submit_job(self, job_name, fn, *args, **kwargs):
        """
        Método exigido pela GUI. Registra a tarefa e a envia para a thread em background.
        """
        with self.lock:
            self.job_counter += 1
            job_id = f"PID_{self.job_counter:04X}"

            self.active_jobs[job_id] = {
                "name": job_name,
                "future": None,
                "status": "RUNNING",
                "created_at": datetime.now().isoformat(),
                "finished_at": None,
                "result": None,
                "error": None,
            }

        future = self.executor.submit(
            self._execution_wrapper,
            job_id,
            job_name,
            fn,
            *args,
            **kwargs
        )

        with self.lock:
            self.active_jobs[job_id]["future"] = future

        return job_id

    def _execution_wrapper(self, job_id, job_name, fn, *args, **kwargs):
        """Monitora e executa o job (exigido pelo Sentinela)."""
        try:
            res = fn(*args, **kwargs)
            with self.lock:
                self.active_jobs[job_id]["status"] = "COMPLETED"
                self.active_jobs[job_id]["finished_at"] = datetime.now().isoformat()
                self.active_jobs[job_id]["result"] = res
            return res
        except Exception as e:
            with self.lock:
                self.active_jobs[job_id]["status"] = "FAILED"
                self.active_jobs[job_id]["finished_at"] = datetime.now().isoformat()
                self.active_jobs[job_id]["error"] = str(e)
            self.log_status(f"FALHA NO JOB {job_id} ({job_name}): {e}")
            raise e

    def process(self, user_input: str) -> str:
        """
        Processamento síncrono da inteligência da Aurora (chamado pelo TacticalAgent).
        """
        # Se houver agente tático injetado, ele assume
        if self.tactical_agent:
            return self.tactical_agent.responder(user_input)
            
        return "Aurora Core Online, mas Módulo Tático não encontrado."