# Phase 3 — Safety receipt, verification, polish (Aug 29 – Sep 1)

## Aug 29–30 · The safety receipt
Compile the frozen record: gate decision + rule snapshot + extracted evidence +
comprehension result + baseline + consent + attestation. Hash it (SHA-256).

Patient-facing verification view: scan QR → see the receipt and its status.

## Aug 30–31 · name.com  (build last, as designed)
Publish the receipt hash and status as a DNS TXT record on a domain we register
in the sandbox. Anyone can `dig TXT` and confirm the record they hold is unaltered.

Endpoint coverage: search · availability · registration · DNS.

**State the limitation plainly, on camera and in the write-up:** a TXT record is
mutable by its owner. This is a public verification channel, not an immutable
notary. Overclaiming loses a technical judge instantly.

Sandbox notes: `https://api.dev.name.com` · creds take ~15 min · a domain must be
registered in the sandbox before GET works · DNS records do not propagate.

## Sep 1 · Feature freeze
Bug triage only. Anything unfinished is cut, not rushed.

## Cut order (from the bottom, without debate)
1. VTO expectation-setting → skin baseline alone carries Perfect Corp
2. Patient QR verification view → receipt still exists and is hashed
3. name.com DNS anchor → receipt stands without it
4. SerpApi live alerts → seeded rules still demonstrate the Gate

**Never cut:** the Gate · the BLOCKED moment · human review routing ·
the comprehension gate · the medical director attestation · the demo video.
