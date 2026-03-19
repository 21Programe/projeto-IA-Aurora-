# memory/vector_store.py
import os
import json
import sqlite3
import threading
import numpy as np
import faiss
import hashlib
from sentence_transformers import SentenceTransformer
from config.settings import DB_PATH
from tools.file_reader import AuroraFileReader
from memory.chunking import DocumentChunker

def sha256_str(valor): 
    return hashlib.sha256(valor.encode("utf-8", errors="ignore")).hexdigest()

print("[SENTINELA] Boot do Motor Vetorial Semântico (Multilíngue)...")
try:
    encoder_rag = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
except Exception as e:
    print(f"[SENTINELA] Falha ao carregar encoder vetorial: {e}")
    encoder_rag = None

class SubsistemaRAG:
    def __init__(self):
        self.indice_faiss, self.mapeamento_ids, self.ultimas_fontes = None, {}, []
        threading.Thread(target=self.carregar_indice_memoria_real, daemon=True).start()

    def carregar_indice_memoria_real(self):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=20, check_same_thread=False)
            linhas = conn.cursor().execute("SELECT id_chunk, conteudo_texto, vetor_json, origem, categoria, caminho_arquivo FROM base_conhecimento_rag").fetchall()
            conn.close()
            if not linhas: return
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
        except: pass

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
            texto_bruto = AuroraFileReader.carregar_texto_de_arquivo(caminho_arquivo)
            if not texto_bruto.strip(): return 0
            chunks = DocumentChunker.quebrar_em_chunks(texto_bruto)
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
        except: return 0