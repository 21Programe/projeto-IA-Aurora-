import os
import re
import json
import time
import shutil
import hashlib
import mimetypes
from pathlib import Path
from datetime import datetime
from threading import Lock

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from seguranca.barramento_eventos import fila_alertas

# =========================================================
# CONFIGURAÇÕES
# =========================================================
PASTA_MONITORADA = os.path.join(os.path.expanduser("~"), "Downloads")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PASTA_QUARENTENA = os.path.join(BASE_DIR, "prisao_quarentena")
PASTA_LOGS = os.path.join(BASE_DIR, "logs")
ARQUIVO_LOG = os.path.join(PASTA_LOGS, "quarentena_web.jsonl")

os.makedirs(PASTA_QUARENTENA, exist_ok=True)
os.makedirs(PASTA_LOGS, exist_ok=True)

# Assinaturas simples de risco
ASSINATURAS_MALICIOSAS = [
    b"<script",
    b"powershell",
    b"eval(",
    b"wscript.shell",
    b"cscript",
    b"cmd.exe",
    b"invoke-webrequest",
    b"invoke-expression",
    b"frombase64string",
    b"http://",
    b"https://",
    b"mshta",
    b"regsvr32",
    b"rundll32",
]

# Extensões mais sensíveis para elevar risco
EXTENSOES_RISCO_ALTO = {
    ".exe", ".msi", ".bat", ".cmd", ".ps1", ".vbs", ".js", ".jse",
    ".wsf", ".scr", ".hta", ".dll", ".jar", ".lnk"
}

# Extensões compactadas / contêiner
EXTENSOES_ARQUIVO_COMPACTADO = {
    ".zip", ".rar", ".7z", ".iso"
}

# Ignorados
EXTENSOES_TEMPORARIAS = {
    ".crdownload", ".tmp", ".part", ".download"
}

NOMES_IGNORADOS = {
    "desktop.ini",
    "thumbs.db",
}

MAX_LEITURA_CABECALHO = 200_000
MAX_LEITURA_RODAPE = 100_000
TAMANHO_MAX_ANALISE = 100 * 1024 * 1024  # 100 MB
TEMPO_ESPERA_ARQUIVO_ESTAVEL = 2.0
MAX_TENTATIVAS_ESTABILIZACAO = 8

# Evita processar várias vezes o mesmo arquivo em sequência
arquivos_processados = {}
processados_lock = Lock()
TTL_REPROCESSAMENTO = 120  # segundos


# =========================================================
# UTILITÁRIOS
# =========================================================
def agora_iso():
    return datetime.utcnow().isoformat() + "Z"


def registrar_log(tipo, dados):
    evento = {
        "timestamp": agora_iso(),
        "tipo": tipo,
        "dados": dados
    }
    try:
        with open(ARQUIVO_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(evento, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[LOG] Falha ao gravar log: {e}")


def limpar_cache_processados():
    limite = time.time() - TTL_REPROCESSAMENTO
    with processados_lock:
        expirados = [k for k, v in arquivos_processados.items() if v < limite]
        for k in expirados:
            del arquivos_processados[k]


def ja_processado_recentemente(caminho):
    limpar_cache_processados()
    with processados_lock:
        if caminho in arquivos_processados:
            return True
        arquivos_processados[caminho] = time.time()
        return False


def calcular_sha256(caminho):
    sha256 = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1024 * 1024), b""):
            sha256.update(bloco)
    return sha256.hexdigest()


def obter_tamanho(caminho):
    try:
        return os.path.getsize(caminho)
    except Exception:
        return 0


def esperar_arquivo_estavel(caminho):
    """
    Espera o arquivo parar de crescer/modificar para reduzir erro
    ao analisar download ainda em andamento.
    """
    ultimo_tamanho = -1
    ult_mtime = -1.0

    for _ in range(MAX_TENTATIVAS_ESTABILIZACAO):
        if not os.path.exists(caminho):
            return False

        try:
            tamanho = os.path.getsize(caminho)
            mtime = os.path.getmtime(caminho)
        except OSError:
            time.sleep(TEMPO_ESPERA_ARQUIVO_ESTAVEL)
            continue

        if tamanho == ultimo_tamanho and mtime == ult_mtime and tamanho > 0:
            return True

        ultimo_tamanho = tamanho
        ult_mtime = mtime
        time.sleep(TEMPO_ESPERA_ARQUIVO_ESTAVEL)

    return False


