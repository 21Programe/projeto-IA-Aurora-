# ui/components.py
import re
import customtkinter as ctk

class TechStackPanel(ctk.CTkFrame):
    def __init__(self, parent, dados_radar):
        # Herda as configurações visuais do frame original
        super().__init__(parent, fg_color="#0a0c10", border_width=1, border_color="#cc00ff")
        titulo_painel, stack_data = dados_radar
        
        lbl_titulo = ctk.CTkLabel(self, text=titulo_painel, font=("Consolas", 14, "bold"), text_color="#cc00ff")
        lbl_titulo.pack(pady=(10, 5))
        
        lbl_sub = ctk.CTkLabel(self, text="Composição analítica sugerida para a sua diretriz:", font=("Consolas", 11), text_color="#a9b1d6")
        lbl_sub.pack(pady=(0, 15))

        cores_tech = {
            "HTML5": "#e34f26", "CSS3": "#264de4", "JavaScript": "#f7df1e", "Python": "#3776ab", "SQL/DB": "#00758f", "Shell/Ops": "#4eaa25",
            "Recon/OSINT": "#00ffcc", "Exploitation": "#ff0033", "Networking": "#ff9900", "Cryptography": "#cc00ff", "Payload Crafting": "#ff3399",
            "NLP/Tokenização": "#00aaff", "Álgebra Linear": "#ffcc00", "Estatística": "#ff5500", "Machine Learning": "#ccff00", "Eng. de Dados": "#00ff66"
        }

        container_barras = ctk.CTkFrame(self, fg_color="transparent")
        container_barras.pack(fill="x", padx=20, pady=(0, 15))

        for tech, porc in stack_data.items():
            linha = ctk.CTkFrame(container_barras, fg_color="transparent")
            linha.pack(fill="x", pady=4)
            cor = cores_tech.get(tech, "#00ffcc") 
            
            ctk.CTkLabel(linha, text=f"{tech}", font=("Consolas", 11, "bold"), text_color=cor, width=150, anchor="w").pack(side="left")
            bar = ctk.CTkProgressBar(linha, height=10, fg_color="#1a1a1a", progress_color=cor)
            bar.pack(side="left", fill="x", expand=True, padx=10)
            bar.set(porc / 100.0)
            ctk.CTkLabel(linha, text=f"{porc}%", font=("Consolas", 12), text_color="#ffffff", width=40, anchor="e").pack(side="right")


class FontesRAGPanel(ctk.CTkFrame):
    def __init__(self, parent, fontes_detectadas):
        super().__init__(parent, fg_color="#000000")
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="🔍 RASTREAMENTO DE FONTES (RAG)", font=("Consolas", 16, "bold"), text_color="#ff0033").grid(row=0, column=0, pady=(10, 30))

        for i, (nome, porc) in enumerate(fontes_detectadas[:3]): 
            item_frame = ctk.CTkFrame(self, fg_color="transparent")
            item_frame.grid(row=i+1, column=0, pady=10)

            nome_limpo = re.sub(r'^(arxiv|openlibrary|gutendex)_\d+_', '', nome)
            nome_display = (nome_limpo[:45] + '...') if len(nome_limpo) > 45 else nome_limpo
            ctk.CTkLabel(item_frame, text=nome_display.upper(), font=("Consolas", 12, "bold"), text_color="#a9b1d6").pack()

            canvas = ctk.CTkCanvas(item_frame, width=150, height=150, bg="#000000", highlightthickness=0)
            canvas.pack(pady=10)
            canvas.create_oval(20, 20, 130, 130, outline="#1a1a1a", width=12)
            cor_neon = "#ff0033" if porc >= 50 else "#ffcc00"
            canvas.create_arc(20, 20, 130, 130, start=90, extent=-(porc/100.0)*360, outline=cor_neon, width=12, style="arc")
            canvas.create_text(75, 65, text=f"{porc}%", fill="white", font=("Consolas", 24, "bold"))
            canvas.create_text(75, 95, text="VERIFICAR", fill=cor_neon, font=("Consolas", 11, "bold"))