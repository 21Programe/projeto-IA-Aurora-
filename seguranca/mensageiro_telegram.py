import os
import threading

import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()


def disparar_api_telegram(texto):
    """Envia um alerta para o Telegram usando credenciais do ambiente."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("[MENSAGEIRO] Telegram desativado: credenciais não configuradas.")
        return

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": texto,
            "parse_mode": "Markdown",
        }
        resposta = requests.post(url, json=payload, timeout=10)
        if resposta.status_code == 200:
            print("[MENSAGEIRO] Alerta Telegram enviado.")
        else:
            print(f"[MENSAGEIRO] Falha no Telegram: HTTP {resposta.status_code}")
    except requests.RequestException as exc:
        print(f"[MENSAGEIRO] Erro de conexão com Telegram: {exc}")


def enviar_alerta_telegram(alerta):
    """Formata o alerta e envia em segundo plano."""
    if alerta.get("tipo") == "ALERTA_QUARENTENA":
        texto = (
            f"🚨 *AURORA EDR - QUARENTENA {alerta.get('nivel', 'ALTO')}* 🚨\n\n"
            f"Arquivo Suspeito Interceptado!\n\n"
            f"📦 *Arquivo:* `{alerta.get('nome_arquivo', 'N/A')}`\n"
            f"⚠️ *Motivo:* `{alerta.get('motivo', 'N/A')}`\n"
            f"🦠 *Assinatura:* `{alerta.get('assinatura', 'N/A')}`\n"
            f"🔒 *Status:* `{alerta.get('estado', 'N/A')}`\n"
            f"🛡️ *SHA256:* `{alerta.get('sha256', 'N/A')[:16]}...`\n\n"
            f"Aguardando ordens no monitor principal."
        )
    else:
        texto = (
            f"🚨 *AURORA EDR - ALERTA {alerta.get('nivel', 'CRÍTICO')}* 🚨\n\n"
            f"Comandante, interceptei uma ameaça!\n\n"
            f"📝 *Detalhe:* `{alerta.get('mensagem', 'Atividade Suspeita')}`\n"
            f"🦠 *Processo:* `{alerta.get('processo', 'N/A')}` (PID: {alerta.get('pid', 'N/A')})\n"
            f"👤 *Usuário:* `{alerta.get('usuario', 'N/A')}`\n"
            f"🚪 *Porta/Estado:* `{alerta.get('porta_suspeita', 'N/A')}` ({alerta.get('estado', 'N/A')})\n"
            f"📍 *IP Remoto:* `{alerta.get('ip_remoto', 'N/A')}`\n"
            f"📂 *Path:* `{alerta.get('executavel', 'N/A')}`\n\n"
            f"Aguardando ordens."
        )

    threading.Thread(
        target=disparar_api_telegram,
        args=(texto,),
        daemon=True,
    ).start()
