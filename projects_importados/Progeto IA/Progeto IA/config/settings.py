# config/settings.py
import os
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env (se existir)
load_dotenv()

# Define a raiz do projeto (C:\Progeto IA)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

DIRS = {
    "sandbox": os.path.join(BASE_DIR, "sandbox"),
    "memoria": os.path.join(BASE_DIR, "memoria"),
    "rag": os.path.join(BASE_DIR, "rag"),
    "logs": os.path.join(BASE_DIR, "logs"),
    "aprovados": os.path.join(BASE_DIR, "aprovados"),
    "knowledge": os.path.join(BASE_DIR, "knowledge"),
    "knowledge_cache": os.path.join(BASE_DIR, "knowledge_cache"),
    "knowledge_catalog": os.path.join(BASE_DIR, "knowledge_catalog"),
}

KNOWLEDGE_SUBDIRS = {
    "livros": os.path.join(DIRS["knowledge"], "livros"),
    "artigos": os.path.join(DIRS["knowledge"], "artigos"),
    "codigos": os.path.join(DIRS["knowledge"], "codigos"),
    "manuais": os.path.join(DIRS["knowledge"], "manuais"),
    "exploits": os.path.join(DIRS["knowledge"], "exploits")
}

DB_PATH = os.path.join(DIRS["memoria"], "aurora_memory.db")

# Ajuste aqui para o caminho exato onde estão os seus arquivos GGUF na sua máquina
CAMINHO_MODELO_LLM = os.getenv("LLM_MODEL_PATH", r"C:\IA_Aurora\modelos\Meta-Llama-3-8B-Instruct-Q4_K_M.gguf")
CAMINHO_MODELO_VISAO = os.getenv("VISION_MODEL_PATH", r"C:\IA_Aurora\modelos\moondream2-text-model-f16.gguf")
CAMINHO_PROJETOR_VISAO = os.getenv("VISION_PROJECTOR_PATH", r"C:\IA_Aurora\modelos\moondream2-mmproj-f16.gguf")

def bootstrap_directories():
    for d in DIRS.values():
        os.makedirs(d, exist_ok=True)
    for d in KNOWLEDGE_SUBDIRS.values():
        os.makedirs(d, exist_ok=True)