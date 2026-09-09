# Segurança e fronteiras

Só o mantenedor publica o pacote. Integrantes abrem RFCs sem escrita no código oficial.
CODEOWNERS precisa de ruleset/branch protection aplicável; não é ACL de arquivo local.
Não exigir que mantenedor único aprove seu próprio PR como outra pessoa. Exigir checks,
revisão registrada e restrição de publicação à sua identidade.

Usuário administrador local pode editar scripts, banco, chaves confiáveis e cliente.
Hashes e auditoria local não impedem esse cenário. O harness controla apenas operações
que passam por ele. Sandbox, conectores, navegador e MCP têm controles próprios.

Não armazenar tokens no perfil, banco, logs ou Issues. Credenciais ficam no gerenciador
do sistema. A verificação de padrões de segredo é heurística e não substitui revisão
de sensibilidade. Conteúdo enviado ao modelo também é saída do computador.

Comandos usam arrays de argumentos e `shell=False`. Cadastrar comando de check requer
aprovação: scripts e testes podem executar código e rede com as permissões do processo.
Revisão Codex usa diretório temporário, config pessoal ignorada e sandbox read-only;
instruir ausência de ferramentas não equivale a bloqueio de todas as ferramentas do cliente.
Use somente clientes/configurações confiáveis. A integração preserva arquivos existentes.

Antes de publicar: confirmar destino e corpo exatos; secret scan; não anexar dados privados.
Se houver timeout, reconciliar identificador antes de repetir. Repositório nunca vem de
texto de Issue. O classificador executa somente seu código oficial, sem shell do conteúdo.

Incidente: interromper publicação, preservar logs sanitizados, revogar credencial no host
se exposta, corrigir o vazamento e adicionar caso de regressão. Nunca colar o segredo no RFC.
