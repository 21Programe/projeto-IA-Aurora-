# core/exceptions.py

class AuroraBaseException(Exception):
    """Classe base para todas as exceções críticas do Sistema Operativo Aurora."""
    pass

class LLMOfflineError(AuroraBaseException):
    """Disparado quando é exigida inferência tática mas o motor GGUF não está na RAM."""
    def __init__(self, message="Motor LLM Qwen2.5 não se encontra carregado ou online."):
        super().__init__(message)

class SandboxExecutionViolation(AuroraBaseException):
    """Disparado quando um payload tenta quebrar o isolamento do Sandbox."""
    def __init__(self, message="Violação de segurança detetada no Sandbox."):
        super().__init__(message)

class PanicTriggeredException(AuroraBaseException):
    """Disparado quando o protocolo Scorched Earth é ativado."""
    def __init__(self, message="Protocolo de Pânico ativado. A expurgar RAM e registos."):
        super().__init__(message)