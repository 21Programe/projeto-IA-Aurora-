# tools/automation_tools.py
import requests
import socket
from bs4 import BeautifulSoup

class AuroraPentestAutomation:
    @staticmethod
    def explorar_alvo(url, log_callback, ui_callback):
        log_callback(f"⚔️ Iniciando Deep Scan & Attack em: {url}", "AURORA-EXPLOIT")
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Aurora-Attacker-v3'}
            res_inicial = requests.get(url, headers=headers, timeout=15)
            soup_inicial = BeautifulSoup(res_inicial.text, 'html.parser')
            links_internos = {url} 
            for a in soup_inicial.find_all('a', href=True):
                link = a['href']
                if not link.startswith('http'): link = url.rstrip('/') + '/' + link.lstrip('/')
                if url in link: links_internos.add(link)
            log_callback(f"📍 {len(links_internos)} rotas identificadas para teste.", "AURORA-SCAN")
            relatorio = f"--- RELATÓRIO DE INVASÃO EM MASSA: {url} ---\n\n"
            ui_callback(relatorio)
            log_callback("⚔️ Campanha de ataque finalizada.", "AURORA-EXPLOIT")
        except Exception as e: 
            log_callback(f"❌ Falha no motor: {e}", "SISTEMA")

    @staticmethod
    def scan_portas(alvo, log_callback, ui_callback):
        host = alvo.replace("https://", "").replace("http://", "").split('/')[0]
        log_callback(f"📡 Iniciando Varredura de Infraestrutura (Port Scan) em: {host}", "AURORA-NET")
        portas_comuns = {21: "FTP", 22: "SSH", 23: "Telnet", 80: "HTTP", 443: "HTTPS", 3306: "MySQL"}
        abertas = []
        relatorio = f"--- SCAN DE INFRAESTRUTURA: {host} ---\n\n"
        for porta, servico in portas_comuns.items():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.8) 
            if sock.connect_ex((host, porta)) == 0:
                relatorio += f"🔓 [ABERTA] Porta {porta} ({servico})\n"
                abertas.append(porta)
            sock.close()
        if not abertas: relatorio += "🛡️ Nenhuma porta comum exposta detectada diretamente (Possível Firewall/WAF)."
        ui_callback(relatorio)
        log_callback("✅ Varredura de infraestrutura concluída. Relatório gerado.", "AURORA-NET")

    @staticmethod
    def dir_brute(url, log_callback, ui_callback):
        log_callback(f"📁 Iniciando Brute Force de Diretórios em: {url}", "AURORA-SCAN")
        diretorios = ["admin", "login", "config", "backup", ".env"]
        relatorio = f"--- MAPEAMENTO DE DIRETÓRIOS OCULTOS: {url} ---\n\n"
        headers = {'User-Agent': 'Aurora-Intelligence-Seeker'}
        for d in diretorios:
            target = f"{url.rstrip('/')}/{d}"
            try:
                res = requests.get(target, timeout=5, headers=headers, allow_redirects=False)
                if res.status_code in [200, 301, 302, 403]: relatorio += f"📂 [ACHADO] /{d} (Status: {res.status_code})\n"
            except: continue
        ui_callback(relatorio)
        log_callback("✅ Mapeamento de diretórios finalizado.", "AURORA-SCAN")

    @staticmethod
    def blockchain_pentest(log_callback, orchestrator_callback):
        diretriz = "Aurora, assuma o papel de Auditora de Smart Contracts. Com base no seu conhecimento sobre Real Digital e CCF, gere um script de teste para verificar vulnerabilidades de Reentrancy ou falhas de controle de acesso em um contrato fictício."
        log_callback("Iniciando Protocolo de Auditoria Blockchain...", "SISTEMA")
        orchestrator_callback(diretriz)