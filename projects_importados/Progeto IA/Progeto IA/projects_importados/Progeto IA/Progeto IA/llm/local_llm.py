# llm/local_llm.py
import os
import psutil
from llama_cpp import Llama
from config.settings import CAMINHO_MODELO_LLM
# IMPORTAÇÃO CRÍTICA: Conecta o LLM aos 2531 chunks de memória
from memory.rag_engine import gerenciador_rag

# --- INJEÇÃO DE CAMINHO CUDA (Para sua RTX 2060) ---
cuda_bin = r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4\bin'
if os.path.exists(cuda_bin):
    os.environ["PATH"] = cuda_bin + os.pathsep + os.environ["PATH"]

cerebro_llm = None
modelo_carregado = False

def iniciar_llm():
    global cerebro_llm, modelo_carregado
    try:
        # Só inicializa se ainda não estiver na memória
        if os.path.exists(CAMINHO_MODELO_LLM) and cerebro_llm is None:
            cores_fisicos = psutil.cpu_count(logical=False) or 4
            
            print(f"[LLM] Inicializando Matriz Neural na GPU...")
            
            cerebro_llm = Llama(
                model_path=CAMINHO_MODELO_LLM,
                n_gpu_layers=15,   # RTX 2060
                n_threads=cores_fisicos,
                n_ctx=2048,       # Contexto otimizado
                n_batch=512,
                embedding=True,
                chat_format="llama-3",
                verbose=True       
            )
            modelo_carregado = True
            print("[LLM CORE] Sistema operando com aceleração CUDA.")
    except Exception as e:
        print(f"[ERRO CRÍTICO] Falha no hardware: {e}")
        
    return cerebro_llm

# --- A CLASSE QUE FALTAVA PARA O MAIN.PY FUNCIONAR ---
class LocalLLM:
    def __init__(self):
        # Garante que a matriz de tensores está ativa
        self.instancia = iniciar_llm()

    def gerar_resposta(self, prompt):
        """Interface simples para textos diretos"""
        mensagens = [{"role": "user", "content": prompt}]
        return self.__call__(mensagens)

    def __call__(self, prompt_contexto):
        """A sua lógica tática original, agora blindada dentro da classe"""
        if not self.instancia: return "Cérebro offline."
        
        try:
            # 1. Pega APENAS a pergunta final do Diego (compatível com a GUI)
            pergunta_usuario = prompt_contexto[-1]['content']
            
          # 2. Busca aprimorada: Traz 15 blocos do FAISS para a IA ler!
            contexto_rag = gerenciador_rag.recuperar_contexto(pergunta_usuario, limiar_top_k=15) 
            
            # 3. PROMPT DE CONTROLE TÁTICO (Foco total em Pentest do seu código)
            instrucao_mestra = f"""VOCÊ É A AURORA IA. Seu núcleo de Coder foi desativado.
            ESTADO ATUAL: Modo Analista de Cyber Security e Pentest.
            
            INSTRUÇÃO: Use APENAS os dados técnicos abaixo para extrair o que o usuário pediu. 
            Se houver comandos de terminal (Aircrack, aireplay, etc), priorize-os. 
            NÃO fale sobre lógica, matemática ou algoritmos de busca.

            CLUSTERS DE MEMÓRIA (DADOS BRUTOS):
            {contexto_rag if contexto_rag else "Use sua base de dados interna de ferramentas Kali Linux."}
            """

            # Recriando o pacote de mensagens sem o "lixo" anterior
            mensagens_limpas = [
                {"role": "system", "content": instrucao_mestra},
                {"role": "user", "content": pergunta_usuario}
            ]

            print(f"[RAG] Injetando contexto tático na RTX 2060...")

            # 4. GERAÇÃO (Temperatura zero para não alucinar)
            res = self.instancia.create_chat_completion(
                messages=mensagens_limpas, 
                temperature=0.0, # Zero absoluto: a IA vira um robô de busca
                max_tokens=600
            )
            return res['choices'][0]['message']['content']

        except Exception as e: 
            return f"Erro na síntese tática: {e}"

# Mantido para retrocompatibilidade caso outro arquivo ainda chame assim
consultar_ia_local = LocalLLM()