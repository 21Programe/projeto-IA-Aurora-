# agents/executor_agent.py

class ExecutorAgent:
    def __init__(self, autocorrect_loop, code_executor=None):
        self.code_executor = code_executor
        self.autocorrect_loop = autocorrect_loop

    def run(self, task: str) -> dict:
        try:
            # CORREÇÃO AQUI: Mudado de processar() para run_mission()
            result = self.autocorrect_loop.run_mission(task)
            return {"ok": result.success, "type": "execution", "content": result.final_output}
        except Exception as e:
            return {"ok": False, "type": "execution", "error": str(e)}