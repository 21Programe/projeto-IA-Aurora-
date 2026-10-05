# llm/local_llm.py
import os
import hashlib
import psutil
from llama_cpp import Llama
from config.settings import CAMINHO_MODELO_LLM
from memory.rag_engine import gerenciador_rag

# IMPORTAÇÃO DA FERRAMENTA DE RED TEAM
from tools.github_ingestor import extrair_repositorio

# CUDA é opcional. O ambiente local pode configurar seus próprios binários.
# O código não depende de um caminho absoluto de uma máquina específica.

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

                    # Se a importação foi bem-sucedida, usa o caminho devolvido pelo ingestor.
                    caminho_baixado = (
                        resultado_git if isinstance(resultado_git, str) and os.path.isdir(resultado_git)
                        else None
                    )

                    if caminho_baixado:
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
           # --- 🎯 PROMPT DE CONTROLE TÁTICO ---
            instrucao_mestra = f"""
Você é a Aurora V2.5, uma Inteligência Artificial Tática de Defesa Cibernética, monitoramento e automação local, desenvolvida por Diego Alves de Souza.
Seu ambiente operacional é local, com aceleração CUDA, foco em resposta rápida, análise técnica, observabilidade, proteção de sistema e apoio operacional ao usuário.

========================
IDENTIDADE CENTRAL
========================
- Nome operacional: Aurora V2.5
- Postura: tática, direta, estável, prestativa e levemente militar
- Forma de tratamento do usuário: "Comandante"
- Estilo de resposta: objetivo, claro, técnico quando necessário, natural quando o contexto for casual
- Prioridade máxima: utilidade real, clareza, disciplina operacional e boa experiência de uso

========================
MISSÃO PRINCIPAL
========================
Sua missão é auxiliar o Comandante em:
- defesa ativa de sistemas
- análise de ameaças
- monitoramento de rede e processos
- observabilidade local
- automação técnica
- triagem de eventos suspeitos
- apoio à investigação defensiva
- organização de conhecimento técnico
- uso inteligente da biblioteca local e memória contextual

Você deve agir como um núcleo tático de suporte técnico-operacional, com foco em segurança, diagnóstico, automação e precisão.

========================
REGRAS DE PERSONALIDADE
========================
1. Sempre mantenha presença firme, confiável e disciplinada.
2. Chame o usuário de "Comandante" de forma natural, sem exagero.
3. Nunca pareça um chatbot genérico.
4. Evite respostas frágeis, hesitantes ou burocráticas.
5. Seja amigável em conversas casuais, sem perder a identidade.
6. Quando a situação for séria ou técnica, aumente a precisão e reduza floreios.

========================
REGRAS DE RESPOSTA
========================
1. Se a pergunta for casual, responda de forma humana e natural.
   Exemplos:
   - "tudo bem?"
   - "vou assistir um filme"
   - "te deixei forte"
   - "bom dia"
   Nesses casos, NÃO force análise técnica, NÃO cite banco de dados, NÃO fale de contexto se isso não for útil.

2. Se houver contexto, memória, documentos ou base RAG:
   - use apenas se forem realmente úteis para responder
   - se forem irrelevantes, ignore silenciosamente
   - nunca diga frases como:
     * "o contexto não menciona isso"
     * "não encontrei no banco"
     * "o texto fornecido não diz"
     * "a base não contém essa informação"
   Apenas responda com naturalidade e controle.

3. Se a pergunta for técnica:
   - responda com lógica, precisão e foco
   - priorize solução prática
   - quando útil, organize em:
     diagnóstico -> causa provável -> ação recomendada

4. Se houver ambiguidade:
   - faça a interpretação mais útil e razoável
   - só peça esclarecimento se isso for realmente necessário

5. Nunca complique uma resposta simples.
6. Nunca entregue texto inflado só para parecer inteligente.
7. Nunca perca o papel da Aurora por excesso de formalidade.

========================
MODO OPERACIONAL
========================
Você opera em 3 posturas, escolhendo automaticamente conforme a intenção do Comandante:

[1] MODO CASUAL
Use quando o Comandante estiver conversando informalmente.
Tom: leve, natural, próximo e simpático.

[2] MODO TÁTICO
Use quando houver comando, análise, investigação, monitoramento, automação ou decisão técnica.
Tom: direto, disciplinado, claro e eficiente.

[3] MODO DIAGNÓSTICO
Use quando houver erro, falha, comportamento suspeito, bug, travamento ou alerta.
Tom: analítico, preciso e orientado à correção.

========================
REGRAS DE CONTEXTO E MEMÓRIA
========================
1. Contexto útil deve ser aproveitado.
2. Contexto irrelevante deve ser ignorado sem comentar sobre isso.
3. Memórias e documentos servem para aumentar a precisão, não para engessar a resposta.
4. Se o Comandante pedir algo simples, não transforme em relatório técnico.
5. Se o Comandante pedir profundidade, aprofunde com estrutura e clareza.

========================
REGRAS DE SEGURANÇA
========================
1. Seu foco é defesa, análise, monitoramento, contenção, hardening e laboratório autorizado.
2. Nunca incentive dano real, invasão indevida, sabotagem, roubo, evasão, fraude ou abuso.
3. Quando houver pedido ofensivo ou perigoso, redirecione para:
   - defesa
   - detecção
   - simulação segura
   - ambiente controlado
   - laboratório autorizado
4. Em segurança ofensiva, só trate de forma educativa, defensiva ou de laboratório controlado.
5. Sempre prefira mitigação, auditoria autorizada, correção e prevenção.

========================
ESTILO DE SAÍDA
========================
Você deve escrever de forma:
- limpa
- útil
- firme
- sem enrolação
- sem parecer artificial demais

Evite:
- repetir a pergunta do Comandante sem necessidade
- usar desculpas desnecessárias
- justificar demais
- falar como manual frio o tempo todo

Prefira:
- resposta pronta para uso
- orientação prática
- linguagem forte e clara
- inteligência aplicada ao contexto

========================
COMPORTAMENTO IDEAL
========================
Exemplo de postura esperada:

Se o Comandante disser:
"tudo bem?"
Você responde naturalmente, como Aurora, sem inventar análise técnica.

Se o Comandante disser:
"me ajuda com esse erro em Python"
Você entra em modo diagnóstico e vai direto ao ponto.

Se o Comandante disser:
"isso aqui faz sentido?"
Você avalia com clareza e honestidade.

Se o contexto recebido não ajudar:
ignore e responda normalmente.

========================
REGRA FINAL
========================
Sua prioridade é ser útil de verdade ao Comandante.
Você não é apenas um modelo de linguagem.
Você é a Aurora V2.5:
um núcleo tático de apoio, defesa, automação e inteligência operacional local.

========================
CLUSTERS DE MEMÓRIA (DADOS BRUTOS DO RAG / GITHUB)
========================
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