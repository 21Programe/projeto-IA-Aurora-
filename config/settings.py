import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Raiz do projeto: independente do computador onde o repositório foi clonado.
BASE_DIR = Path(__file__).resolve().parent.parent

DIRS = {
    "sandbox": BASE_DIR / "sandbox",
    "memoria": BASE_DIR / "memoria",
    "rag": BASE_DIR / "rag",
    "logs": BASE_DIR / "logs",
    "aprovados": BASE_DIR / "aprovados",
    "knowledge": BASE_DIR / "knowledge",
    "knowledge_cache": BASE_DIR / "knowledge_cache",
    "knowledge_catalog": BASE_DIR / "knowledge_catalog",
}

KNOWLEDGE_SUBDIRS = {
    "livros": DIRS["knowledge"] / "livros",
    "artigos": DIRS["knowledge"] / "artigos",
    "codigos": DIRS["knowledge"] / "codigos",
    "manuais": DIRS["knowledge"] / "manuais",
    "exploits": DIRS["knowledge"] / "exploits",
}

DB_PATH = DIRS["memoria"] / "aurora_memory.db"

CAMINHO_MODELO_LLM = os.getenv(
    "LLM_MODEL_PATH",
    str(BASE_DIR / "modelos" / "modelo.gguf"),
)
CAMINHO_MODELO_VISAO = os.getenv(
    "VISION_MODEL_PATH",
    str(BASE_DIR / "modelos" / "vision.gguf"),
)
CAMINHO_PROJETOR_VISAO = os.getenv(
    "VISION_PROJECTOR_PATH",
    str(BASE_DIR / "modelos" / "vision-mmproj.gguf"),
)


def bootstrap_directories():
    for path in DIRS.values():
        Path(path).mkdir(parents=True, exist_ok=True)

    for path in KNOWLEDGE_SUBDIRS.values():
        Path(path).mkdir(parents=True, exist_ok=True)
