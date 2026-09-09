# Proposed scenario: cross-team revocation

1. Alpha publishes revision 2 of a synthetic finding.
2. A curator grants Beta access until a defined expiry.
3. Beta retrieves revision 2 and cites its ID/hash in a report.
4. Alpha revokes the grant.
5. A new Beta lookup is denied or returns no visible object.
6. The implementation records revocation and delivery metadata without claiming to erase a copy already received by Beta.

Acceptance requires authorization tests, audit events, a documented cache-invalidation policy and a decision about retention.
