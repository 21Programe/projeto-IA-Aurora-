# vision/image_analyzer.py
import os
import base64
from llama_cpp import Llama
from llama_cpp.llama_chat_format import Llava15ChatHandler
from config.settings import CAMINHO_MODELO_VISAO, CAMINHO_PROJETOR_VISAO

class AuroraVisionSystem:
    def __init__(self):
        self.caminho_modelo = CAMINHO_MODELO_VISAO
        self.caminho_projetor = CAMINHO_PROJETOR_VISAO
        self.llm_vision = None
        self.ativo = False

    def carregar_modelo(self):
        if self.ativo: return "Sistema visual já está online."
        
        if not os.path.exists(self.caminho_modelo) or not os.path.exists(self.caminho_projetor):
            return f"Arquivos GGUF ausentes. Verifique a pasta {os.path.dirname(self.caminho_modelo)}."

        try:
            chat_handler = Llava15ChatHandler(clip_model_path=self.caminho_projetor, verbose=False)
            self.llm_vision = Llama(
                model_path=self.caminho_modelo,
                chat_handler=chat_handler,
                n_ctx=2048, 
                n_gpu_layers=0, # Mantido na CPU para não competir com o Qwen na RTX 2060
                verbose=False
            )
            self.ativo = True
            return "Visão Computacional Online. Protocolo GGUF ativado com sucesso."
        except Exception as e:
            return f"Erro ao carregar Olhos (GGUF): {str(e)}"

    def analisar_imagem(self, caminho_imagem, pergunta="Describe the image in detail."):
        if not self.ativo or self.llm_vision is None: 
            return "Sistema de visão offline ou não inicializado corretamente."

        try:
            with open(caminho_imagem, "rb") as image_file:
                imagem_b64 = base64.b64encode(image_file.read()).decode('utf-8')
            
            url_data = f"data:image/jpeg;base64,{imagem_b64}"

            mensagens = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": url_data}},
                        {"type": "text", "text": pergunta}
                    ]
                }
            ]

            resposta = self.llm_vision.create_chat_completion(
                messages=mensagens,
                max_tokens=1024,  
                temperature=0.3   
            )
            return resposta["choices"][0]["message"]["content"].strip()
            
        except Exception as e:
            return f"Erro na análise visual (GGUF): {e}"