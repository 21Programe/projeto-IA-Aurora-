import os
import json
from pathlib import Path
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from app_builder.project_generator import ProjectGenerator

router = APIRouter(prefix="/builder")
generator = None

# Força o caminho a ser ONDE O TERMINAL ESTÁ RODANDO (ex: C:\Progeto IA)
CURRENT_DIR = Path(os.getcwd())
PROJECTS_ROOT = CURRENT_DIR / "aurora_projects"

@router.get("/preview/{project_name}/{file_path:path}")
async def serve_preview(project_name: str, file_path: str):
    full_path = PROJECTS_ROOT / project_name / file_path
    print(f"\n==================================================")
    print(f"🔍 [NAVEGADOR PEDIU O ARQUIVO]: {full_path}")
    print(f"📂 A pasta existe? {full_path.parent.exists()}")
    print(f"📄 O arquivo existe? {full_path.exists()}")
    print(f"==================================================\n")
    
    if full_path.exists() and full_path.is_file():
        return FileResponse(full_path)
        
    # O SEGREDO: Agora o erro diz EXATAMENTE onde tentou procurar!
    return {"error": f"Arquivo não encontrado. Eu procurei exatamente aqui: {full_path}"}

@router.websocket("/ws")
async def builder_ws(websocket: WebSocket):
    global generator
    if generator is None:
        generator = ProjectGenerator()

    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            request = json.loads(data)

            await websocket.send_json({"type": "status", "data": {"message": "A ligar os motores da Aurora..."}})

            # A IA pensa e gera o código
            response = await generator.create_from_prompt(request.get("prompt", ""))

            # 🚨 FORÇA BRUTA: O próprio servidor grava o ficheiro para garantir!
            project_dir = PROJECTS_ROOT / response.project_name
            project_dir.mkdir(parents=True, exist_ok=True)
            
            for file_data in response.files:
                file_path = project_dir / file_data.path
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(file_data.content)
                print(f"💾 [FORÇADO] Ficheiro gravado com sucesso em: {file_path}")

            # Manda o link para o frontend
            preview_url = f"http://localhost:8000/builder/preview/{response.project_name}/index.html"
            await websocket.send_json({"type": "preview_ready", "data": {"url": preview_url}})
            await websocket.send_json({"type": "status", "data": {"message": "Construção concluída com sucesso!", "done": True}})
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[ERRO CRÍTICO NO WEBSOCKET]: {e}")