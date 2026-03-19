# voice/tts.py
import pyttsx3
import re

class AuroraVoiceSystem:
    def __init__(self):
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 165) 
            vozes = self.engine.getProperty('voices')
            for voz in vozes:
                if "brazil" in voz.name.lower() or "maria" in voz.name.lower() or "pt-br" in voz.id.lower():
                    self.engine.setProperty('voice', voz.id)
                    break
            self.ativo = True
        except Exception as e:
            print(f"[ERRO DE ÁUDIO] Falha ao inicializar cordas vocais: {e}")
            self.ativo = False

    def falar(self, texto):
        if not self.ativo: return
        try:
            texto_limpo = re.sub(r'[*`#]', '', texto)
            texto_limpo = re.sub(r'```.*?```', 'Código gerado e enviado para a interface.', texto_limpo, flags=re.DOTALL)
            self.engine.say(texto_limpo)
            self.engine.runAndWait()
        except Exception:
            pass