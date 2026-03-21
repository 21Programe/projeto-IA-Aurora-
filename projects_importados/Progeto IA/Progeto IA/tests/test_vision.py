# tests/test_vision.py
import unittest
import os
from unittest.mock import patch
from vision.image_pipeline import AuroraImagePipeline

class TestVisionPipeline(unittest.TestCase):
    def setUp(self):
        """Prepara o terreno: Cria uma imagem temporária (falsa) para testar o conversor Base64."""
        self.test_img = "test_img_temp.jpg"
        with open(self.test_img, "wb") as f:
            f.write(b"matriz_de_pixels_falsa_para_teste_de_visao")

    def tearDown(self):
        """Limpa o terreno: Apaga a imagem temporária após a conclusão do teste."""
        if os.path.exists(self.test_img):
            os.remove(self.test_img)

    # Bloqueamos as chamadas reais para o GGUF para o teste não esgotar a VRAM do sistema
    @patch('llm.vision_llm.VisionLLMInterface.inicializar_motor')
    @patch('llm.vision_llm.VisionLLMInterface.inferir_imagem')
    def test_preparar_e_analisar(self, mock_inferir, mock_inicializar):
        """Testa se o pipeline consegue converter a imagem e interagir com o modelo."""
        
        # Configura as respostas falsas do modelo simulado
        mock_inicializar.return_value = "Visão Computacional Online."
        mock_inferir.return_value = "This is a simulated description of the image."

        # Instancia o pipeline visual
        pipeline = AuroraImagePipeline()
        
        # Força o status como ativo para simular um boot bem-sucedido do LLM de visão
        pipeline.motor_visao.ativo = True 
        
        # Executa a análise tática
        resultado = pipeline.preparar_e_analisar(self.test_img, "What is this?")
        
        # Validações de Segurança e Lógica
        self.assertEqual(resultado, "This is a simulated description of the image.")
        mock_inferir.assert_called_once() # Garante que o motor de inferência foi chamado exatamente uma vez

if __name__ == '__main__':
    unittest.main()