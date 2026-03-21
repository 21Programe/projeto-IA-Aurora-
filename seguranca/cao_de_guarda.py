import psutil
import time
import socket
import logging
from datetime import datetime
from collections import deque
from threading import Lock
from seguranca.barramento_eventos import fila_alertas

# =========================
# CONFIGURAÇÃO
# =========================
PORTAS_SUSPEITAS = {4444, 5555, 8888}
ESTADOS_MONITORADOS = {"LISTEN", "ESTABLISHED"}
INTERVALO_VARREDURA = 3
TTL_ALERTA_SEGUNDOS = 300  # evita repetição por 5 minutos
MAX_HISTORICO = 5000

# Processos permitidos nessas portas, se você quiser exceções
ALLOWLIST_PROCESSOS = {
    # "python.exe",
    # "svchost.exe",
}

# IPs permitidos, se necessário
ALLOWLIST_IPS = {
    "127.0.0.1",
    "::1",
}

# =========================
# LOG
# =========================
logging.basicConfig(
    filename="monitor_rede.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# =========================
# CONTROLE DE ALERTAS
# =========================
alertas_enviados = {}
historico_eventos = deque(maxlen=MAX_HISTORICO)
lock_alertas = Lock()


def agora_str():
    return datetime.utcnow().isoformat() + "Z"


def limpar_alertas_expirados():
    """Remove alertas antigos para não crescer memória indefinidamente."""
    limite = time.time() - TTL_ALERTA_SEGUNDOS
    with lock_alertas:
        expirados = [k for k, ts in alertas_enviados.items() if ts < limite]
        for k in expirados:
            del alertas_enviados[k]


def resolver_ip(ip):
    """Tenta resolver DNS reverso sem quebrar a rotina."""
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return None


def classificar_risco(porta, estado, ip_remoto, nome_proc):
    """Classificação simples de severidade."""
    risco = "MÉDIO"

    if porta in PORTAS_SUSPEITAS:
        risco = "ALTO"

    if estado == "ESTABLISHED" and ip_remoto and ip_remoto not in ALLOWLIST_IPS:
        risco = "CRÍTICO"

    if nome_proc.lower() not in {p.lower() for p in ALLOWLIST_PROCESSOS} and porta in PORTAS_SUSPEITAS:
        risco = "CRÍTICO"

    return risco


def criar_chave_unica(conn):
    pid = conn.pid or 0
    laddr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "0.0.0.0:0"
    raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "0.0.0.0:0"
    return f"{pid}|{conn.status}|{laddr}|{raddr}"


def processo_allowlist(nome_proc):
    return nome_proc.lower() in {p.lower() for p in ALLOWLIST_PROCESSOS}


def monitorar_conexoes_rede():
    """
    Monitora conexões suspeitas de forma defensiva.
    Não executa contra-ataque.
    Apenas detecta, classifica e envia alerta.
    """
    limpar_alertas_expirados()

    try:
        conexoes = psutil.net_connections(kind="inet")
    except Exception as e:
        logging.error(f"Falha ao listar conexões: {e}")
        return

    for conn in conexoes:
        try:
            if conn.status not in ESTADOS_MONITORADOS:
                continue

            porta_local = conn.laddr.port if conn.laddr else 0
            porta_remota = conn.raddr.port if conn.raddr else 0

            if porta_local not in PORTAS_SUSPEITAS and porta_remota not in PORTAS_SUSPEITAS:
                continue

            pid = conn.pid
            if not pid:
                continue

            try:
                proc = psutil.Process(pid)
                nome_proc = proc.name()
                usuario_proc = proc.username()
                cmdline = " ".join(proc.cmdline())[:500]
                exe_path = proc.exe()
                criado_em = datetime.fromtimestamp(proc.create_time()).isoformat()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                nome_proc = "desconhecido"
                usuario_proc = "desconhecido"
                cmdline = ""
                exe_path = ""
                criado_em = ""

            if processo_allowlist(nome_proc):
                continue

            ip_remoto = conn.raddr.ip if conn.raddr else None
            host_remoto = resolver_ip(ip_remoto) if ip_remoto else None
            porta_alvo = porta_local if porta_local in PORTAS_SUSPEITAS else porta_remota
            risco = classificar_risco(porta_alvo, conn.status, ip_remoto, nome_proc)

            chave = criar_chave_unica(conn)

            with lock_alertas:
                if chave in alertas_enviados:
                    continue
                alertas_enviados[chave] = time.time()

            alerta = {
                "timestamp": agora_str(),
                "tipo": "ALERTA_REDE",
                "nivel": risco,
                "processo": nome_proc,
                "pid": pid,
                "usuario": usuario_proc,
                "porta_suspeita": porta_alvo,
                "estado": conn.status,
                "ip_local": conn.laddr.ip if conn.laddr else None,
                "porta_local": porta_local,
                "ip_remoto": ip_remoto,
                "porta_remota": porta_remota,
                "host_remoto": host_remoto,
                "executavel": exe_path,
                "cmdline": cmdline,
                "criado_em": criado_em,
                "mensagem": (
                    f"Conexão suspeita detectada: processo={nome_proc} pid={pid} "
                    f"estado={conn.status} porta={porta_alvo} remoto={ip_remoto}:{porta_remota}"
                )
            }

            historico_eventos.append(alerta)
            fila_alertas.put(alerta)

            logging.warning(
                f"[{risco}] {alerta['mensagem']} | exe={exe_path} | usuario={usuario_proc}"
            )

        except Exception as e:
            logging.error(f"Erro ao processar conexão: {e}")


def rotina_de_seguranca_invisivel():
    """Loop principal defensivo."""
    logging.info("Rotina de segurança iniciada.")
    while True:
        monitorar_conexoes_rede()
        time.sleep(INTERVALO_VARREDURA)


if __name__ == "__main__":
    rotina_de_seguranca_invisivel()