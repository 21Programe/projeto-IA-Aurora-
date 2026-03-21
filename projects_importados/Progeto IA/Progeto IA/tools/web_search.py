# tools/web_search.py
import requests
import re
import time
import webbrowser
from bs4 import BeautifulSoup, Comment

class WebReconTools:
    @staticmethod
    def inspecionar_web(url, log_callback, ui_callback):
        log_callback(f"🕵️ Iniciando Inspeção de Superfície em: {url}", "AURORA-SCAN")
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Aurora-Inspector'}
            res = requests.get(url, headers=headers, timeout=30)
            soup = BeautifulSoup(res.text, 'html.parser')
            relatorio = f"--- RELATÓRIO DE INSPEÇÃO DOM: {url} ---\n\n"
            forms = soup.find_all('form')
            relatorio += f"[+] FORMS DETECTADOS: {len(forms)}\n"
            for i, form in enumerate(forms):
                action = form.get('action', 'N/A')
                method = form.get('method', 'GET').upper()
                relatorio += f"\n  -> Form {i+1}: Método {method} | Destino: {action}\n"
                for inp in form.find_all('input'):
                    inp_type = inp.get('type', 'text')
                    inp_name = inp.get('name', 'N/A')
                    inp_value = inp.get('value', '')
                    if inp_type == 'hidden': relatorio += f"     ⚠️ HIDDEN INPUT: name='{inp_name}' value='{inp_value}'\n"
                    elif inp_type in ['text', 'email', 'password', 'search']: relatorio += f"     - Input Visível: type='{inp_type}' name='{inp_name}'\n"
            
            relatorio += "\n[+] COMENTÁRIOS NO CÓDIGO FONTE:\n"
            comments = soup.find_all(string=lambda text: isinstance(text, Comment))
            com_uteis = sum(1 for c in comments if 4 < len(str(c).strip()) < 200)
            if com_uteis == 0: relatorio += "  -> Nenhum comentário suspeito encontrado.\n"
            else: relatorio += f"  -> {com_uteis} Comentários encontrados.\n"
            
            relatorio += "\n======================================================\n[!] GUIA TÁTICO GERADO COM SUCESSO.\n======================================================"
            ui_callback(relatorio)
            log_callback(f"✅ Inspeção de {url} finalizada.", "SISTEMA")
        except Exception as e: 
            log_callback(f"❌ Erro na inspeção: {e}", "SISTEMA")

    @staticmethod
    def osint_dorking(alvo, log_callback, ui_callback):
        log_callback(f"🕵️ Iniciando Varredura OSINT (Google Dorking) para: {alvo}", "AURORA-BLACKOPS")
        try:
            dorks = {
                "Painéis de Admin": f'site:{alvo} intitle:"admin" OR intitle:"login"',
                "Arquivos Confidenciais": f'site:{alvo} filetype:pdf OR filetype:doc OR filetype:xlsx "confidencial"',
                "Bancos de Dados/Logs": f'site:{alvo} filetype:log OR filetype:sql OR filetype:env',
                "Diretórios Expostos": f'site:{alvo} intitle:"index of /"',
                "Câmeras/Dispositivos": f'site:{alvo} inurl:/view/index.shtml'
            }
            relatorio = f"--- OPERAÇÃO BLACK OPS: BUSCA DE VULNERABILIDADES EXTERNAS ---\nALVO: {alvo}\n\n[!] A Aurora está abrindo as consultas de inteligência no seu navegador...\n\n"
            for categoria, query in dorks.items():
                relatorio += f"[+] Categoria: {categoria}\n    🔍 Dork: {query}\n\n"
                url_busca = f"https://www.google.com/search?q={query.replace(' ', '+')}"
                webbrowser.open(url_busca)
                time.sleep(1.5) 

            relatorio += "======================================================\n🎯 ANALISE OS RESULTADOS NO NAVEGADOR PARA ENCONTRAR BRECHAS."
            ui_callback(relatorio)
            log_callback("✅ Varredura OSINT finalizada. Inteligência extraída com sucesso.", "AURORA-BLACKOPS")
        except Exception as e:
            log_callback(f"❌ Falha no motor Black Ops: {e}", "SISTEMA")

    @staticmethod
    def scan_cabecalhos(url, log_callback, ui_callback):
        log_callback(f"🛡️ Iniciando Auditoria de Cabeçalhos e WAF em: {url}", "AURORA-BLUE")
        try:
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 Aurora-Auditor'}, timeout=10)
            cabecalhos = res.headers
            relatorio = f"--- AUDITORIA DE SEGURANÇA (HTTP HEADERS): {url} ---\n\n"
            relatorio += f"  -> Servidor Web Exposto: {cabecalhos.get('Server', 'Oculto')}\n"
            relatorio += f"  -> Tecnologia/Linguagem: {cabecalhos.get('X-Powered-By', 'Oculto')}\n\n"
            ui_callback(relatorio)
            log_callback("✅ Auditoria de cabeçalhos finalizada com sucesso.", "AURORA-BLUE")
        except Exception as e: 
            log_callback(f"❌ Falha no motor de auditoria: {e}", "SISTEMA")