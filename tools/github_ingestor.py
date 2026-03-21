import os
import subprocess

def extrair_repositorio(url_github):
    """
    Clona um repositório alvo diretamente para a pasta 'projects_importados' da Aurora.
    """
    print(f"\n[MÓDULO DE INGESTÃO] Iniciando extração tática de: {url_github}")
    
    # Aponta para a pasta raiz do seu projeto (onde ficam os projetos importados)
    # os.getcwd() pega a pasta atual onde a Aurora está rodando
    pasta_base = os.getcwd() 
    pasta_destino = os.path.join(pasta_base, "projects_importados")
    
    # Garante que a pasta existe
    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)
        print("[SISTEMA] Diretório 'projects_importados' criado/verificado.")

    # Pega o nome do projeto (ex: de https://github.com/user/sqlmap.git vira sqlmap)
    nome_repo = url_github.split("/")[-1].replace(".git", "")
    caminho_final = os.path.join(pasta_destino, nome_repo)
    
    # Verifica se a Aurora já clonou isso antes
    if os.path.exists(caminho_final):
        print(f"[AVISO] O alvo '{nome_repo}' já está no cofre de projetos importados.")
        return caminho_final

    # Executa o Git Clone silenciosamente
    try:
        print("[SISTEMA] Baixando arquivos do alvo... Aguarde.")
        subprocess.run(["git", "clone", url_github, caminho_final], check=True, capture_output=True)
        print(f"[SUCESSO] Repositório '{nome_repo}' isolado com sucesso na pasta 'projects_importados'!")
        return caminho_final
    except subprocess.CalledProcessError as e:
        print(f"[ERRO CRÍTICO] Falha ao extrair o alvo. Verifique o link ou sua conexão.")
        return None