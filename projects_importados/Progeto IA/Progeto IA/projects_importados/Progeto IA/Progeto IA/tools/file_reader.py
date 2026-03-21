# tools/file_reader.py
from pathlib import Path
from bs4 import BeautifulSoup
import fitz

class AuroraFileReader:
    @staticmethod
    def ler_arquivo_texto(caminho):
        try:
            with open(caminho, "r", encoding="utf-8") as f: return f.read()
        except:
            try:
                with open(caminho, "r", encoding="latin-1") as f: return f.read()
            except: return ""

    @staticmethod
    def ler_pdf(caminho):
        try:
            documento = fitz.open(caminho)
            texto = [pagina.get_text("text") for pagina in documento]
            documento.close()
            return "\n".join(texto)
        except: return ""

    @staticmethod
    def ler_epub(caminho):
        try:
            from ebooklib import epub
            livro = epub.read_epub(caminho)
            partes = [BeautifulSoup(i.get_content(), "html.parser").get_text(separator=" ", strip=True) for i in livro.get_items() if i.get_type() == 9]
            return "\n\n".join(filter(None, partes))
        except: return ""

    @staticmethod
    def carregar_texto_de_arquivo(caminho):
        ext = Path(caminho).suffix.lower()
        if ext == ".pdf": return AuroraFileReader.ler_pdf(caminho)
        elif ext in {".txt", ".md", ".py", ".js", ".html", ".css", ".json"}: return AuroraFileReader.ler_arquivo_texto(caminho)
        elif ext == ".epub": return AuroraFileReader.ler_epub(caminho)
        return ""