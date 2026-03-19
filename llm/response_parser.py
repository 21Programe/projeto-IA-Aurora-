# llm/response_parser.py
import re

class AuroraResponseParser:
    @staticmethod
    def extrair_blocos_de_codigo(texto_resposta):
        """
        Varre a resposta da IA e extrai tudo que estiver dentro de blocos Markdown (```).
        Retorna uma tupla: (lista_de_codigos_extraidos, texto_resposta_limpo)
        """
        marcadores = chr(96) * 3
        # Regex suprema: Pega TUDO o que for código, independentemente da linguagem
        padrao_codigo = marcadores + r"[^\n]*\n(.*?)" + marcadores
        
        codigos_encontrados = re.findall(padrao_codigo, texto_resposta, re.DOTALL)
        
        if codigos_encontrados:
            texto_limpo = re.sub(padrao_codigo, "\n\n[⚙️ SCRIPT EXTRAÍDO PARA O PAINEL DE PAYLOAD]\n", texto_resposta, flags=re.DOTALL)
            return codigos_encontrados, texto_limpo
            
        return [], texto_resposta

    @staticmethod
    def checar_uso_de_ferramenta(texto_resposta):
        """
        Verifica se a IA tentou invocar uma ferramenta no formato:
        TOOL: nome_da_ferramenta
        INPUT: "parametro"
        """
        match = re.search(r"TOOL:\s*(.*?)\nINPUT:\s*(.*)", texto_resposta, re.IGNORECASE)
        if match:
            tool_name = match.group(1).strip().replace("()", "")
            tool_input = match.group(2).strip().strip('"\'')
            return tool_name, tool_input
        return None, None