def inferir_tipo_arquivo(caminho):
    mime, _ = mimetypes.guess_type(caminho)
    return mime or "application/octet-stream"


def nome_seguro_quarentena(nome_arquivo):
    nome_limpo = re.sub(r'[^a-zA-Z0-9._-]', '_', nome_arquivo)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_INFECTADO_{nome_limpo}.locked"


def risco_por_extensao(extensao):
    ext = extensao.lower()
    if ext in EXTENSOES_RISCO_ALTO:
        return "CRÍTICO"
    if ext in EXTENSOES_ARQUIVO_COMPACTADO:
        return "ALTO"
    return "MÉDIO"


def contem_assinatura(conteudo: bytes):
    conteudo_lower = conteudo.lower()
    for assinatura in ASSINATURAS_MALICIOSAS:
        if assinatura in conteudo_lower:
            return True, assinatura.decode("utf-8", errors="ignore")
    return False, None


def analisar_bytes_arquivo(caminho_arquivo):
    """
    Estratégia rápida:
    - lê cabeçalho
    - lê rodapé
    - busca padrões suspeitos
    - retorna detalhes para decisão
    """
    resultado = {
        "infectado": False,
        "assinatura": None,
        "motivo": None,
        "tamanho": 0,
        "mime": inferir_tipo_arquivo(caminho_arquivo),
        "extensao": Path(caminho_arquivo).suffix.lower(),
    }

    try:
        tamanho = os.path.getsize(caminho_arquivo)
        resultado["tamanho"] = tamanho

        if tamanho == 0:
            resultado["motivo"] = "arquivo_vazio"
            return resultado

        if tamanho > TAMANHO_MAX_ANALISE:
            resultado["motivo"] = "arquivo_muito_grande_analise_parcial"

        with open(caminho_arquivo, "rb") as f:
            cabecalho = f.read(min(MAX_LEITURA_CABECALHO, tamanho))

            infectado, assinatura = contem_assinatura(cabecalho)
            if infectado:
                resultado["infectado"] = True
                resultado["assinatura"] = assinatura
                resultado["motivo"] = "assinatura_no_cabecalho"
                return resultado

            if tamanho > MAX_LEITURA_RODAPE:
                f.seek(max(0, tamanho - MAX_LEITURA_RODAPE))
            rodape = f.read(MAX_LEITURA_RODAPE)

            infectado, assinatura = contem_assinatura(rodape)
            if infectado:
                resultado["infectado"] = True
                resultado["assinatura"] = assinatura
                resultado["motivo"] = "assinatura_no_rodape"
                return resultado

        # Heurística simples por extensão
        if resultado["extensao"] in EXTENSOES_RISCO_ALTO:
            # executável/script baixado da internet merece alerta elevado,
            # mas não significa infecção por si só
            resultado["motivo"] = "extensao_sensivel"
            return resultado

        return resultado

    except Exception as e:
        resultado["motivo"] = f"erro_analise: {e}"
        return resultado


def isolar_ameaca(caminho_arquivo, nome_arquivo):
    """
    Move para quarentena com nome seguro.
    """
    destino = os.path.join(PASTA_QUARENTENA, nome_seguro_quarentena(nome_arquivo))
    try:
        shutil.move(caminho_arquivo, destino)
        return True, destino
    except Exception as e:
        return False, f"Falha ao isolar: {e}"


def construir_alerta(nome_arquivo, caminho_original, caminho_isolado, analise, sha256):
    nivel = "CRÍTICO" if analise["infectado"] else risco_por_extensao(analise["extensao"])

    return {
        "timestamp": agora_iso(),
        "tipo": "ALERTA_QUARENTENA",
        "nivel": nivel,
        "processo": "download_monitor",
        "pid": 0,
        "usuario": os.path.expanduser("~").split("\\")[-1] if "\\" in os.path.expanduser("~") else os.path.basename(os.path.expanduser("~")),
        "porta_suspeita": "Download Web",
        "estado": "ISOLADO" if caminho_isolado else "DETECTADO",
        "ip_remoto": "N/A",
        "arquivo_original": caminho_original,
        "arquivo_isolado": caminho_isolado,
        "executavel": caminho_isolado or caminho_original,
        "nome_arquivo": nome_arquivo,
        "sha256": sha256,
        "mime": analise["mime"],
        "extensao": analise["extensao"],
        "motivo": analise["motivo"],
        "assinatura": analise["assinatura"],
        "mensagem": (
            f"Arquivo suspeito detectado em Downloads: {nome_arquivo}. "
            f"Motivo={analise['motivo']}; assinatura={analise['assinatura']}; sha256={sha256[:16]}..."
        )
    }


