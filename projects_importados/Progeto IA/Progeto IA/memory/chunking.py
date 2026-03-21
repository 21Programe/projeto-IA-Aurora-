# memory/chunking.py
import re

class DocumentChunker:
    @staticmethod
    def quebrar_em_chunks(texto, tamanho=900, sobreposicao=150):
        # Limpa o texto primeiro
        texto = re.sub(r"[ \t]+", " ", re.sub(r"\n{3,}", "\n\n", (texto or "").strip()))
        chunks, inicio = [], 0
        
        # Despedaça mantendo contexto (sobreposição)
        while inicio < len(texto):
            chunk = texto[inicio:inicio+tamanho].strip()
            if len(chunk) > 40: chunks.append(chunk)
            inicio += max(1, tamanho - sobreposicao)
            
        return chunks