# vision/image_pipeline.py
import base64
from llm.vision_llm import VisionLLMInterface

class AuroraImagePipeline:
    def __init__(self):
        self.motor_visao = VisionLLMInterface()

    def preparar_e_analisar(self, caminho_imagem, pergunta="Describe the image in detail."):
        try:
            # 1. Tenta arrancar o motor se estiver offline
            if not self.motor_visao.ativo:
                self.motor_visao.inicializar_motor()

            # 2. Conversão da imagem para Base64 (Protocolo Llava)
            with open(caminho_imagem, "rb") as image_file:
                imagem_b64 = base64.b64encode(image_file.read()).decode('utf-8')
            
            url_data = f"data:image/jpeg;base64,{imagem_b64}"

            # 3. Inferência
            return self.motor_visao.inferir_imagem(url_data, pergunta)
            
        except Exception as e:
            return f"Falha no pipeline visual: {e}"