# Arquitetura da Aurora IA

A Aurora IA é um Sistema Operativo de Defesa Cibernética baseado num modelo `Package-by-Feature`.

## Camadas do Sistema
1. **Core (`/core`)**: Gere o estado, exceções e a orquestração de threads para evitar bloqueios na GUI.
2. **Interface (`/ui`)**: Construída em `customtkinter`, dividida em componentes reutilizáveis, janelas modulares e um maestro central (`gui.py`).
3. **Cérebro (`/llm` & `/agents`)**: O Qwen2.5 (Abliterated) atua como raciocínio lógico, enquanto os agentes ReAct fazem auto-correção.
4. **Memória (`/memory`)**: Motor RAG baseado em FAISS L2 e SQLite (Air-gapped).
5. **Ferramentas (`/tools`)**: Isolamento estrito de I/O, Sandbox fileless e OSINT.