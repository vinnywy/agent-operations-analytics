# Synthetic analytics demonstration

`implemented` demonstration for the SCAN EDA skill. The fixture is intentionally small and synthetic. It shows how an analyst records stakeholder questions, coverage limitations, aggregates, anomalies and segments before selecting a model.

Run `python generate.py --seed 42 --output sales.csv`. The same seed produces the same file hash. The example does not estimate a causal effect, predict a future outcome, or represent a real business dataset.

## Expected workflow

1. S — define revenue, cancellation rate and order count with denominators.
2. C — inspect types, nulls, duplicate order IDs and date coverage.
3. A — aggregate by month and locate a deliberately injected outlier.
4. N — compare channel and region while preserving denominator context.

Record conclusions as an evidence-backed task in the harness. A suspicious segment is an observation, not an automatic cleaning instruction.
