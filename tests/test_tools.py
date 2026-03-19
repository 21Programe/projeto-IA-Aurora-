# tests/test_tools.py
import unittest
from tools.code_executor import sandbox_tester

class TestCodeExecutor(unittest.TestCase):
    def test_sandbox_python_bloqueio(self):
        # Testa se a lista negra está a funcionar
        resultado = sandbox_tester.test_code("import os\nos.remove('ficheiro.txt')", "python")
        self.assertIn("Bloqueado", resultado)

    def test_sandbox_python_seguro(self):
        # Testa se a execução fileless em RAM funciona
        resultado = sandbox_tester.test_code("print('Aurora Segura')", "python")
        self.assertIn("Aurora Segura", resultado)

if __name__ == '__main__':
    unittest.main()