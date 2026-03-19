# memory/sqlite_store.py
import sqlite3
from config.settings import DB_PATH
from llm.prompt_builder import INSTRUCAO_SISTEMA

def init_db():
    conn = sqlite3.connect(DB_PATH, timeout=20, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS historico (id_interacao INTEGER PRIMARY KEY AUTOINCREMENT, mensagem_usuario TEXT, resposta_aurora TEXT, data_hora DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS relatorios_vuln (id_relatorio INTEGER PRIMARY KEY AUTOINCREMENT, alvo TEXT, tipo_vulnerabilidade TEXT, descricao TEXT, data_hora DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS memoria_contexto_longo (id_memoria INTEGER PRIMARY KEY AUTOINCREMENT, texto_interacao TEXT, vetor_json TEXT, data_hora DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS base_conhecimento_rag (
        id_chunk INTEGER PRIMARY KEY AUTOINCREMENT, origem TEXT, categoria TEXT, caminho_arquivo TEXT, conteudo_texto TEXT, vetor_json TEXT, hash_chunk TEXT, data_hora DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS knowledge_catalog (
        id_item INTEGER PRIMARY KEY AUTOINCREMENT, fonte TEXT, external_id TEXT, titulo TEXT, autores TEXT, ano INTEGER, idioma TEXT, categoria TEXT, pagina_url TEXT, download_url TEXT, formato TEXT, status TEXT DEFAULT 'catalogado', hash_unico TEXT UNIQUE, data_hora DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS knowledge_jobs (
        id_job INTEGER PRIMARY KEY AUTOINCREMENT, termo_busca TEXT, categoria TEXT, status TEXT DEFAULT 'pendente', data_hora DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS knowledge_topics (
        id_topic INTEGER PRIMARY KEY AUTOINCREMENT, termo TEXT UNIQUE, categoria TEXT DEFAULT 'livros', ativo INTEGER DEFAULT 1, data_hora DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        email TEXT,
        data_registro DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    temas_padrao = [("ethical hacking", "livros"), ("python programming", "livros"), ("cyber security", "livros"), ("linux administration", "livros"), ("machine learning", "livros"), ("cryptography", "livros")]
    for termo, categoria in temas_padrao:
        try: cursor.execute("INSERT OR IGNORE INTO knowledge_topics (termo, categoria, ativo) VALUES (?, ?, 1)", (termo, categoria))
        except: pass
    conn.commit()
    conn.close()

def salvar_interacao_bd(usuario, aurora):
    try:
        conn = sqlite3.connect(DB_PATH, timeout=20, check_same_thread=False)
        conn.cursor().execute("INSERT INTO historico (mensagem_usuario, resposta_aurora) VALUES (?,?)", (usuario, aurora))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Erro BD: {e}")

def obter_historico_para_ia(limite=12):
    historico = [{"role": "system", "content": INSTRUCAO_SISTEMA}]
    try:
        conn = sqlite3.connect(DB_PATH, timeout=20, check_same_thread=False)
        linhas = conn.cursor().execute("SELECT mensagem_usuario, resposta_aurora FROM historico ORDER BY id_interacao DESC LIMIT ?", (limite,)).fetchall()
        conn.close()
        for u, a in reversed(linhas):
            historico.append({"role": "user", "content": str(u)})
            historico.append({"role": "assistant", "content": str(a)})
    except: pass
    return historico