# =========================================================
# HANDLER
# =========================================================
class MonitorDownloads(FileSystemEventHandler):
    def on_created(self, event):
        self._processar_evento(event.src_path, event.is_directory)

    def on_moved(self, event):
        self._processar_evento(event.dest_path, False)

    def _processar_evento(self, caminho, is_directory):
        if is_directory:
            return

        try:
            nome_arquivo = os.path.basename(caminho)
            extensao = Path(nome_arquivo).suffix.lower()

            if not nome_arquivo or nome_arquivo.lower() in NOMES_IGNORADOS:
                return

            if extensao in EXTENSOES_TEMPORARIAS:
                return

            if not os.path.exists(caminho):
                return

            if ja_processado_recentemente(caminho):
                return

            print(f"\n[QUARENTENA] 🔍 Novo arquivo detectado: {nome_arquivo}")
            registrar_log("arquivo_detectado", {
                "arquivo": caminho,
                "nome": nome_arquivo
            })

            estavel = esperar_arquivo_estavel(caminho)
            if not estavel:
                registrar_log("arquivo_instavel", {
                    "arquivo": caminho,
                    "nome": nome_arquivo
                })
                return

            tamanho = obter_tamanho(caminho)
            if tamanho <= 0:
                return

            analise = analisar_bytes_arquivo(caminho)

            # Só calcula hash quando o arquivo realmente existe e estabilizou
            try:
                sha256 = calcular_sha256(caminho)
            except Exception:
                sha256 = "indisponivel"

            # Regra de contenção:
            # 1) se assinatura foi detectada, isola
            # 2) opcionalmente você pode isolar também extensões críticas
            deve_isolar = analise["infectado"]

            caminho_isolado = None
            if deve_isolar:
                sucesso, resultado = isolar_ameaca(caminho, nome_arquivo)
                if sucesso:
                    caminho_isolado = resultado
                    print(f"[QUARENTENA] 🛑 Arquivo isolado: {resultado}")
                else:
                    print(f"[QUARENTENA] ❌ {resultado}")
                    registrar_log("falha_isolamento", {
                        "arquivo": caminho,
                        "erro": resultado
                    })

            # Alerta em assinatura real ou extensão muito sensível
            if analise["infectado"] or analise["extensao"] in EXTENSOES_RISCO_ALTO:
                alerta = construir_alerta(
                    nome_arquivo=nome_arquivo,
                    caminho_original=caminho,
                    caminho_isolado=caminho_isolado,
                    analise=analise,
                    sha256=sha256
                )
                fila_alertas.put(alerta)
                registrar_log("alerta_emitido", alerta)

                if analise["infectado"]:
                    print(f"[QUARENTENA] 🚨 Ameaça detectada: assinatura={analise['assinatura']}")
                else:
                    print(f"[QUARENTENA] ⚠️ Arquivo sensível detectado: {nome_arquivo}")

        except Exception as e:
            registrar_log("erro_handler", {
                "arquivo": caminho,
                "erro": str(e)
            })
            print(f"[QUARENTENA] Erro ao processar arquivo: {e}")


# =========================================================
# ROTINA PRINCIPAL
# =========================================================
def rotina_quarentena_web():
    print(f"[SYSTEM] Escudo de Quarentena Web ativado em: {PASTA_MONITORADA}")
    print(f"[SYSTEM] Quarentena: {PASTA_QUARENTENA}")
    print(f"[SYSTEM] Logs: {ARQUIVO_LOG}")

    if not os.path.isdir(PASTA_MONITORADA):
        raise FileNotFoundError(f"Pasta monitorada não encontrada: {PASTA_MONITORADA}")

    observador = Observer()
    manipulador = MonitorDownloads()
    observador.schedule(manipulador, PASTA_MONITORADA, recursive=False)
    observador.start()

    registrar_log("monitor_iniciado", {
        "pasta_monitorada": PASTA_MONITORADA,
        "pasta_quarentena": PASTA_QUARENTENA
    })

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[SYSTEM] Encerrando monitor de quarentena...")
        registrar_log("monitor_encerrado", {})
        observador.stop()
    except Exception as e:
        registrar_log("erro_rotina_principal", {"erro": str(e)})
        observador.stop()
        raise
    finally:
        observador.join()


if __name__ == "__main__":
    rotina_quarentena_web()