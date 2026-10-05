# Security Policy — Aurora AI

## Uso autorizado

O Aurora AI deve ser usado somente em sistemas, dispositivos, redes e dados para os quais você tenha autorização.

Os componentes de monitoramento, análise e resposta são destinados a laboratório, desenvolvimento e defesa autorizada.

## Segredos

Nunca coloque no Git:

- tokens de API;
- chaves privadas;
- senhas;
- cookies ou sessões;
- bancos de dados com informações pessoais;
- arquivos de configuração com credenciais.

Use variáveis de ambiente e mantenha os valores reais no `.env`, que não deve ser versionado.

## Relato de vulnerabilidades

Para uma vulnerabilidade de segurança real, evite publicar credenciais, dados pessoais ou detalhes exploráveis em uma issue pública. Compartilhe o problema de forma privada com o mantenedor.

## Execução de código

O analisador de código da Aurora opera em modo de análise estática e não deve ser tratado como sandbox para executar código não confiável. O projeto não considera `exec()`, blacklist ou subprocessos isolados como mecanismos suficientes para executar código arbitrário com segurança.

## Limitações

As heurísticas de detecção do projeto não substituem uma solução antivírus/EDR profissional. Um alerta pode ser falso positivo e uma ausência de alerta não significa que um arquivo seja seguro.
