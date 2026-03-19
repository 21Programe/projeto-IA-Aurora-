# voice/stt.py
import speech_recognition as sr

class AuroraSpeechToText:
    @staticmethod
    def ouvir_comando(log_callback, process_callback):
        with sr.Microphone() as source:
            log_callback("🎙️ Escutando...", "SISTEMA")
            try:
                # Ouve e converte para texto
                query = sr.Recognizer().recognize_google(
                    sr.Recognizer().listen(source, timeout=5), 
                    language="pt-BR"
                ).lower()
                
                log_callback(query, "Usuário Acústico")
                process_callback(query) # Envia para o processador de comandos
            except Exception:
                log_callback("Ruído limitando inferência verbal.", "SISTEMA")