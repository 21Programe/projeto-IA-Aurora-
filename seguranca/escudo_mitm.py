import time
import threading
from collections import defaultdict, deque
from urllib.parse import urlparse
from mitmproxy import http

from barramento_eventos import fila_alertas

# ==============================
# CONFIGURAÇÃO DEFENSIVA
# ==============================

# Domínios explicitamente maliciosos
DOMINIOS_MALICIOSOS = {
    "site-hacker.com",
    "phishing-banco.net",
    "download-virus.org",
    "ngrok.io",
    "temp-mail.org",
}

# Palavras/sinais suspeitos na URL
INDICADORES_SUSPEITOS = {
    "malware",
    "phishing",
    "stealer",
    "ransom",
    "payload",
    "keylogger",
    "botnet",
}

# Domínios permitidos mesmo se algum termo coincidir
ALLOWLIST = {
    "microsoft.com",
    "google.com",
    "github.com",
    "cloudflare.com",
}

# Controle anti-spam de alertas
JANELA_ALERTA_SEGUNDOS = 60
MAX_ALERTAS_POR_HOST = 3


class ControleAlertas:
    def __init__(self):
        self._eventos = defaultdict(deque)
        self._lock = threading.Lock()

    def pode_alertar(self, host: str) -> bool:
        agora = time.time()

        with self._lock:
            fila = self._eventos[host]

            while fila and (agora - fila[0]) > JANELA_ALERTA_SEGUNDOS:
                fila.popleft()

            if len(fila) >= MAX_ALERTAS_POR_HOST:
                return False

            fila.append(agora)
            return True


controle_alertas = ControleAlertas()


# ==============================
# FUNÇÕES AUXILIARES
# ==============================

def normalizar_host(host: str) -> str:
    if not host:
        return ""

    host = host.strip().lower().rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    return host


def host_corresponde(host: str, dominio_base: str) -> bool:
    """
    Bloqueia domínio exato e subdomínios.
    Ex.: evil.ngrok.io também casa com ngrok.io
    """
    host = normalizar_host(host)
    dominio_base = normalizar_host(dominio_base)

    return host == dominio_base or host.endswith("." + dominio_base)


def esta_na_allowlist(host: str) -> bool:
    host = normalizar_host(host)
    return any(host_corresponde(host, permitido) for permitido in ALLOWLIST)


def detectar_ameaca(url: str, host: str) -> str | None:
    url_lower = (url or "").lower()
    host = normalizar_host(host)

    # 1. Allowlist primeiro
    if esta_na_allowlist(host):
        return None

    # 2. Domínios bloqueados
    for dominio in DOMINIOS_MALICIOSOS:
        if host_corresponde(host, dominio):
            return f"Domínio malicioso identificado: {dominio}"

    # 3. Indicadores suspeitos na URL
    for indicador in INDICADORES_SUSPEITOS:
        if indicador in url_lower:
            return f"Indicador suspeito detectado na URL: {indicador}"

    return None


def gerar_html_bloqueio(motivo: str, dominio: str) -> bytes:
    html_bloqueio = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
        <head>
            <meta charset="utf-8">
            <title>AURORA EDR - BLOQUEIO</title>
            <style>
                body {{
                    background-color: #000;
                    color: #ff2b2b;
                    text-align: center;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                }}
                .box {{
                    margin: 8% auto;
                    width: 80%;
                    max-width: 900px;
                    border: 1px solid #ff2b2b;
                    padding: 30px;
                    box-shadow: 0 0 25px rgba(255, 0, 0, 0.25);
                    background: rgba(20, 20, 20, 0.95);
                }}
                h1 {{
                    font-size: 42px;
                    margin-bottom: 10px;
                }}
                h2 {{
                    color: #ffffff;
                    margin-top: 25px;
                }}
                p {{
                    font-size: 18px;
                    color: #d0d0d0;
                }}
                .rodape {{
                    color: #7a7a7a;
                    margin-top: 25px;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="box">
                <h1>⚠️ AURORA EDR: ACESSO BLOQUEADO</h1>
                <hr style="border: 1px solid red; width: 60%;">
                <h2>Destino bloqueado: {dominio}</h2>
                <p>{motivo}</p>
                <p>A conexão foi interrompida para proteger o ambiente monitorado.</p>
                <div class="rodape">[Comandante: Diego Alves de Souza]</div>
            </div>
        </body>
    </html>
    """
    return html_bloqueio.encode("utf-8")


def enviar_alerta(flow: http.HTTPFlow, motivo: str, url_alvo: str) -> None:
    host = flow.request.host or "desconhecido"

    if not controle_alertas.pode_alertar(host):
        return

    alerta = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tipo": "ALERTA_REDE",
        "nivel": "CRÍTICO",
        "processo": "proxy-client",
        "pid": 0,
        "usuario": "Diego",
        "porta_suspeita": getattr(flow.request, "port", 0),
        "estado": "CONEXÃO CORTADA",
        "ip_remoto": host,
        "executavel": "Proxy_MITM_Aurora",
        "metodo_http": getattr(flow.request, "method", "GET"),
        "motivo": motivo,
        "mensagem": f"Acesso bloqueado: {url_alvo}",
    }

    fila_alertas.put(alerta)


# ==============================
# ESCUDO WEB
# ==============================

class EscudoWebAurora:
    def request(self, flow: http.HTTPFlow) -> None:
        try:
            url_alvo = flow.request.pretty_url or ""
            host = normalizar_host(flow.request.pretty_host or flow.request.host or "")
            motivo = detectar_ameaca(url_alvo, host)

            if not motivo:
                return

            print(f"\n[ESCUDO WEB] 🛑 BLOQUEIO TÁTICO: {host}")
            print(f"[MOTIVO] {motivo}")

            flow.response = http.Response.make(
                403,
                gerar_html_bloqueio(motivo, host),
                {
                    "Content-Type": "text/html; charset=utf-8",
                    "Cache-Control": "no-store, no-cache, must-revalidate",
                    "Pragma": "no-cache",
                },
            )

            enviar_alerta(flow, motivo, url_alvo)

        except Exception as e:
            print(f"[ERRO ESCUDO WEB] Falha ao processar requisição: {e}")


addons = [EscudoWebAurora()]