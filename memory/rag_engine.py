# memory/rag_engine.py
import os
import re
import json
import sqlite3
import hashlib
import requests
import threading
import time
import numpy as np
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import quote_plus
import xml.etree.ElementTree as ET
from PIL import Image, ExifTags
import fitz
import faiss
from sentence_transformers import SentenceTransformer
from ebooklib import epub
from config.settings import DB_PATH, KNOWLEDGE_SUBDIRS

# Importações internas para manter a estrutura original
from memory.vector_store import SubsistemaRAG as BaseRAG
from memory.contextual_memory import SubsistemaMemoriaContextual as BaseContext

print("[SENTINELA] Boot do Motor Vetorial Semântico (Multilíngue)...")
try:
    # --- A MÁGICA ACONTECE AQUI ---
    encoder_rag = SentenceTransformer(
        'paraphrase-multilingual-MiniLM-L12-v2',
        device='cpu'  # <--- FORÇA O RAG A RODAR NA CPU E RAM NORMAL
    )
except Exception as e:
    print(f"[SENTINELA] Falha ao carregar encoder vetorial: {e}")
    encoder_rag = None

# ==========================================
# FUNÇÕES UTILITÁRIAS DE INGESTÃO
# ==========================================
def ler_arquivo_texto(caminho):
    try:
        with open(caminho, "r", encoding="utf-8") as f: return f.read()
    except:
        try:
            with open(caminho, "r", encoding="latin-1") as f: return f.read()
        except: return ""

def ler_pdf(caminho):
    try:
        documento = fitz.open(caminho)
        texto = [pagina.get_text("text") for pagina in documento]
        documento.close()
        return "\n".join(texto)
    except: return ""

def ler_epub(caminho):
    try:
        import ebooklib
        livro = epub.read_epub(caminho)
        partes = [BeautifulSoup(i.get_content(), "html.parser").get_text(separator=" ", strip=True) for i in livro.get_items() if i.get_type() == 9]
        return "\n\n".join(filter(None, partes))
    except: return ""

def carregar_texto_de_arquivo(caminho):
    ext = Path(caminho).suffix.lower()
    if ext == ".pdf": return ler_pdf(caminho)
    elif ext in {".txt", ".md", ".py", ".js", ".html", ".css", ".json"}: return ler_arquivo_texto(caminho)
    elif ext == ".epub": return ler_epub(caminho)
    return ""

def quebrar_em_chunks(texto, tamanho=900, sobreposicao=150):
    texto = re.sub(r"[ \t]+", " ", re.sub(r"\n{3,}", "\n\n", (texto or "").strip()))
    chunks, inicio = [], 0
    while inicio < len(texto):
        chunk = texto[inicio:inicio+tamanho].strip()
        if len(chunk) > 40: chunks.append(chunk)
        inicio += max(1, tamanho - sobreposicao)
    return chunks

def sha256_str(valor): 
    return hashlib.sha256(valor.encode("utf-8", errors="ignore")).hexdigest()

