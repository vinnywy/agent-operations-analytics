# SCAN — referência normativa

Definição fornecida pelo responsável pelo método, registrada em 2026-09-08.
Escopo: guiar o workflow durante uma etapa de Análise Exploratória de Dados (EDA).

## S — Stakeholder goals

Identificar quais KPIs e dimensões importam para os envolvidos. Levantar requisitos:
tendências gerais, taxas de crescimento, mensuração de desempenho e acompanhamento
de KPIs. Exemplos genéricos: crescimento mensal/anual; desempenho de um produto;
taxa de reembolso e valor médio de pedido. São exemplos de perguntas, não obrigações
de calcular métricas indisponíveis ou irrelevantes. Taxas exigem denominadores definidos.

## C — Columns and Coverage

Inventariar dados disponíveis e possibilidades de uso: colunas, tipos, features numéricas
e categóricas, chaves, granularidade, cobertura, valores ausentes e restrições.
Perguntar quais dados existem e como podem responder aos objetivos.

## A — Aggregate and Anomalies

Calcular métricas agregadas relevantes. Examinar outliers e padrões inesperados.
Não descartar outliers apenas por serem extremos. Separar possível erro de registro de
observação legítima. Registre regra e impacto de qualquer transformação.

## N — Notable Segments

Recortar por categoria, tempo ou outras dimensões importantes para revelar insights
iniciais. Comparar cobertura e tamanho dos grupos. Explicitar incerteza; exploração não
estabelece causalidade nem valida automaticamente um modelo.

## Dados brutos → dados úteis

Avaliar features numéricas/categóricas, ausências, outliers e necessidade de limpeza.
Preservar dados brutos. Quando pertinente, comparar visão original e tratada para mostrar
impacto. A decisão pode ser não limpar. Anotar limitações e questões para investigação.

## Saída da etapa

Perguntas e KPIs; inventário/cobertura; agregados/anomalias; segmentos relevantes;
transformações justificadas; evidências; limitações; próximos passos. Profundidade é
proporcional ao briefing. Não impor todas as análises em cada dataset.
