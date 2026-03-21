# config/logging_config.py
import logging
import os
from config.settings import DIRS

def configurar_logs_sistema():
    """Configura o sistema de logs rotativos da Aurora."""
    log_file = os.path.join(DIRS["logs"], "aurora_kernel.log")
    
    # Formatação militar/técnica para os logs físicos
    log_format = '%(asctime)s - [AURORA_KERNEL] - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler() # Opcional: também imprime na consola do terminal
        ]
    )
    return logging.getLogger("AuroraCore")

kernel_logger = configurar_logs_sistema()