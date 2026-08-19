# Xano Phase 1 handoff

`schema.json` is the import/deployment contract for the Xano control plane. It is
deliberately marked `BLUEPRINT_NOT_PUSHED`: this workspace currently exposes no
Xano MCP tools and has no Xano CLI executable.

When access is configured:

1. Create the listed enums and tables.
2. Make `GateDecision` and `AuditEvent` append-only to ordinary clinic roles.
3. Implement each transition as a Xano function with optimistic locking on
   `Encounter.version`.
4. Store the canonical rule JSON and SHA-256 returned by `shared/gate` without
   reconstructing it in the frontend.
5. Seed only the committed Texas neurotoxin rule and synthetic fixtures.
6. Export the resulting Xano schema/function definitions into this directory and
   record the workspace/version in the Phase 1 task note.

The judging demo should show the Xano state transition and its matching
`AuditEvent`, not just a frontend badge.

