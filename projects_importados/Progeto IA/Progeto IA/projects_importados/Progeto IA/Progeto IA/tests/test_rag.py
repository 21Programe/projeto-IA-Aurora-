# tests/test_rag.py
import unittest
from memory.chunking import DocumentChunker

class TestMemoryChunking(unittest.TestCase):
    def test_quebra_de_texto(self):
        texto_longo = "A " * 2000
        chunks = DocumentChunker.quebrar_em_chunks(texto_longo, tamanho=900, sobreposicao=100)
        self.assertTrue(len(chunks) > 1, "O fragmentador falhou ao dividir um texto grande.")

if __name__ == '__main__':
    unittest.main()