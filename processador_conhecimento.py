import os
import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter

def extrair_conhecimento_pdf(caminho_arquivo):
    nome_base = os.path.basename(caminho_arquivo)
    print(f"\n[KNOWLEDGE] 📖 Lendo: {nome_base}")
    
    texto_completo = ""
    try:
        doc = fitz.open(caminho_arquivo)
        for pagina in doc:
            texto_completo += pagina.get_text()
        doc.close()

        if not texto_completo.strip():
            print(f"[AVISO] ⚠️ {nome_base} parece não ter texto legível (imagem).")
            return 0

        # Configuração do Divisor (Chunking) - Ajustado para o cérebro da Aurora
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=80
        )
        
        chunks = splitter.split_text(texto_completo)
        return len(chunks)

    except Exception as e:
        print(f"[ERRO] Falha ao processar {nome_base}: {e}")
        return 0

# ==============================
# BLOCO DE EXECUÇÃO AJUSTADO
# ==============================
if __name__ == "__main__":
    # COORDENADA ATUALIZADA:
    diretorio_base = r"C:\Progeto IA\knowledge\livros"
    total_chunks = 0
    
    print("=== 🛡️ INICIANDO INDEXAÇÃO DE CONHECIMENTO - AURORA V2.5 ===")
    
    # Busca arquivos de 11 a 15
    for i in range(11, 16):
        nome_pdf = f"arxiv_{i}.pdf"
        caminho_full = os.path.join(diretorio_base, nome_pdf)
        
        if os.path.exists(caminho_full):
            n_chunks = extrair_conhecimento_pdf(caminho_full)
            if n_chunks > 0:
                print(f"[SUCESSO] ✅ {nome_pdf}: {n_chunks} fragmentos gerados.")
                total_chunks += n_chunks
        else:
            print(f"[ERRO] ❌ Arquivo não localizado em: {caminho_full}")

    print(f"\n=== 📊 RESUMO: {total_chunks} fragmentos prontos para a RTX 2060! ===")