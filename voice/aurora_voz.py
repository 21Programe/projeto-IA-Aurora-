import asyncio
import edge_tts
import os
import sys
import time

VOICE = "pt-BR-FranciscaNeural" 

async def gerar_audio(texto):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Cria um nome de arquivo ÚNICO baseado nos milissegundos atuais
    nome_arquivo = f"aurora_{int(time.time() * 1000)}.mp3"
    caminho_final_mp3 = os.path.join(script_dir, nome_arquivo)
    
    try:
        communicate = edge_tts.Communicate(texto, VOICE)
        await communicate.save(caminho_final_mp3)
        # Cospe o caminho exato para o C# ou GUI pegar
        print(caminho_final_mp3)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        mensagem = " ".join(sys.argv[1:])
        asyncio.run(gerar_audio(mensagem))