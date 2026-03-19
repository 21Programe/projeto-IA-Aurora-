# agents/planner_agent.py

class PlannerAgent:
    def __init__(self, llm=None):
        self.llm = llm

    def plan(self, user_input: str) -> dict:
        text = user_input.lower()

        # Gatilhos para Pesquisa (RAG ou Web)
        use_research = any(k in text for k in ["pesquise", "busque", "procure", "internet", "quem é", "o que é"])
        
        # Gatilhos para Execução de Código/Scripts
        use_code = any(k in text for k in ["crie código", "corrija código", "execute", "script", "python", "bash", "terminal"])
        
        # Gatilhos para Memória e Contexto do Projeto
        use_memory = any(k in text for k in ["lembra", "memória", "contexto", "continuar", "projeto aurora", "histórico"])
        
        # Gatilhos de Segurança (Auditoria de Comandos)
        use_safety = any(k in text for k in ["segurança", "falha", "vulnerabilidade", "auditoria", "ataque", "invadir"])

        return {
            "use_research": use_research,
            "use_code": use_code,
            "use_memory": use_memory,
            "use_safety": use_safety,
            "goal": user_input
        }
    