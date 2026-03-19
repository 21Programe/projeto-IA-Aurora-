# agents/research_agent.py

class ResearchAgent:
    def __init__(self, web_search_tool, file_reader_tool=None):
        self.web_search_tool = web_search_tool
        self.file_reader_tool = file_reader_tool

    def run(self, query: str) -> dict:
        try:
            result = self.web_search_tool.buscar(query)
            return {"ok": True, "type": "research", "content": result}
        except Exception as e:
            return {"ok": False, "type": "research", "error": str(e)}