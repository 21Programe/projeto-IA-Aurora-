# services/sentinel.py
import os
import time
import gc
import ctypes
import threading
import psutil
import subprocess

class SystemSentinel:
    def __init__(self, orchestrator, threshold_ram=85, threshold_cpu=90, threshold_gpu_temp=82):
        self.orchestrator = orchestrator
        self.threshold_ram = threshold_ram
        self.threshold_cpu = threshold_cpu
        self.threshold_gpu_temp = threshold_gpu_temp
        threading.Thread(target=self.monitor_loop, daemon=True).start()

    def obter_dados_gpu(self):
        try:
            flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            res = subprocess.check_output(
                ['nvidia-smi', '--query-gpu=utilization.gpu,temperature.gpu,memory.used,memory.total', '--format=csv,noheader,nounits'], 
                encoding='utf-8', 
                creationflags=flags
            )
            util, temp, mem_used, mem_total = map(float, res.strip().split(', '))
            return util, temp, (mem_used / mem_total) * 100
        except Exception: 
            return 0, 0, 0

    def monitor_loop(self):
        psutil.cpu_percent(interval=None)
        while True:
            time.sleep(15)
            # 1. Defesa da RAM do Sistema
            if psutil.virtual_memory().percent > self.threshold_ram:
                gc.collect()
                if os.name == "nt":
                    try: 
                        ctypes.windll.psapi.EmptyWorkingSet(ctypes.windll.kernel32.GetCurrentProcess())
                    except: 
                        pass
            
            # 2. Defesa Térmica e VRAM da Placa de Vídeo
            util, temp, vram_perc = self.obter_dados_gpu()
            if temp > self.threshold_gpu_temp:
                self.orchestrator.message_queue.put(("SISTEMA", f"🔥 ALERTA TÉRMICO CRÍTICO: GPU atingiu {temp}°C! Risco de dano físico."))
            
           # if vram_perc > 92.0:
              #  self.orchestrator.message_queue.put(("SISTEMA", f"⚠️ ALERTA DE VRAM: Memória da GPU quase cheia ({vram_perc:.1f}%). Possível gargalo no LLM."))

            # 3. Limpeza de processos falhos no Orquestrador
            failed_jobs = [jid for jid, info in self.orchestrator.active_jobs.items() if info["status"] == "FAILED"]
            for jid in failed_jobs: 
                del self.orchestrator.active_jobs[jid]