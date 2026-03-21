import requests
import threading

# --- CONFIGURAÇÕES DO TELEGRAM ---
TOKEN = "7625411545:AAHjmJ7yEfa5b5baXxc0fQ6ceUcFQnK_2eE"
CHAT_ID = "7125751042"

def disparar_api_telegram(texto):
    """Envia o alerta para o Telegram via API Oficial em segundo plano."""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": texto,
            "parse_mode": "Markdown" # Permite usar negrito e formatação legal
        }
        
        resposta = requests.post(url, json=payload, timeout=10)
        
        if resposta.status_code == 200:
            print("\n[MENSAGEIRO] ✈️ Alerta TELEGRAM disparado com sucesso para o comandante!")
        else:
            print(f"\n[MENSAGEIRO] ⚠️ Falha ao enviar Telegram. Erro: {resposta.text}")
    except Exception as e:
        print(f"\n[MENSAGEIRO] ❌ Erro de conexão com Telegram: {e}")

def enviar_alerta_telegram(alerta):
    """Monta o pacote de dados à prova de falhas usando o método .get()"""
    
    # Se o alerta for do módulo de Quarentena, a mensagem é diferente
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
        # Padrão original para os outros alertas (Rede/Processo/Visão)
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
    
    thread_msg = threading.Thread(target=disparar_api_telegram, args=(texto,))
    thread_msg.start()
    
    