# services/scheduler.py
import time
import threading
import sqlite3
import requests
import re
import os
import hashlib
from urllib.parse import quote_plus
import xml.etree.ElementTree as ET
from config.settings import DB_PATH, KNOWLEDGE_SUBDIRS

def sha256_str(valor): 
    return hashlib.sha256(valor.encode("utf-8", errors="ignore")).hexdigest()

def baixar_arquivo(url, destino, timeout=60):
    headers = {"User-Agent": "AuroraIA/1.0"}
    # Remove qualquer espaço ou caractere estranho da URL antes de baixar
    url_limpa = url.strip()
    with requests.get(url_limpa, headers=headers, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        with open(destino, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk: f.write(chunk)

class AutoKnowledgeIngestor:
    def __init__(self, rag_manager, callback=None):
        self.rag = rag_manager
        self.callback = callback
        self.running = False
        self.interval_hours = 12
        
        self.default_terms = [
            "cyber security", "ethical hacking", "computer networks", "cryptography", "information security",
            "python programming", "javascript", "software engineering", "data structures", "algorithms", "c++ programming",
            "linux administration", "devops", "cloud computing", "system administration", "operating systems",
            "sql database", "machine learning", "data science", "artificial intelligence", "relational databases",
            "web development", "software architecture", "html css", "backend development"
        ]

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
        except Exception as e:
            self.log(f"Falha ao salvar catálogo: {e}")

    def buscar_arxiv(self, termo):
        try:
            termo_fmt = quote_plus(termo)
            # URL limpa e sem chance de erro de formatação
            base_url = "export.arxiv.org/api/query?search_query=all:"
            url = f"http://{base_url}{termo_fmt}&start=0&max_results=5"
            
            # REMOVE QUALQUER CARACTERE DE FORMATAÇÃO QUE SOBROU
            url = url.replace("[", "").replace("]", "").split(")")[0]
            
            r = requests.get(url, timeout=15)
            # ... resto do código (extração do XML)
        except Exception as e:
            self.log(f"Falha arXiv: {e}")

    def buscar_openlibrary(self, termo):
        try:
            termo_fmt = quote_plus(termo)
            url = f"https://openlibrary.org/search.json?q={termo_fmt}&limit=10"
            url = url.replace("[", "").replace("]", "").split(")")[0]
            
            r = requests.get(url, timeout=15)
            # ... resto do código (extração do JSON)
        except Exception as e:
            self.log(f"Falha Open Library: {e}")
        try:
            termo_fmt = quote_plus(termo)
            url = "https://" + "openlibrary.org/search.json?q=" + termo_fmt + "&limit=10"
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                dados = r.json()
                for doc in dados.get("docs", []):
                    if doc.get("public_scan_b") and "key" in doc:
                        capa = doc.get('cover_edition_key', '')
                        dl_url = "https://" + "archive.org/download/" + f"{capa}/{capa}.pdf" if capa else ""
                        pagina = "https://" + "openlibrary.org" + doc['key']
                        if dl_url:
                            self.salvar_catalogo({
                                "fonte": "openlibrary", "external_id": doc["key"], 
                                "titulo": doc.get("title", "Sem título"), 
                                "autores": ", ".join(doc.get("author_name", [])), 
                                "ano": doc.get("first_publish_year", 0), "idioma": "en", 
                                "categoria": "livros", "pagina_url": pagina, 
                                "download_url": dl_url, "formato": "pdf"
                            })
        except Exception as e:
            self.log(f"Falha Open Library: {e}")

    def buscar_gutendex(self, termo):
        try:
            termo_fmt = quote_plus(termo)
            url = "https://" + "gutendex.com/books?search=" + termo_fmt
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                dados = r.json()
                for livro in dados.get("results", []):
                    formats = livro.get("formats", {})
                    dl_url = formats.get("application/epub+zip") or formats.get("text/plain; charset=us-ascii")
                    if dl_url:
                        formato = "epub" if "epub" in dl_url else "txt"
                        pagina = "https://" + "gutenberg.org/ebooks/" + str(livro['id'])
                        self.salvar_catalogo({
                            "fonte": "gutendex", "external_id": str(livro["id"]), 
                            "titulo": livro.get("title", "Sem título"), 
                            "autores": ", ".join([a.get("name", "") for a in livro.get("authors", [])]), 
                            "ano": 0, "idioma": livro.get("languages", ["en"])[0], 
                            "categoria": "livros", "pagina_url": pagina, 
                            "download_url": dl_url, "formato": formato
                        })
        except Exception as e:
            self.log(f"Falha Gutendex: {e}")

    def baixar_e_ingerir_catalogados_abertos(self):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=20, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("SELECT id_item, download_url, formato, categoria, fonte FROM knowledge_catalog WHERE status = 'catalogado' LIMIT 3")
            pendentes = cursor.fetchall()
            
            for item in pendentes:
                id_item, url, formato, categoria, fonte = item
                if not url: continue
                
                nome_arquivo = f"{fonte}_{id_item}_{sha256_str(url)[:8]}.{formato}"
                pasta_destino = KNOWLEDGE_SUBDIRS.get(categoria, KNOWLEDGE_SUBDIRS["manuais"])
                caminho_completo = os.path.join(pasta_destino, nome_arquivo)
                
                self.log(f"Baixando artefato tático: {nome_arquivo}")
                try:
                    baixar_arquivo(url, caminho_completo)
                    if self.rag:
                        self.rag.ingerir_arquivo_generico(caminho_completo, categoria, fonte, self.callback)
                    
                    cursor.execute("UPDATE knowledge_catalog SET status = 'ingerido' WHERE id_item = ?", (id_item,))
                    conn.commit()
                except Exception as e:
                    self.log(f"Falha ao processar {url}: {e}")
                    cursor.execute("UPDATE knowledge_catalog SET status = 'erro' WHERE id_item = ?", (id_item,))
                    conn.commit()
            conn.close()
        except Exception as e:
            self.log(f"Erro no ciclo de ingestão: {e}")

    def rodada_diaria_temas(self, limite=1):
        import random
        temas = random.sample(self.default_terms, min(limite, len(self.default_terms)))
        for termo in temas:
            self.log(f"OSINT Ativo - Buscando tema: {termo}")
            self.buscar_arxiv(termo)
            self.buscar_openlibrary(termo)
            self.buscar_gutendex(termo)
            time.sleep(2)

    def processar_jobs_pendentes(self):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=20, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("SELECT id_job, termo_busca FROM knowledge_jobs WHERE status = 'pendente'")
            jobs = cursor.fetchall()
            for id_job, termo in jobs:
                self.log(f"Processando Diretriz Manual: {termo}")
                self.buscar_arxiv(termo)
                self.buscar_openlibrary(termo)
                self.buscar_gutendex(termo)
                cursor.execute("UPDATE knowledge_jobs SET status = 'concluido' WHERE id_job = ?", (id_job,))
                conn.commit()
            conn.close()
        except Exception as e:
            self.log(f"Erro ao processar jobs: {e}")

    def rodada_descoberta(self, termos=None):
        self.log("Iniciando varredura OSINT de Conhecimento...")
        self.processar_jobs_pendentes()
        
        if termos:
            for termo in termos:
                self.buscar_arxiv(termo)
                self.buscar_openlibrary(termo)
                self.buscar_gutendex(termo)
        else:
            self.rodada_diaria_temas()
            
        self.baixar_e_ingerir_catalogados_abertos()
        self.log("Varredura OSINT finalizada.")

    def iniciar_loop(self, interval_hours=12, termos=None):
        if self.running: return
        self.interval_hours = interval_hours
        self.running = True
        def loop():
            self.log("Motor Sentinela OSINT ativado.")
            while self.running:
                try: self.rodada_descoberta(termos=termos)
                except Exception as e: self.log(f"Falha no ciclo automático: {e}")
                time.sleep(max(1, self.interval_hours) * 3600)
        threading.Thread(target=loop, daemon=True).start()

    def parar_loop(self):
        self.running = False
        self.log("Motor Sentinela OSINT desativado.")

    def adicionar_job(self, termo_busca, categoria="livros"):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=20, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO knowledge_jobs (termo_busca, categoria, status) VALUES (?, ?, 'pendente')", (termo_busca, categoria))
            conn.commit()
            conn.close()
            self.log(f"Diretriz de busca adicionada: {termo_busca}")
        except Exception as e:
            self.log(f"Falha ao adicionar diretriz: {e}")