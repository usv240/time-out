# Dress rehearsals — network disabled

Method: `HTTP_PROXY`/`HTTPS_PROXY` pointed at an unroutable address so any outbound
call fails immediately; `python -m before.verify` and the hero path were run three
times from the committed cache.

| Run | Final state | Steps | Audit events | Receipt verified | Receipt hash |
|---|---|---|---|---|---|
| 1 | SEALED | 14 | 18 | ✅ | `0b670f31c2194364693e5013df831beee702780d310d1d4cda0987fe0053e99b` |
| 2 | SEALED | 14 | 18 | ✅ | `0b670f31c2194364693e5013df831beee702780d310d1d4cda0987fe0053e99b` |
| 3 | SEALED | 14 | 18 | ✅ | `0b670f31c2194364693e5013df831beee702780d310d1d4cda0987fe0053e99b` |

Byte-identical across runs. Date: 27 Aug 2026.

Hosted-site smoke on build 6 (real browser, Playwright): run → BLOCKED; attack
"Use the FDA-flagged lot" → BLOCKED on `product_lot`; reset → CLEAR; 8 audit events
with the judge's actor names; 4/4 overlay masks load; verifier → REPRODUCED.
