# agents/safety_agent.py

class SafetyAgent:
    def run(self, task: str) -> dict:
        blocked_terms = [
            "apagar system32",
            "formatar disco",
            "desativar antivirus",
            "roubar senha"
        ]

        lowered = task.lower()
        for term in blocked_terms:
            if term in lowered:
                return {
                    "ok": False,
                    "type": "safety",
                    "blocked": True,
                    "reason": f"Comando bloqueado por segurança: {term}"
                }

        return {
            "ok": True,
            "type": "safety",
            "blocked": False,
            "reason": "Tarefa liberada"
        }