# Evidências

Toda evidência liga um critério a arquivo existente no workspace, com SHA-256 e instante.
Uma referência de arquivo é evidência estrutural, não aprovação semântica automática.
Saídas determinísticas incluem comando cadastrado, hashes de entradas, exit code e data.
Saídas de agentes são pareceres. Campos PASS/FAIL/ERROR/NOT_RUN não são intercambiáveis.

Registre como entradas do check todos os arquivos relevantes (código, configuração,
fixtures); o harness não infere toda a árvore de dependências de qualquer linguagem.
Mudança das entradas declaradas ou dos artefatos invalida o fechamento. Mudança não
declarada pode escapar: a documentação deve declarar essa cobertura limitada.

Reabrir task concluída limpa checks e requer nova validação. Não há prova inviolável
contra edição direta do SQLite pelo proprietário da máquina.
