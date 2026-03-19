# tests/test_autocorrect.py
import unittest
from agents.autocorrect_loop import AuroraAutoCorrectLoop

class TestAutoCorrectLoop(unittest.TestCase):
    def test_auto_cura_sucesso(self):
        # 1. Simula o "Cérebro" (LLM) da Aurora
        respostas_llm = [
            "```python\nprint('Falta fechar aspas)\n```",  # Erro proposital
            "```python\nprint('Corrigido!')\n```"           # Consertado
        ]
        
        def mock_llm(mensagens):
            return respostas_llm.pop(0) if respostas_llm else ""

        # 2. Simula o "Sandbox" executando o código
        def mock_sandbox(linguagem, codigo):
            if "Falta fechar aspas" in codigo:
                return {"success": False, "stdout": "", "stderr": "SyntaxError: EOL while scanning string literal"}
            return {"success": True, "stdout": "Corrigido!\n", "stderr": ""}

        # 3. Inicializa o motor com os simuladores
        motor = AuroraAutoCorrectLoop(llm_callable=mock_llm, sandbox_callable=mock_sandbox, max_attempts=3)
        
        # 4. Executa a missão
        resultado = motor.run_mission("Escreva um print na tela")

        # 5. Validações
        self.assertTrue(resultado.success, "O motor falhou em consertar o código.")
        self.assertIn("Corrigido", resultado.final_output, "A saída final não corresponde ao código corrigido.")

if __name__ == '__main__':
    unittest.main()