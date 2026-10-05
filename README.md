# 🌌 Aurora AI — Local AI & Cybersecurity Orchestrator

> Projeto principal do portfólio **21Programe**: um laboratório de engenharia em Python que combina IA local, memória semântica, automação e componentes de monitoramento/defesa em uma aplicação desktop.

![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)
![LLM Local](https://img.shields.io/badge/LLM-Local%20%2F%20GGUF-7F52FF)
![RAG](https://img.shields.io/badge/RAG-FAISS-00A98F)
![SQLite](https://img.shields.io/badge/Storage-SQLite-003B57)
![Status](https://img.shields.io/badge/Status-Em%20evolução-orange)

## Visão geral

A **Aurora AI** nasceu como uma tentativa de criar um assistente local capaz de trabalhar com conhecimento técnico sem depender obrigatoriamente de uma API externa.

O projeto evoluiu para uma arquitetura modular com:

- **LLM local** para processamento de linguagem;
- **RAG** para busca semântica em conhecimento técnico;
- **memória persistente** com SQLite e armazenamento vetorial;
- **agentes** para planejamento, memória, pesquisa, execução e segurança;
- **monitoramento** de recursos do sistema;
- **componentes de segurança** e barramento de eventos;
- **interface desktop** em CustomTkinter;
- **testes automatizados** para partes críticas do sistema.

O objetivo deste repositório não é apenas demonstrar uma aplicação pronta, mas registrar a evolução de um sistema complexo construído de forma incremental.

## 🧠 Arquitetura

A estrutura atual separa responsabilidades por domínio:

```text
projeto-IA-Aurora-/
├── agents/        # Agentes de planejamento, memória, pesquisa e execução
├── api/           # Rotas/API
├── core/          # Estado, orquestração e núcleo da aplicação
├── llm/           # Integração com modelos locais e construção de prompts
├── memory/        # Chunking, RAG, SQLite e busca vetorial
├── seguranca/     # Componentes de monitoramento e resposta
├── services/      # Monitoramento, scheduler e sentinel
├── ui/            # Interface desktop
├── tests/         # Testes automatizados
├── knowledge/     # Base de conhecimento
├── config/        # Configurações e bootstrap
├── tools/         # Ferramentas auxiliares
└── main.py        # Ponto de entrada
```

O ponto de entrada inicializa banco, LLM, interface e agentes e, em seguida, inicia componentes de monitoramento/segurança em threads separadas.

## 🔎 Tecnologias

**Python:** aplicação principal e automações.

**IA local:** suporte a modelos quantizados no formato GGUF por meio de `llama-cpp-python`.

**RAG:** FAISS + embeddings para recuperação semântica de documentos e conhecimento técnico.

**Persistência:** SQLite para memória e estado.

**Desktop:** CustomTkinter.

**Processamento de documentos:** PyMuPDF, BeautifulSoup e EbookLib.

**Sistema:** integração com processos, recursos e hardware via `psutil`, com suporte a ambientes NVIDIA/CUDA no setup local.

## 🛡️ Segurança e engenharia

O projeto possui componentes separados para:

- barramento de eventos e alertas;
- monitoramento do sistema;
- visão/proteção;
- quarentena de downloads;
- filtros e rotinas auxiliares;
- testes de componentes de segurança.

A proposta é manter esses módulos isolados para facilitar auditoria, manutenção e evolução.

> **Importante:** os módulos de segurança são destinados a ambientes próprios, laboratório e uso autorizado.

## 🧪 Testes

O repositório contém testes para áreas como:

- autocorreção;
- RAG;
- ferramentas;
- visão.

A meta da próxima fase é ampliar cobertura, adicionar testes de integração e tornar a execução reproduzível em ambiente limpo.

## 🚀 Instalação

### Requisitos

- Windows 10/11 ou ambiente compatível;
- Python 3.10+;
- GPU NVIDIA é opcional, mas pode ser utilizada para aceleração local;
- modelo GGUF compatível.

### Ambiente virtual

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Depois, copie o template de ambiente e ajuste somente os valores locais:

```powershell
Copy-Item .env.example .env
```

Edite `.env` para apontar para os modelos GGUF e, opcionalmente, configurar alertas Telegram. **Nunca publique o arquivo `.env` nem credenciais reais no Git.**

## 📌 Estado do projeto

**Fase atual:** refatoração e consolidação para portfólio.

### Próximos marcos

- [x] eliminar caminhos absolutos do ambiente local;
- [x] centralizar configurações principais;
- [ ] melhorar instalação do projeto;
- [ ] ampliar testes;
- [ ] adicionar demonstração visual;
- [ ] documentar fluxo completo de RAG e memória;
- [ ] preparar release `v1.0`.

## 👨‍💻 Autor

**Diego Alves de Souza — 21Programe**

Foco em **Python, Inteligência Artificial local, desenvolvimento de sistemas, Linux e Segurança da Informação**.

[GitHub 21Programe](https://github.com/21Programe)
