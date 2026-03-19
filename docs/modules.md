# Módulos Táticos

- **Sentinel (`services/sentinel.py`)**: Monitoriza temperatura da GPU e RAM via `psutil` e `nvidia-smi`.
- **Warp Exit (`services/monitor.py`)**: Protocolo Scorched Earth para apagar logs e evadir-se de análises forenses.
- **AutoKnowledge (`services/scheduler.py`)**: Agendador que recolhe papers do arXiv e OpenLibrary autonomamente.
- **Vision (`vision/`)**: Pipeline de conversão e inferência usando o Moondream2 (GGUF).