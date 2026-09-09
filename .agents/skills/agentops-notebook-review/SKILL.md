---
name: agentops-notebook-review
description: Revisar notebook por solicitação explícita, com escopo e profundidade delimitados.
---

Defina se o pedido cobre código, narrativa, leakage ou segurança. Na revisão direcionada,
selecione somente trecho relevante e dependências imediatas. Revise fontes, chaves, joins,
disponibilidade temporal, split, preprocessing e métricas quando aplicáveis ao escopo.
Não executar células, gerar dados sintéticos ou treinar por inferência. Uma análise estática
não prova reprodutibilidade. O runner remove outputs e metadados do notebook por padrão.
Use review notebook ou review leakage conforme o objetivo. Relate cobertura limitada.
