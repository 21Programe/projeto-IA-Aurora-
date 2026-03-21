import ctypes
import psutil
import os
import json
import time
from datetime import datetime

ARQUIVO_LOG = "aurora_defesa_log.jsonl"

# Processos críticos que não devem ser encerrados automaticamente
PROCESSOS_PROTEGIDOS = {
    "system",
    "registry",
    "wininit.exe",
    "winlogon.exe",
    "csrss.exe",
    "services.exe",
    "lsass.exe",
    "smss.exe",
    "svchost.exe",
    "explorer.exe",
}

def agora():
    return datetime.utcnow().isoformat() + "Z"

def registrar_evento(tipo, dados):
    """Grava eventos em JSONL para auditoria."""
    evento = {
        "timestamp": agora(),
        "tipo": tipo,
        "dados": dados
    }
    try:
        with open(ARQUIVO_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(evento, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[LOG] Falha ao registrar evento: {e}")

def processo_eh_protegido(nome_processo):
    return (nome_processo or "").lower() in PROCESSOS_PROTEGIDOS

def coletar_detalhes_processo(pid):
    """Coleta o máximo de contexto possível sem derrubar a execução."""
    detalhes = {
        "pid": pid,
        "nome": "desconhecido",
        "usuario": "desconhecido",
        "exe": "",
        "cmdline": "",
        "status": "",
        "criado_em": "",
    }

    try:
        p = psutil.Process(pid)
        detalhes["nome"] = p.name()
        detalhes["usuario"] = p.username()
        detalhes["exe"] = p.exe()
        detalhes["cmdline"] = " ".join(p.cmdline())[:600]
        detalhes["status"] = p.status()
        detalhes["criado_em"] = datetime.fromtimestamp(p.create_time()).isoformat()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    except Exception as e:
        detalhes["erro"] = str(e)

    return detalhes

def neutralizar_ameaca(pid, processo):
    """Defesa ativa local: tenta encerrar o processo com cuidado."""
    detalhes_antes = coletar_detalhes_processo(pid)
    registrar_evento("tentativa_neutralizacao", {
        "pid": pid,
        "processo_informado": processo,
        "detalhes_antes": detalhes_antes
    })

    nome_real = detalhes_antes.get("nome", processo)

    if processo_eh_protegido(nome_real):
        msg = f"[DEFESA ATIVA] Processo protegido detectado: {nome_real} (PID: {pid}). Encerramento bloqueado."
        print(msg)
        registrar_evento("neutralizacao_bloqueada", {"pid": pid, "processo": nome_real, "motivo": "processo_protegido"})
        return False

    try:
        p = psutil.Process(pid)
        # Tentativa amigável
        p.terminate()
        try:
            p.wait(timeout=3)
            print(f"[DEFESA ATIVA] Processo {nome_real} (PID: {pid}) encerrado via terminate().")
            registrar_evento("neutralizacao_sucesso", {"pid": pid, "processo": nome_real, "modo": "terminate"})
            return True
        except psutil.TimeoutExpired:
            pass

        # Tentativa forçada
        p.kill()
        p.wait(timeout=2)
        print(f"[DEFESA ATIVA] Processo {nome_real} (PID: {pid}) encerrado via kill().")
        registrar_evento("neutralizacao_sucesso", {"pid": pid, "processo": nome_real, "modo": "kill"})
        return True

    except psutil.NoSuchProcess:
        print(f"[DEFESA ATIVA] O processo {nome_real} (PID: {pid}) já não existe mais.")
        registrar_evento("neutralizacao_sem_alvo", {"pid": pid, "processo": nome_real})
        return True

    except psutil.AccessDenied:
        print(f"[DEFESA ATIVA] Acesso negado ao tentar encerrar {nome_real}. Execute como Administrador.")
        registrar_evento("neutralizacao_falha", {"pid": pid, "processo": nome_real, "motivo": "access_denied"})
        return False

    except Exception as e:
        print(f"[DEFESA ATIVA] Erro ao neutralizar {nome_real} (PID: {pid}): {e}")
        registrar_evento("neutralizacao_falha", {"pid": pid, "processo": nome_real, "motivo": "erro", "erro": str(e)})
        return False

def montar_mensagem_alerta(alerta, detalhes_proc):
    return (
        f"Atenção!\n\n"
        f"NÍVEL DE RISCO: {alerta.get('nivel', 'CRÍTICO')}\n"
        f"Foi detectada uma atividade suspeita na REDE ou MEMÓRIA do sistema.\n\n"
        f"MOTIVO: {alerta.get('mensagem', 'Detecção genérica')}\n\n"
        f"PROCESSO: {detalhes_proc.get('nome', alerta.get('processo', 'N/A'))}\n"
        f"PID: {alerta.get('pid', 'N/A')}\n"
        f"USUÁRIO: {detalhes_proc.get('usuario', alerta.get('usuario', 'N/A'))}\n"
        f"ESTADO: {alerta.get('estado', 'N/A')}\n"
        f"PORTA: {alerta.get('porta_suspeita', 'N/A')}\n"
        f"EXECUTÁVEL: {detalhes_proc.get('exe', alerta.get('executavel', 'N/A'))}\n\n"
        f"Deseja encerrar este processo suspeito agora?"
    )

def iniciar_defesa(alerta):
    """Lógica central de Defesa Ativa."""
    
    # 🛑 1. SILENCIADOR PARA ALERTAS VISUAIS (TELA)
    if alerta.get("tipo") == "ALERTA_VISAO":
        print("[AURORA] 👁️ Alerta de Visão processado silenciosamente (Enviado apenas para Telegram).")
        return True
        
    # 🛑 2. SILENCIADOR PARA ALERTAS DE QUARENTENA (ARQUIVOS)
    if alerta.get("tipo") == "ALERTA_QUARENTENA":
        print("[AURORA] 📦 Alerta de Quarentena processado silenciosamente (Arquivo já foi isolado).")
        return True

    # 3. VERIFICAÇÃO DE PID VÁLIDO PARA ALERTAS REAIS DE REDE/PROCESSO
    pid = alerta.get("pid")
    if pid is None or pid == 0:
        print("[AURORA] Alerta ignorado: Não há PID processável ou PID é 0.")
        registrar_evento("alerta_invalido", {"alerta": alerta})
        return False

    # 4. EXIBIÇÃO DA JANELA SOMENTE PARA VÍRUS REAIS (PID > 0)
    detalhes_proc = coletar_detalhes_processo(pid)
    titulo = f"AURORA EDR - ALERTA {alerta.get('nivel', 'CRÍTICO')}"
    mensagem = montar_mensagem_alerta(alerta, detalhes_proc)

    # 0x10 = ícone de erro | 0x04 = botões Sim/Não | 0x40000 = topmost
    estilo = 0x10 | 0x04 | 0x40000
    registrar_evento("alerta_exibido", {"alerta": alerta, "detalhes": detalhes_proc})

    resposta = ctypes.windll.user32.MessageBoxW(0, mensagem, titulo, estilo)

    if resposta == 6:  # Sim (Usuário mandou matar o vírus)
        print(f"[AURORA] Autorização confirmada para contenção do processo PID {pid}.")
        registrar_evento("autorizacao_usuario", {"pid": pid, "acao": "encerrar_processo"})
        return neutralizar_ameaca(pid, detalhes_proc.get("nome", alerta.get("processo", "desconhecido")))

    print(f"[AURORA] Ação cancelada pelo usuário para o alerta de rede.")
    registrar_evento("acao_cancelada_usuario", {"pid": pid})
    return False