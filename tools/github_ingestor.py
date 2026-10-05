import os
import re
import subprocess
from urllib.parse import urlparse


GITHUB_REPO_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def _validar_url_github(url):
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc.lower() != "github.com":
        raise ValueError("A ingestão aceita somente URLs HTTPS do github.com.")

    path = parsed.path.strip("/")
    if path.endswith(".git"):
        path = path[:-4]
    if not GITHUB_REPO_PATTERN.fullmatch(path):
        raise ValueError("URL inválida. Use https://github.com/usuario/repositorio.")


def extrair_repositorio(url_github):
    """Importa um repositório público do GitHub para análise local autorizada."""
    if os.getenv("AURORA_ALLOW_REPO_INGESTION", "false").lower() != "true":
        return (
            "Ingestão de repositórios desativada. "
            "Defina AURORA_ALLOW_REPO_INGESTION=true no ambiente para habilitá-la."
        )

    try:
        _validar_url_github(url_github)
    except ValueError as exc:
        return f"[ERRO] {exc}"

    pasta_base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    pasta_destino = os.path.join(pasta_base, "projects_importados")
    os.makedirs(pasta_destino, exist_ok=True)

    nome_repo = urlparse(url_github).path.strip("/").split("/")[-1].removesuffix(".git")
    caminho_final = os.path.join(pasta_destino, nome_repo)

    if os.path.exists(caminho_final):
        return caminho_final

    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", url_github, caminho_final],
            check=True,
            capture_output=True,
            text=True,
        )
        return caminho_final
    except (subprocess.CalledProcessError, OSError):
        return "[ERRO] Não foi possível importar o repositório."
