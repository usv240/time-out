# BEFORE public site

Zero-dependency public UI served by the local reference API. Run from repository
root:

```powershell
python -m before.seed
python -m before.app.server --offline
```

Routes:

- `/` - live seeded BLOCKED encounter
- `/try` - complete thirteen-step synthetic workflow
- `/api` - instant key, playground, endpoint reference, boundaries
- `/receipt/:id` - verified patient-visible bounded receipt
- `/evidence` - primary sources and sponsor implementation evidence
- `/how-it-works` - Gate, state machine, and snapshot reproduction

The UI has explicit loading, workflow-conflict, offline, and empty states. It makes
no claim that Xano or live sponsor accounts are activated.
