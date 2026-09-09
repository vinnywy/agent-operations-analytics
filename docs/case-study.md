# Case study

This project studies a narrow problem: how a small analytics team can preserve task context and evidence while using an AI client without turning every task into an expensive review or a long prompt.

The implemented baseline stores local task state and keeps personal presentation preferences separate from common operating controls. The experimental extension stores approved, synthetic team records in a scoped service. The proposed extension describes cross-team grants because sharing requires explicit policy, provenance and revocation.

The main hypothesis is testable: scoped, attributable retrieval may reduce avoidable repeated investigation. The project does not treat repeated validation after a data or code change as waste. Measurement requires paired tasks, labelled retrieval queries and independent quality review.
