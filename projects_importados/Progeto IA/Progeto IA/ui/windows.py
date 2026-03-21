# ui/windows.py
import customtkinter as ctk
from tools.code_executor import sandbox_tester

class SandboxWindow(ctk.CTkToplevel):
    def __init__(self, parent, orchestrator, log_callback):
        super().__init__(parent)
        self.title("🧪 Sandbox Code Injector")
        self.geometry("700x500")
        self.configure(fg_color="#000000")
        
        # Guardamos as referências ao motor principal
        self.orchestrator = orchestrator
        self.log_callback = log_callback

        ctrl_frame = ctk.CTkFrame(self, fg_color="transparent")
        ctrl_frame.pack(fill="x", padx=20, pady=(10, 0))
        
        ctk.CTkLabel(ctrl_frame, text="Motor:", text_color="#cc00ff", font=("Consolas", 14)).pack(side="left")
        
        self.combo_lang = ctk.CTkComboBox(ctrl_frame, values=["python", "javascript", "shell", "sql"], fg_color="#0a0c10", text_color="#39ff14", border_color="#cc00ff", width=150)
        self.combo_lang.pack(side="left", padx=10)
        self.combo_lang.set("python")
        
        self.txt_code = ctk.CTkTextbox(self, font=("Consolas", 14), fg_color="#0a0c10", text_color="#ffffff", border_color="#cc00ff", border_width=1)
        self.txt_code.pack(expand=True, fill="both", padx=20, pady=10)

        btn_run = ctk.CTkButton(self, text="[ EXECUTAR PAYLOAD ]", fg_color="transparent", border_color="#cc00ff", border_width=2, text_color="#cc00ff", hover_color="#330033", command=self.executar)
        btn_run.pack(pady=10)

    def executar(self):
        self.log_callback("Submetendo script ao Sandbox Tester...", "SISTEMA")
        codigo_extraido = self.txt_code.get("1.0", "end-1c")
        linguagem_extraida = self.combo_lang.get()
        
        # Envia a execução para o orquestrador (Thread em background)
        self.orchestrator.submit_job(
            "SandboxExec", 
            lambda c=codigo_extraido, l=linguagem_extraida: self.log_callback(sandbox_tester.test_code(c, l), "SISTEMA")
        )
        self.destroy()