def baixar_arquivo(url, destino, timeout=60):
    headers = {"User-Agent": "AuroraIA/1.0"}
    with requests.get(url, headers=headers, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        with open(destino, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk: f.write(chunk)

# ==========================================
# SUBSISTEMAS DE MEMÓRIA
# ==========================================

class SubsistemaRAG:
    def __init__(self):
        self.indice_faiss, self.mapeamento_ids, self.ultimas_fontes = None, {}, []
        threading.Thread(target=self.carregar_indice_memoria_real, daemon=True).start()

    def carregar_indice_memoria_real(self):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=20, check_same_thread=False)
            linhas = conn.cursor().execute("SELECT id_chunk, conteudo_texto, vetor_json, origem, categoria, caminho_arquivo FROM base_conhecimento_rag").fetchall()
            conn.close()
            if not linhas: 
                print("[RAG] Base de conhecimento local vazia.")
                return
            
            vetores, self.mapeamento_ids = [], {}
            for i, l in enumerate(linhas):
                v = np.array(json.loads(l[2]), dtype="float32")
                if v.ndim == 1:
                    vetores.append(v)
                    self.mapeamento_ids[i] = {"conteudo": l[1], "origem": l[3] or "desconhecido", "categoria": l[4] or "geral", "caminho_arquivo": l[5] or ""}
            
            if vetores:
                matriz = np.vstack(vetores)
                self.indice_faiss = faiss.IndexFlatIP(int(matriz.shape[1]))
                self.indice_faiss.add(matriz)
                print(f"[RAG] Memória Vetorial Pronta: {len(vetores)} chunks carregados da RTX 2060.")
        except Exception as e: 
            print(f"[RAG] Erro ao carregar memória: {e}")

    def chunk_ja_existe(self, hash_chunk):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=20, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM base_conhecimento_rag WHERE hash_chunk = ? LIMIT 1", (hash_chunk,))
            existe = cursor.fetchone() is not None
            conn.close()
            return existe
        except: return False

    def gerar_vetor_embedding(self, texto):
        if encoder_rag is None or not str(texto).strip(): return None
        try: return np.array(encoder_rag.encode(str(texto), normalize_embeddings=True), dtype="float32")
        except: return None

    def recuperar_contexto(self, pergunta, limiar_top_k=3):
        try:
            if self.indice_faiss is None or self.indice_faiss.ntotal == 0: return ""
            vetor = self.gerar_vetor_embedding(pergunta)
            if vetor is None: return ""
            Distancias, Indices = self.indice_faiss.search(np.array([vetor], dtype="float32"), min(int(limiar_top_k), int(self.indice_faiss.ntotal)))
            blocos, self.ultimas_fontes = [], []
            for i, idx in enumerate(Indices[0]):
                if idx == -1: continue
                item = self.mapeamento_ids.get(int(idx))
                if not item: continue
                blocos.append(f"[FONTE: {item['origem']} | CAT: {item['categoria']}]\n{item['conteudo']}")
                nome_fonte, porc = item['origem'], max(0, min(100, int(float(Distancias[0][i]) * 100)))
                if not any(f[0] == nome_fonte for f in self.ultimas_fontes): self.ultimas_fontes.append((nome_fonte, porc))
            return "\n---\n".join(blocos)
        except: return ""

    def ingerir_arquivo_generico(self, caminho_arquivo, categoria="geral", origem="local", callback_interface=None):
        try:
            texto_bruto = carregar_texto_de_arquivo(caminho_arquivo)
            if not texto_bruto or not texto_bruto.strip(): return 0
            chunks = quebrar_em_chunks(texto_bruto)
            inseridos = 0
            conn = sqlite3.connect(DB_PATH, timeout=20, check_same_thread=False)
            cursor = conn.cursor()
            for bloco in chunks:
                hash_chunk = sha256_str(f"{caminho_arquivo}::{bloco}")
                if cursor.execute("SELECT 1 FROM base_conhecimento_rag WHERE hash_chunk = ?", (hash_chunk,)).fetchone(): continue
                vetor = self.gerar_vetor_embedding(bloco)
                if vetor is not None:
                    cursor.execute("INSERT INTO base_conhecimento_rag (origem, categoria, caminho_arquivo, conteudo_texto, vetor_json, hash_chunk) VALUES (?, ?, ?, ?, ?, ?)", (f"{origem}:{os.path.basename(caminho_arquivo)}", categoria, caminho_arquivo, bloco, json.dumps(vetor.tolist()), hash_chunk))
                    inseridos += 1
            conn.commit()
            conn.close()
            if inseridos > 0: self.carregar_indice_memoria_real()
            if callback_interface: callback_interface(f"Indexados {inseridos} chunks de {os.path.basename(caminho_arquivo)}")
            return inseridos
        except Exception as e:
            print(f"Erro na ingestão: {e}")
            return 0

class SubsistemaMemoriaContextual:
    def __init__(self, gerenciador_rag):
        self.gerenciador_rag = gerenciador_rag
        self.indice_faiss, self.mapeamento_ids = None, {}
        self.carregar_indice_memoria_longa()

    def carregar_indice_memoria_longa(self):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=20, check_same_thread=False)
            linhas = conn.cursor().execute("SELECT id_memoria, texto_interacao, vetor_json FROM memoria_contexto_longo").fetchall()
            conn.close()
            if not linhas: return
            vetores = []
            for i, l in enumerate(linhas):
                v = np.array(json.loads(l[2]), dtype="float32")
                if v.ndim == 1:
                    vetores.append(v)
                    self.mapeamento_ids[i] = l[1]
            if vetores:
                matriz = np.vstack(vetores)
                self.indice_faiss = faiss.IndexFlatIP(int(matriz.shape[1]))
                self.indice_faiss.add(matriz)
        except: pass

    def memorizar_interacao(self, usuario, aurora):
        texto = f"Usuário: '{usuario}'. Aurora: '{aurora}'."
        vetor = self.gerenciador_rag.gerar_vetor_embedding(texto)
        if vetor is not None:
            conn = sqlite3.connect(DB_PATH, timeout=20, check_same_thread=False)
            conn.cursor().execute("INSERT INTO memoria_contexto_longo (texto_interacao, vetor_json) VALUES (?,?)", (texto, json.dumps(vetor.tolist())))
            conn.commit()
            conn.close()
            self.carregar_indice_memoria_longa()

    def resgatar_lembrancas(self, pergunta, limiar_top_k=3):
        try:
            if self.indice_faiss is None or self.indice_faiss.ntotal == 0: return ""
            vetor = self.gerenciador_rag.gerar_vetor_embedding(pergunta)
            if vetor is None: return ""
            _, Indices = self.indice_faiss.search(np.array([vetor], dtype="float32"), min(int(limiar_top_k), int(self.indice_faiss.ntotal)))
            return "\n---\n".join(filter(None, [self.mapeamento_ids.get(int(idx), "") for idx in Indices[0] if idx != -1]))
        except: return ""

