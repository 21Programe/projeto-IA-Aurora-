import os
import time
import shutil
from datetime import datetime, timedelta
from barramento_eventos import fila_alertas

# ==============================
# CONFIGURAÇÃO DE LOGÍSTICA
# ==============================
PASTA_QUARENTENA = r"C:\Progeto IA\seguranca\prisao_quarentena"
DIAS_PARA_EXPIRAR = 7  # Tempo de custódia antes da execução (deleção)
TAMANHO_MAX_PASTA_MB = 500  # Limite de segurança para não lotar o disco

def obter_tamanho_pasta(caminho):
    total = 0
    with os.scandir(caminho) as it:
        for entrada in it:
            if entrada.is_file():
                total += entrada.stat().size
    return total / (1024 * 1024)

def executar_limpeza_automatica():
    print(f"\n[MANUTENÇÃO] 🧹 Iniciando varredura na Prisão de Quarentena...")
    
    agora = time.time()
    limite_tempo = agora - (DIAS_PARA_EXPIRAR * 86400)
    arquivos_removidos = 0

    if not os.path.exists(PASTA_QUARENTENA):
        print("[ERRO] Pasta de quarentena não encontrada.")
        return

    # 1. Limpeza por Tempo (Arquivos expirados)
    for arquivo in os.listdir(PASTA_QUARENTENA):
        caminho_completo = os.path.join(PASTA_QUARENTENA, arquivo)
        status_arquivo = os.stat(caminho_completo)

        if status_arquivo.st_mtime < limite_tempo:
            try:
                os.remove(caminho_completo)
                arquivos_removidos += 1
                print(f"[LIMPEZA] 🗑️ Arquivo expirado removido: {arquivo}")
            except Exception as e:
                print(f"[ERRO] Falha ao deletar {arquivo}: {e}")

    # 2. Limpeza por Espaço (Se a pasta passar de 500MB, deleta o mais antigo)
    tamanho_atual = obter_tamanho_pasta(PASTA_QUARENTENA)
    if tamanho_atual > TAMANHO_MAX_PASTA_MB:
        print(f"[ALERTA] Quarentena excedeu {TAMANHO_MAX_PASTA_MB}MB. Removendo excedentes...")
        # Ordena por data de modificação (mais antigo primeiro)
        arquivos = [os.path.join(PASTA_QUARENTENA, f) for f in os.listdir(PASTA_QUARENTENA)]
        arquivos.sort(key=os.path.getmtime)
        
        while obter_tamanho_pasta(PASTA_QUARENTENA) > TAMANHO_MAX_PASTA_MB and arquivos:
            antigo = arquivos.pop(0)
            os.remove(antigo)
            arquivos_removidos += 1

    # 3. Relatório para o Comandante via Telegram
    if arquivos_removidos > 0:
        alerta = {
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "tipo": "MANUTENÇÃO_SISTEMA",
            "nivel": "INFO",
            "processo": "Modulo_Limpeza",
            "usuario": "Diego",
            "estado": "CONCLUÍDO",
            "mensagem": f"Faxina concluída na Quarentena. {arquivos_removidos} ameaças antigas foram incineradas permanentemente."
        }
        fila_alertas.put(alerta)
    else:
        print("[MANUTENÇÃO] ✅ Tudo limpo. Nenhum arquivo expirado encontrado.")

if __name__ == "__main__":
    executar_limpeza_automatica()