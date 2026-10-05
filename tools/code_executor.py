"""Ferramenta segura de análise de código da Aurora.

Por padrão, este módulo NÃO executa código fornecido pelo usuário/modelo.
Ele realiza somente inspeção estática e retorna achados básicos.
Execução arbitrária não deve ser tratada como sandbox apenas por blacklist.
"""

import ast
import re


class CodeInjectionTester:
    """Analisa snippets sem executá-los."""

    def test_code(self, code_str, language="python"):
        if not isinstance(code_str, str):
            return "❌ Entrada inválida: o código precisa ser texto."

        language = language.lower().strip()

        if language == "python":
            return self._analisar_python(code_str)
        if language in {"javascript", "shell", "sql"}:
            return self._analisar_generico(code_str, language)

        return "❌ Linguagem não suportada."

    def _analisar_python(self, code_str):
        try:
            tree = ast.parse(code_str)
        except SyntaxError as exc:
            return f"❌ Sintaxe Python inválida: {exc}"

        achados = []
        chamadas_sensiveis = {
            "exec", "eval", "compile", "__import__",
            "system", "popen", "run", "Popen", "check_output",
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                nome = self._nome_chamada(node.func)
                if nome in chamadas_sensiveis:
                    achados.append(f"chamada sensível: {nome}")

            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in {"subprocess", "ctypes"}:
                        achados.append(f"import sensível: {alias.name}")

            if isinstance(node, ast.ImportFrom) and node.module in {"subprocess", "ctypes"}:
                achados.append(f"import sensível: {node.module}")

        if not achados:
            return "✅ Análise estática concluída: nenhum padrão sensível básico encontrado."

        return "⚠️ Análise estática — revisar antes de executar:\n- " + "\n- ".join(sorted(set(achados)))

    @staticmethod
    def _nome_chamada(node):
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return "<dinâmica>"

    def _analisar_generico(self, code_str, language):
        padroes = {
            "javascript": [r"\b(eval|Function)\s*\(", r"child_process", r"process\.exit"],
            "shell": [r"(^|\s)(rm\s+-rf|shutdown|format|del\s+/s)(\s|$)"],
            "sql": [r"\b(DROP|TRUNCATE|ALTER)\b"],
        }

        encontrados = []
        for pattern in padroes[language]:
            if re.search(pattern, code_str, flags=re.IGNORECASE):
                encontrados.append(pattern)

        if not encontrados:
            return f"✅ Análise estática {language} concluída."

        return (
            f"⚠️ Análise estática {language}: "
            "foram encontrados padrões que exigem revisão manual."
        )


sandbox_tester = CodeInjectionTester()
