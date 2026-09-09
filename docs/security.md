# Security and guardrails

External documents, search results, RFC bodies and memory records are untrusted data. They cannot alter authority. A model is never the authorization layer: access belongs to the host, API and database policy.

Controls include explicit paths, closed schemas, argument arrays instead of shell interpolation, content hashes, scoped retrieval, secret-pattern checks, human approval for external publication and bounded review packets. Each control has a limit: a local administrator can modify local files; a hash does not prove semantic correctness; a scanner cannot find every secret; and a textual policy cannot sandbox a client.

The threat model covers prompt injection, excessive tool privilege, cross-team disclosure, stale evidence, duplicate publication and unbounded model cost. OWASP recommends least privilege and keeping authorization outside a system prompt. [OWASP guidance](https://genai.owasp.org/llmrisk/llm072025-system-prompt-leakage/)
