# agents/autocorrect_loop.py
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class ExecutionAttempt:
    attempt_number: int
    plan: str
    code: str
    success: bool
    stdout: str = ""
    stderr: str = ""
    error_summary: str = ""
    validation_passed: bool = False

@dataclass
class MissionResult:
    mission: str
    success: bool
    final_code: str
    final_output: str
    attempts: List[ExecutionAttempt] = field(default_factory=list)

class AuroraAutoCorrectLoop:
    def __init__(self, llm_callable, sandbox_callable, rag_search_callable=None, max_attempts: int = 5):
        self.llm = llm_callable
        self.sandbox = sandbox_callable
        self.rag_search = rag_search_callable
        self.max_attempts = max_attempts

    def run_mission(self, mission: str, language: str = "python") -> MissionResult:
        attempts: List[ExecutionAttempt] = []
        context = ""
        plan = "1. Escrever o script. 2. Simular dados. 3. Executar."
        previous_error = ""
        current_code = self._extract_code(self.llm([{"role": "user", "content": f"Mude o código se houver erro.\nMissão: {mission}"}]))

        for attempt_number in range(1, self.max_attempts + 1):
            sandbox_result = self.sandbox(language, current_code)
            success = sandbox_result.get("success", False)
            stdout = sandbox_result.get("stdout", "")
            stderr = sandbox_result.get("stderr", "")

            attempt = ExecutionAttempt(attempt_number=attempt_number, plan=plan, code=current_code, success=success, stdout=stdout, stderr=stderr)
            attempts.append(attempt)

            if success:
                return MissionResult(mission=mission, success=True, final_code=current_code, final_output=stdout, attempts=attempts)

            previous_error = stderr
            # Pede para a IA consertar o erro
            prompt_correcao = f"O código falhou!\nMISSÃO: {mission}\nCÓDIGO ATUAL:\n{current_code}\nERRO DO PYTHON:\n{stderr}\nCorrija os erros e me dê apenas o código completo e funcional."
            current_code = self._extract_code(self.llm([{"role": "user", "content": prompt_correcao}]))

        return MissionResult(mission=mission, success=False, final_code=current_code, final_output="Falha após múltiplas tentativas.", attempts=attempts)

    def _extract_code(self, raw: str) -> str:
        raw = raw.strip()
        if raw.startswith("```"):
            lines = raw.splitlines()
            if len(lines) >= 3: return "\n".join(lines[1:-1]).strip()
        return raw