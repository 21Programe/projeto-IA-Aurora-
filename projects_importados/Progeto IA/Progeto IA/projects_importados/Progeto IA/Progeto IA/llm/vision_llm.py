# llm/vision_llm.py
import os
from llama_cpp import Llama
from llama_cpp.llama_chat_format import Llava15ChatHandler
from config.settings import CAMINHO_MODELO_VISAO, CAMINHO_PROJETOR_VISAO

class VisionLLMInterface:
    def __init__(self):
        self.caminho_modelo = CAMINHO_MODELO_VISAO
        self.caminho_projetor = CAMINHO_PROJETOR_VISAO
        self.modelo = None
        self.ativo = False

    def inicializar_motor(self):
        if self.ativo:
            return "Motor visual já se encontra online."
        
        if not os.path.exists(self.caminho_modelo) or not os.path.exists(self.caminho_projetor):
            raise FileNotFoundError(f"Ficheiros GGUF de visão ausentes em: {os.path.dirname(self.caminho_modelo)}")

        try:
            chat_handler = Llava15ChatHandler(clip_model_path=self.caminho_projetor, verbose=False)
            self.modelo = Llama(
                model_path=self.caminho_modelo,
                chat_handler=chat_handler,
                n_ctx=2048, 
                n_gpu_layers=0, # Mantido na CPU para não sobrecarregar a VRAM da RTX 2060
                verbose=False
            )
            self.ativo = True
            return "Visão Computacional Online. Protocolo GGUF ativado."
        except Exception as e:
            self.ativo = False
            raise Exception(f"Erro ao carregar projeção visual: {e}")

    def inferir_imagem(self, url_data, pergunta):
        if not self.ativo or self.modelo is None:
            raise RuntimeError("O motor de visão não foi inicializado.")

        mensagens = [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": url_data}},
                    {"type": "text", "text": pergunta}
                ]
            }
        ]

        resposta = self.modelo.create_chat_completion(
            messages=mensagens,
            max_tokens=1024,  
            temperature=0.3   
        )
        return resposta["choices"][0]["message"]["content"].strip()