class AutoKnowledgeIngestor:
    def __init__(self, rag_manager, callback=None):
        self.rag = rag_manager
        self.callback = callback
        self.running = False
        self.interval_hours = 12
        self.default_terms = ["cyber security", "ethical hacking", "computer networks", "cryptography", "python programming"]

    def log(self, msg):
        if self.callback: self.callback(msg)
        print("[AUTO-KNOWLEDGE]", msg)

    def _catalog_hash(self, fonte, external_id, download_url):
        return sha256_str(f"{fonte}|{external_id}|{download_url}")

    def salvar_catalogo(self, item):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=20, check_same_thread=False)
            cursor = conn.cursor()
            hash_unico = self._catalog_hash(item.get("fonte", ""), item.get("external_id", ""), item.get("download_url", ""))
            cursor.execute("""
                INSERT OR IGNORE INTO knowledge_catalog
                (fonte, external_id, titulo, autores, ano, idioma, categoria, pagina_url, download_url, formato, status, hash_unico)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (item.get("fonte"), item.get("external_id"), item.get("titulo"), item.get("autores"), item.get("ano"), item.get("idioma"), item.get("categoria"), item.get("pagina_url"), item.get("download_url"), item.get("formato"), item.get("status", "catalogado"), hash_unico))
            conn.commit()
            conn.close()
        except Exception as e: self.log(f"Falha ao salvar catálogo: {e}")

    def buscar_openlibrary(self, termo, categoria="livros", limite=10):
        try:
            headers = {"User-Agent": "AuroraIA/1.0"}
            url = f"https://openlibrary.org/search.json?q={quote_plus(termo)}&limit={limite}"
            r = requests.get(url, headers=headers, timeout=30)
            r.raise_for_status()
            data = r.json()
            encontrados = []
            for doc in data.get("docs", []):
                work_key = doc.get("key", "")
                item = {"fonte": "openlibrary", "external_id": work_key, "titulo": doc.get("title"), "autores": ", ".join(doc.get("author_name", [])[:3]), "ano": doc.get("first_publish_year"), "idioma": ", ".join(doc.get("language", [])[:3]) if doc.get("language") else None, "categoria": categoria, "pagina_url": f"https://openlibrary.org{work_key}", "download_url": None, "formato": None, "status": "catalogado"}
                self.salvar_catalogo(item)
                encontrados.append(item)
            self.log(f"Open Library: {len(encontrados)} itens catalogados.")
            return encontrados
        except Exception as e: self.log(f"Falha Open Library: {e}"); return []

    def buscar_arxiv(self, termo, categoria="artigos", limite=5):
        try:
            url = f"http://export.arxiv.org/api/query?search_query=all:{quote_plus(termo)}&start=0&max_results={limite}"
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            root = ET.fromstring(r.text)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            encontrados = []
            for entry in root.findall('atom:entry', ns):
                titulo = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
                pdf_url = entry.find('atom:id', ns).text.replace('/abs/', '/pdf/') + ".pdf"
                item = {"fonte": "arxiv", "external_id": entry.find('atom:id', ns).text.split('/')[-1], "titulo": titulo, "autores": "Vários", "ano": entry.find('atom:published', ns).text[:4] if entry.find('atom:published', ns) is not None else None, "idioma": "en", "categoria": categoria, "pagina_url": entry.find('atom:id', ns).text, "download_url": pdf_url, "formato": "pdf", "status": "aberto"}
                self.salvar_catalogo(item)
                encontrados.append(item)
            self.log(f"arXiv: {len(encontrados)} artigos catalogados.")
            return encontrados
        except Exception as e: self.log(f"Falha arXiv: {e}"); return []

    def buscar_gutendex(self, termo, categoria="livros", limite=10):
        try:
            url = f"https://gutendex.com/books?search={quote_plus(termo)}"
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            data = r.json()
            encontrados = []
            for book in data.get("results", [])[:limite]:
                download_url = book.get("formats", {}).get("application/epub+zip")
                if not download_url: continue
                item = {"fonte": "gutendex", "external_id": str(book.get("id")), "titulo": book.get("title"), "autores": "Vários", "ano": None, "idioma": "en", "categoria": categoria, "pagina_url": f"https://www.gutenberg.org/ebooks/{book.get('id')}", "download_url": download_url, "formato": "epub", "status": "aberto"}
                self.salvar_catalogo(item)
                encontrados.append(item)
            return encontrados
        except Exception as e: self.log(f"Falha Gutendex: {e}"); return []

    # --- Métodos de ciclo e controle ---
    def carregar_temas_ativos(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            linhas = conn.cursor().execute("SELECT termo, categoria FROM knowledge_topics WHERE ativo = 1").fetchall()
            conn.close()
            return linhas
        except: return []

    def rodada_descoberta(self, termos=None):
        termos = termos or self.default_terms
        for termo in termos:
            self.buscar_openlibrary(termo)
            self.buscar_arxiv(termo)
            self.buscar_gutendex(termo)
            time.sleep(2)
        self.baixar_e_ingerir_catalogados_abertos()

    def baixar_e_ingerir_catalogados_abertos(self, limite=5):
        try:
            conn = sqlite3.connect(DB_PATH)
            itens = conn.cursor().execute("SELECT id_item, fonte, titulo, download_url, formato, categoria FROM knowledge_catalog WHERE status = 'aberto' AND download_url IS NOT NULL LIMIT ?", (limite,)).fetchall()
            conn.close()
            total = 0
            for id_item, fonte, titulo, dl_url, fmt, cat in itens:
                ext = f".{fmt}"
                destino = os.path.join(KNOWLEDGE_SUBDIRS["livros"], f"{fonte}_{id_item}{ext}")
                if not os.path.exists(destino):
                    baixar_arquivo(dl_url, destino)
                total += self.rag.ingerir_arquivo_generico(destino, cat, fonte, self.callback)
            return total
        except: return 0

# ==========================================
# INSTANCIAÇÃO GLOBAL
# ==========================================
gerenciador_rag = SubsistemaRAG()
gerenciador_memoria_longa = SubsistemaMemoriaContextual(gerenciador_rag)