# Shared-memory laboratory

`experimental`. Run only with synthetic fixtures. This is a local PostgreSQL laboratory, not a hosted service and not an agent memory plugin.

```bash
docker compose up --build
```

The API listens on loopback. `X-Principal` selects one of the fixture principals only for local demonstration; production requires an identity provider and verified credentials. The service enforces team/project membership before reading or writing records. See `contracts/openapi.yaml` and `migrations/001_initial.sql`.

The demo proves explicit publication, scoped retrieval, revision conflict and a denied cross-team read. It does not measure productivity or provide production authentication.
