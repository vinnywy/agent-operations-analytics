# Evaluation

Deterministic tests verify schemas, transitions, path containment, hashes, explicit checks and service contracts. They run without a model or API key.

Behavioral evals are optional. They record model, protocol hash, case hash, timestamp, output schema and result. They do not certify a host, prove absence of hallucination, or measure all provider tokens.

The shared-memory benchmark uses synthetic records, labelled queries, isolated evaluation queries, precision@5, recall@5, MRR, returned bytes and latency. The initial comparison is exact/filtered retrieval against lexical/filtered retrieval. Vector retrieval requires a separate decision backed by measured failure cases.

The project does not claim AI acceleration. A 2025 METR study of experienced open-source developers found slower completion in its measured setting, a useful reason to measure this workflow rather than rely on intuition. [Source](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/)
