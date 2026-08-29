# Doctavian — what we worked out ourselves

The official OpenAPI spec, downloaded from
`developers.doctavian.com/openapi/latest/resources/doctavian-openapi-specification.json`
(no login required). Kept here so the integration can be reasoned about offline.

## The blocker, precisely

Every route requires **both** a bearer token and an `X-Api-Key`. Verified against the
live API rather than assumed:

| Sent | Response |
|---|---|
| Bearer only (Microsoft), any endpoint | `401 ApiKeyNotFound` |
| Bearer + empty/wrong key | `401 ApiKeyInvalid` |
| No auth at all | `401 ApiKeyNotFound` |

The bearer is never evaluated — the key gate runs first. That is why switching from a
Google to a Microsoft identity changed nothing, and why the account-linkage theory was
a dead end.

The spec confirms it: `security: [{bearerAuth, apiKeyHeader}, {bearerAuth, apiKeyQuery}]`
— both, in either combination.

## Our paths were already right

All four match the spec exactly: `/v1/documents/template/upload`,
`/v1/documents/data/upload`, `/v1/documents/document/generate`,
`/v1/signatures/envelope/create`. Nothing to fix in the client but the key.

## No self-serve key on the API

728 route/method pairs probed for anything that issues or reveals a key — every one
returned `404 OperationNotFound`. The two public routes
(`/public/v1/auth/{provider}/authorize` and `/token`) are OAuth proxies, not key issuers.

Enumeration is possible without credentials because routing runs before authentication:
a path that does not exist returns `404 OperationNotFound` even unauthenticated, while a
real one returns `401`. That difference is a free oracle.

## The way in

Keys come from the portal, and the portal needs an active subscription or trial:

1. **https://portal.doctavian.com/trial** — 30 days, no credit card
2. Sign in with Microsoft or Google, complete the short form (name, job title, company)
3. Portal → **API Keys** → copy the key for the Documents API
4. `DOCTAVIAN_API_KEY=` in `.env` (currently empty), and replace `DOCTAVIAN_BEARER`,
   which still holds an expired Google `ya29.` token

Docs note that subscriptions expect a company Microsoft or Google account and that
personal accounts are not supported. Whether the *trial* enforces that is untested —
it is the one thing worth trying before waiting on support.

Base URL: `https://api.doctavian.com` (the spec's server). `demo.api.doctavian.com`
behaves identically for auth.
