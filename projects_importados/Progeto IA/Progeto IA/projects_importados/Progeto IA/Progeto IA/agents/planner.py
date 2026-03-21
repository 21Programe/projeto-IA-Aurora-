# agents/planner.py

class AuroraTacticalPlanner:
    @staticmethod
    def gerar_plano_de_missao(missao_objetivo):
        """
        Recebe um objetivo bruto e estrutura os passos lógicos (Chain-of-Thought)
        antes de enviar para a execução do LLM ou Sandbox.
        """
        plano_padrao = (
            "1. Reconhecimento de vetores e análise do contexto.\n"
            "2. Geração do script/payload seguro.\n"
            "3. Simulação de dados no ambiente controlado.\n"
            "4. Execução em Sandbox (Memory-safe).\n"
            "5. Relatório de extração."
        )
        # Pode ser expandido no futuro para que o próprio LLM gere este plano
        return plano_padrao

    @staticmethod
    def formatar_prompt_correcao(missao, codigo_atual, erro_traceback):
        """Formata a diretriz de auto-cura quando um código falha."""
        return (
            f"O código falhou durante a execução tática!\n"
            f"MISSÃO: {missao}\n"
            f"CÓDIGO ATUAL:\n{codigo_atual}\n"
            f"ERRO DO COMPILADOR/INTERPRETADOR:\n{erro_traceback}\n"
            f"Corrija os erros estruturais e forneça apenas o código completo e funcional, sem explicações."
        )