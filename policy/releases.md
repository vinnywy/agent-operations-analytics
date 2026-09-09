# Publicação e atualização

1. Mantenedor prepara alteração vinculada a RFC/task e changelog.
2. Executa testes e evals pertinentes. NOT_RUN continua pendência explícita.
3. Confirma checks do GitHub e registra decisão de publicação.
4. Gera release-manifest.json, assina com SSH namespace agentops-release.
5. Publica artefato, assinatura e instruções de confiança por canal conhecido.
6. Integrante verifica assinatura com allowed_signers confiável, obtido por canal
   independente do artefato que será verificado.
7. `update` prepara cópia autenticada e backup. Instala em ambiente separado, testa e
   troca conscientemente o caminho ativo. Preserva a instalação anterior para rollback.

Não atualizar tarefas em andamento. O mantenedor informa release adotada pelo grupo;
cada task registra a versão. Sem serviço central, não há telemetria de todas as instalações
nem revogação instantânea offline. No piloto, origem oficial é verificada no comando de
assinatura/update, e o diagnóstico cotidiano reporta apenas o que foi verificado localmente.
