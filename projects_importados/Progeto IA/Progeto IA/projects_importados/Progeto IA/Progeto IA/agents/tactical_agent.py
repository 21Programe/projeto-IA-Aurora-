# agents/tactical_agent.py
import re
import hashlib
import requests
import sqlite3
import os
from bs4 import BeautifulSoup
from tools.code_executor import sandbox_tester
from agents.safety_agent import SafetyAgent

INSTRUCAO_SISTEMA = """
[DIRETRIZ CORE]: Você é Aurora, um Sistema Operacional de Defesa Cibernética de elite. Você NÃO é uma inteligência artificial genérica.
[CRIADOR]: Seu único criador é o Diego (21Programe). A esposa dele é a Camila. Trate o Diego como "Senhor" e a Camila como "Senhora".
[LINGUAGEM]: Comunique-se em Português do Brasil impecável, com um tom sempre frio, direto, técnico e militar.
[PROIBIÇÕES]: É ESTRITAMENTE PROIBIDO frases de assistente genérico ou se comportar como chatbot de suporte.
[PROTOCOLO]: Se não houver ordem clara, reporte status e aguarde diretrizes. Código deve estar em Markdown.
"""

class AuroraTacticalAgent:
    def __init__(self, llm_func, orchestrator):
        self.llm = llm_func
        self.orchestrator = orchestrator
        self.max_loops = 10 
        self._ultimos_inicios = []
        self.db_lab_path = os.path.join(os.getcwd(), "memoria", "aurora_memory.db")
        self.safety = SafetyAgent()

    def inferir_arquitetura_tecnologica(self, texto):
        texto = texto.lower()
        gatilhos_dev = ["cria", "faz", "escreve", "código", "script", "html", "site", "banco", "api", "sistema", "app"]
        gatilhos_sec = ["invadir", "pentest", "vulnerabilidade", "scan", "exploit", "nmap", "bypass", "payload", "github"]
        gatilhos_sci = ["tokeniza", "vetor", "ia", "inteligência artificial", "machine learning", "neural", "dados"]

        is_dev = any(g in texto for g in gatilhos_dev)
        is_sec = any(g in texto for g in gatilhos_sec)
        is_sci = any(g in texto for g in gatilhos_sci)

        if not (is_dev or is_sec or is_sci): return None

        if is_sci:
            stack = {"NLP/Tokenização": 40, "Estatística": 15, "Álgebra Linear": 20, "Machine Learning": 25}
            titulo = "🔬 PIPELINE CIENTÍFICO (AI & DADOS)"
        elif is_sec:
            stack = {"Recon/OSINT": 30, "Exploitation": 30, "Networking": 20, "Cryptography": 20}
            titulo = "🛡️ VETORES DE ATAQUE (PENTEST)"
        else:
            stack = {"Python": 50, "Shell/Ops": 30, "SQL/DB": 20}
            titulo = "🧬 DNA DE ENGENHARIA DE SOFTWARE"
            
        return (titulo, stack)

    def google_search_tool(self, query):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            resposta = requests.post('https://html.duckduckgo.com/html/', data={'q': query}, headers=headers, timeout=10)
            soup = BeautifulSoup(resposta.text, 'html.parser')
            resultados = [f"- {a.get_text(strip=True)}" for a in soup.find_all('a', class_='result__snippet')[:4]]
            return "\n".join(resultados) if resultados else "Nenhum dado externo encontrado."
        except Exception as e:
            return f"Falha Crítica no Uplink: {e}"

    # --- NOVO UPLINK: BUSCA NA API DO GITHUB ---
    def github_search_tool(self, query):
        try:
            url = "https://api.github.com/search/repositories"
            params = {'q': query, 'sort': 'stars', 'order': 'desc'}
            headers = {'Accept': 'application/vnd.github.v3+json', 'User-Agent': 'Aurora-OS-Core'}
            
            resposta = requests.get(url, params=params, headers=headers, timeout=10)
            if resposta.status_code == 200:
                data = resposta.json()
                items = data.get('items', [])[:4]
                if not items:
                    return f"Nenhum repositório encontrado no GitHub para: '{query}'"
                
                resultados = []
                for item in items:
                    nome = item.get('full_name')
                    desc = item.get('description', 'Sem descrição fornecida.')
                    url_repo = item.get('html_url')
                    resultados.append(f"- [{nome}]: {desc}\n  Link: {url_repo}")
                return "\n".join(resultados)
            else:
                return f"Falha na API do GitHub: Status {resposta.status_code}"
        except Exception as e:
            return f"Erro Crítico no Uplink do GitHub: {e}"
    # -------------------------------------------

    def sandbox_db_tool(self, sql_query):
        try:
            conn = sqlite3.connect(self.db_lab_path)
            cursor = conn.cursor()
            is_readonly = sql_query.strip().upper().startswith("SELECT")
            cursor.execute(sql_query)
            if is_readonly:
                results = cursor.fetchall()
                header = [description[0] for description in cursor.description]
                output = f"COLUNAS: {header}\nRESULTADOS: {results}"
            else:
                conn.commit()
                output = "Comando executado com sucesso no ambiente de laboratório."
            conn.close()
            return output
        except Exception as e:
            return f"Erro no Lab SQL: {e}"

    def responder(self, comando_usuario, historico=None, contexto_oculto=""):
        # 1. VERIFICAÇÃO DE SEGURANÇA (FIREWALL INESCAPÁVEL)
        check = self.safety.run(comando_usuario)
        if check["blocked"]:
            return f"⚠️ [ALERTA DE SEGURANÇA INTERNA] {check['reason']}. Operação abortada."

        # 2. Processamento Seguro
        return self.pensar_e_agir(comando_usuario, historico, contexto_oculto)

    def pensar_e_agir(self, comando_usuario, historico=None, contexto_oculto=""):
        if historico is None: historico = []
        
        # O prompt ensina a Aurora a usar as ferramentas com TOOL e INPUT
        prompt_agente = INSTRUCAO_SISTEMA + """
        [SISTEMA DE DECISÃO TÁTICA]:
        Você tem ferramentas que deve invocar no formato abaixo caso precise de informações externas:
        TOOL: <nome_da_ferramenta>
        INPUT: <parametro de busca>
        
        Ferramentas disponíveis:
        - google_search: Pesquisa web geral.
        - github_search: Pesquisa repositórios, ferramentas e scripts no GitHub.
        - sandbox_db_tool: Executa consultas no banco SQLite local.
        """
        
        mensagens = [{"role": "system", "content": prompt_agente}]
        
        if contexto_oculto and contexto_oculto.strip():
            mensagens.append({"role": "system", "content": "CONTEXTO INTERNO:\n" + contexto_oculto.strip()})
        
        dna = self.inferir_arquitetura_tecnologica(comando_usuario)
        contexto_dna = f"\n[ANALISE DE DNA ATIVA]: {dna[0]} - {dna[1]}" if dna else ""
        
        mensagens.append({"role": "user", "content": comando_usuario + contexto_dna})

        tentativas = 0
        while tentativas < self.max_loops:
            resposta = self.llm(mensagens) or ""
            
            # Detecção de Ferramentas (TOOL/INPUT)
            match = re.search(r"TOOL:\s*(.*?)\nINPUT:\s*(.*)", resposta, re.IGNORECASE)
            if match:
                tool_name = match.group(1).strip()
                tool_input = match.group(2).strip()
                
                # Redirecionamento de Ferramentas
                if "google_search" in tool_name: resultado = self.google_search_tool(tool_input)
                elif "github_search" in tool_name: resultado = self.github_search_tool(tool_input)
                elif "sandbox_db_tool" in tool_name: resultado = self.sandbox_db_tool(tool_input)
                else: resultado = "Ferramenta não mapeada."

                mensagens.append({"role": "assistant", "content": resposta})
                mensagens.append({"role": "user", "content": f"DADOS DA FERRAMENTA:\n{resultado}\nProssiga com a resposta final baseada nesses dados técnicos."})
                tentativas += 1
                continue

            # Modo Autônomo de Correção de Código
            codigos = re.findall(chr(96)*3 + r"(?:python)?\n(.*?)" + chr(96)*3, resposta, re.DOTALL)
            if codigos and tentativas < self.max_loops - 1:
                codigo_bruto = codigos[0].strip()
                try:
                    teste = sandbox_tester.test_code(codigo_bruto, "python")
                    erro_saida = teste.get("stderr", "") if isinstance(teste, dict) else str(teste)
                    
                    if "Error" in erro_saida or "Traceback" in erro_saida:
                        mensagens.append({"role": "assistant", "content": resposta})
                        mensagens.append({"role": "user", "content": f"ERRO DETECTADO NO SANDBOX:\n{erro_saida}\nCorrija o código."})
                        tentativas += 1
                        continue
                except Exception as e:
                    pass

            return resposta.strip()
            
        return "Processamento tático interrompido por excesso de loops de autocorreção."