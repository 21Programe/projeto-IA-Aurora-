# agents/memory_agent.py

class MemoryAgent:
    def __init__(self, rag_engine, contextual_memory):
        self.rag_engine = rag_engine
        self.contextual_memory = contextual_memory

    def run(self, query: str) -> dict:
        try:
            rag_context = self.rag_engine.buscar(query)
        except Exception:
            rag_context = ""

        try:
            recent_context = self.contextual_memory.get_context(query)
        except Exception:
            recent_context = ""

        return {
            "ok": True,
            "type": "memory",
            "content": {
                "rag": rag_context,
                "recent": recent_context
            }
        }