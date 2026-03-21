# memory/contextual_memory.py
import json
import sqlite3
import numpy as np
import faiss
from config.settings import DB_PATH

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