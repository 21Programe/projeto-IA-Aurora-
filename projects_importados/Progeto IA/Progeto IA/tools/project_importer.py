import zipfile
import os
import shutil
from pathlib import Path

class ProjectImporter:
    def __init__(self):
        # Cria a pasta blindada na raiz do seu projeto
        self.pasta_base = Path("projects_importados")
        self.pasta_base.mkdir(exist_ok=True)
        
        # Lista negra absoluta (O que a Aurora NÃO deve ler)
        self.lixo = {
            '.venv', 'node_modules', '__pycache__', 
            '.git', '.vscode', '.idea', 'dist', 'build', 
            '__MACOSX', '.env'
        }

    def extrair_zip(self, caminho_zip):
        if not os.path.exists(caminho_zip):
            return f"[ERRO] Arquivo não encontrado: {caminho_zip}"

        nome_projeto = Path(caminho_zip).stem
        destino = self.pasta_base / nome_projeto
        
        # Se a pasta já existir, aplica "Scorched Earth" nela e cria de novo
        if destino.exists():
            shutil.rmtree(destino)
            
        arquivos_extraidos = 0
            
        try:
            with zipfile.ZipFile(caminho_zip, 'r') as zip_ref:
                for item in zip_ref.namelist():
                    # Verifica se o caminho contém alguma pasta da lista negra
                    partes_caminho = set(Path(item).parts)
                    if not (partes_caminho & self.lixo):
                        zip_ref.extract(item, path=destino)
                        arquivos_extraidos += 1
                        
            return f"[SUCESSO] Projeto '{nome_projeto}' extraído! {arquivos_extraidos} arquivos limpos em: {destino}"
            
        except Exception as e:
            return f"[ERRO CRÍTICO] Falha ao extrair ZIP: {str(e)}"