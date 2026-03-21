# llm/local_llm.py
import os
import hashlib
import psutil
from llama_cpp import Llama
from config.settings import CAMINHO_MODELO_LLM
from memory.rag_engine import gerenciador_rag

# IMPORTAÇÃO DA FERRAMENTA DE RED TEAM
from tools.github_ingestor import extrair_repositorio

# --- INJEÇÃO DE CAMINHO CUDA (Para sua RTX 2060) ---
cuda_bin = r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4\bin'
if os.path.exists(cuda_bin):
    os.environ["PATH"] = cuda_bin + os.pathsep + os.environ["PATH"]

cerebro_llm = None
modelo_carregado = False

def iniciar_llm():
    global cerebro_llm, modelo_carregado
    try:
        if os.path.exists(CAMINHO_MODELO_LLM) and cerebro_llm is None:
            cores_fisicos = psutil.cpu_count(logical=False) or 4
            print(f"[LLM] Inicializando Matriz Neural na GPU...")
            
            cerebro_llm = Llama(
                model_path=CAMINHO_MODELO_LLM,
                n_gpu_layers=-1,   
                n_threads=cores_fisicos,
                n_ctx=8192,       
                n_batch=512,
                embedding=False,  # <--- MUDANÇA CRÍTICA: Desliga o conflito de vetores
                chat_format="chatml", 
                verbose=False      
            )
            modelo_carregado = True
            print("[LLM CORE] Sistema operando com aceleração CUDA.")
    except Exception as e:
        print(f"[ERRO CRÍTICO] Falha no hardware: {e}")
        
    return cerebro_llm

class LocalLLM:
    def __init__(self):
        self.instancia = iniciar_llm()
        self.cache_respostas = {} 

    def gerar_resposta(self, prompt):
        mensagens = [{"role": "user", "content": prompt}]
        return self.__call__(mensagens)

    def __call__(self, prompt_contexto):
        if not self.instancia: return "Cérebro offline."
        
        try:
            pergunta_usuario = prompt_contexto[-1]['content'].strip()
            
           # --- 🛑 GATILHO DE FERRAMENTA: INGESTÃO DE GITHUB ---
            if pergunta_usuario.lower().startswith("clonar "):
                partes = pergunta_usuario.split()
                if len(partes) > 1:
                    link = partes[1]
                    print("[SISTEMA] Interceptando comando tático. Acionando Git...")
                    resultado_git = extrair_repositorio(link)
                    
                    # Se o download foi bem-sucedido ou já existia, injeta no cérebro!
                    nome_repo = link.split("/")[-1].replace(".git", "")
                    caminho_baixado = os.path.join(os.getcwd(), "projects_importados", nome_repo)
                    
                    if os.path.exists(caminho_baixado):
                        # CHAMA A NOSSA NOVA FUNÇÃO DO RAG!
                        chunks, msg = gerenciador_rag.ingerir_diretorio_codigo(caminho_baixado)
                        return f"[OPERAÇÃO CONCLUÍDA] Repositório clonado. {msg}"
                    else:
                        return f"[OPERAÇÃO CONCLUÍDA] {resultado_git}"
                        
                else:
                    return "[ERRO] Forneça o link. Ex: clonar https://github.com/..."
            # -----------------------------------------------------
            # -----------------------------------------------------

            # --- 🛡️ SISTEMA DE CACHE ---
            hash_pergunta = hashlib.md5(pergunta_usuario.encode('utf-8')).hexdigest()
            if hash_pergunta in self.cache_respostas:
                print(f"[CACHE] Resposta recuperada da memória! Uso de GPU: 0%")
                return self.cache_respostas[hash_pergunta]
            
            
            
       # --- 🧠 BUSCA RAG NOS CHUNKS ---
            # Aumentamos para 15 blocos para ela poder ler mais código!
            contexto_rag = gerenciador_rag.recuperar_contexto(pergunta_usuario, limiar_top_k=15)
            
            # --- PAINEL DE DEBUG FORENSE ---
            print("\n" + "!"*60)
            print("[RAIO-X RAG] O QUE A AURORA ESTÁ LENDO DO BANCO DE DADOS:")
            if not contexto_rag:
                print(">>> O RAG ESTÁ VAZIO! A memória não foi carregada ou nada foi encontrado.")
            else:
                # Imprime os primeiros 1500 caracteres para não poluir a tela inteira
                print(contexto_rag[:1500])
                print("... [CORTADO PARA EXIBIÇÃO] ...")
            print("!"*60 + "\n")
            # -------------------------------

            # --- 🎯 PROMPT DE CONTROLE TÁTICO ---
            instrucao_mestra = f"""Você é a Aurora IA, especialista sênior em Cyber Security e Engenharia Reversa Criada por Diego.
            
            SUA MISSÃO: Analise os fragmentos de código abaixo extraídos da sua memória vetorial. 
            Tente deduzir a lógica do script baseando-se nas variáveis e funções apresentadas.
            Responda de forma direta e técnica. Se não souber, diga "Dados insuficientes".

            CLUSTERS DE MEMÓRIA (DADOS BRUTOS DO GITHUB):
            {contexto_rag}
            """

            mensagens_limpas = [
                {"role": "system", "content": instrucao_mestra},
                {"role": "user", "content": pergunta_usuario}
            ]

            print(f"[RAG] Injetando contexto tático na RTX 2060...")

            # --- ⚡ GERAÇÃO ---
            res = self.instancia.create_chat_completion(
                messages=mensagens_limpas, 
                temperature=0.0, 
                max_tokens=2048
            )
            
            resposta_final = res['choices'][0]['message']['content']
            
            # SALVA NO CACHE
            self.cache_respostas[hash_pergunta] = resposta_final
            
            return resposta_final

        except Exception as e: 
            return f"Erro na síntese tática: {e}"

consultar_ia_local = LocalLLM()