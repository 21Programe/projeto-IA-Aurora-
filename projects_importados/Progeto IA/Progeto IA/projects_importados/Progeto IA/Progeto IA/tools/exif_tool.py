# tools/exif_tool.py
from PIL import Image, ExifTags

class AuroraForensics:
    @staticmethod
    def converter_gps_para_decimal(valor, referencia):
        try:
            graus = float(valor[0])
            minutos = float(valor[1])
            segundos = float(valor[2])
            decimal = graus + (minutos / 60.0) + (segundos / 3600.0)
            if referencia in ['S', 'W']: 
                decimal = -decimal
            return decimal
        except:
            return None

    @staticmethod
    def extrair_metadados(caminho_imagem):
        try:
            # Importamos a biblioteca Pillow de forma localizada
            from PIL import Image, ExifTags
            
            # Abre a imagem e caça os metadados brutos
            img = Image.open(caminho_imagem)
            exif_bruto = img._getexif()
            
            # Se a foto realmente não tiver nada, devolve None para acionar nossa trava
            if not exif_bruto:
                return None
                
            dados_formatados = []
            
            # Traduz os códigos numéricos para nomes reais (ex: 'GPSInfo', 'Model', etc)
            for tag_id, valor in exif_bruto.items():
                tag_nome = ExifTags.TAGS.get(tag_id, tag_id)
                
                # Pulamos essas tags porque elas são códigos de máquina gigantescos e sujam o terminal
                if tag_nome in ('MakerNote', 'UserComment', 'PrintImageMatching'):
                    continue
                    
                # Limita o tamanho do texto para não quebrar a tela do seu painel
                valor_str = str(valor)
                if len(valor_str) > 100:
                    valor_str = valor_str[:100] + "..."
                    
                dados_formatados.append(f"[*] {tag_nome}: {valor_str}")
                
            if not dados_formatados:
                return None
                
            # Junta tudo num texto bonito para a Aurora ler
            return "\n".join(dados_formatados)
            
        except ImportError:
            print("[ERRO FATAL] A biblioteca Pillow não está instalada.")
            return None
        except Exception as e:
            print(f"[ERRO EXIF] Falha na leitura do arquivo: {e}")
            return None