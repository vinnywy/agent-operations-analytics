# Desenvolvimento proporcional

Preserve padrões do workspace e alterações existentes. Defina entradas, saídas, erros
esperados e critérios da mudança antes de implementar. Reutilize abstrações comprovadas;
não introduza camada, framework ou dependência sem necessidade e autorização compatível.

Use nomes claros, funções com responsabilidade delimitada, configuração separada de
segredos e mensagens de erro sem credenciais. Comentários explicam decisões não óbvias.
Em Python, prefira biblioteca padrão, context managers, parâmetros explícitos e testes
para comportamento alterado. Não formate o repositório inteiro por mudança pequena.

Presets pessoais são orientação de estilo, não estados de segurança:

- workspace-default: manter convenções vigentes; opção inicial.
- python-standard: em código Python novo sem padrão local, seguir PEP 8, separar I/O de
  transformações e usar type hints em interfaces quando ajudarem; sem instalar formatter.
- minimal-diff: evitar mudanças estéticas fora do escopo; nunca dispensar clareza ou testes.

Check essencial: inspecionar diff, executar testes pertinentes disponíveis, registrar
resultado e limitações. Não inventar suite inexistente. Uma revisão semântica breve pelo
executor não equivale a um parecer independente nem exige chamada extra de modelo.
Erro conhecido, segredo exposto e evidência inválida não podem ser ignorados por recusa
de revisão opcional. Mantenha status bloqueado ou corrigível e explique a pendência.
