# Economia de tokens

## Padrão

- Núcleo curto + task atual + instruções acionadas. Não ler docs/ por inteiro.
- Consultar `context --task ID` para metadados compactos, não exportar o banco inteiro.
- Buscar nomes/termos antes de abrir; ler skill selecionada integralmente.
- Não reler conteúdo estável na mesma execução. Revalidar se houver mudança relevante.
- Checks determinísticos não chamam modelo; revisões opcionais só por pedido/aceite.
- Preferir recorte/diff explícito para revisão direcionada. Não truncar silenciosamente.
- Retornar somente achados sustentados. Sem achados, informar cobertura e limitações em
  poucas linhas. Não fabricar sugestão para preencher relatório ou RFC.
- Sem loop de polimento indefinido, votação de agentes ou revisão integral de rotina.
- Se dois refinamentos de prompt não resolverem, expor impedimento concreto.

## Medição

O limite `--max-chars` limita o pacote encaminhado à revisão, não os tokens internos de
raciocínio nem todo o contexto do provedor. Timeout limita duração do subprocesso; não
garante cancelamento imediato de uma requisição já aceita pelo serviço. Consumo não
reportado é `null`, nunca zero. Comparar custo por entrega aceita, incluindo retrabalho.

O teste estático limita AGENTS.md a 6 KiB. Isso é orçamento de bytes, não uma estimativa
exata de tokens. Redução de tamanho não permite remover evidência, riscos ou segurança.
