# Client facts file — template

One folder per client: `_context/facts/`. The writing skill is only allowed to state what's in here. If a number or spec isn't in this file, it doesn't go on the page — the writer asks instead of guessing.

Build it from: the existing site, brochures, email correspondence, support tickets, onboarding calls. Confirm everything with the client once, then it's canon.

## claims.md — confirmed claims

```
# Confirmed claims (client signed off <date>)

## Services
- <service>: <exactly what can be said about it, in one line>

## Equipment / capabilities
- <item>: <spec as confirmed. Include units. No ranges unless confirmed as ranges.>

## Locations
- <site>: <address / area served, as the client states it>

## Trust signals (safe to claim)
- <years in business / certifications / memberships / fleet size — confirmed only>

## NOT safe to claim (asked, denied, or unverified)
- <claim the old site makes that the client could not confirm — never reuse it>
```

## terminology.md — how this industry actually talks

```
# Terminology

USE            -> INSTEAD OF        (why)
<correct term> -> <wrong/slang term> (<client comment or industry norm>)
```

Every correction the client makes in review goes here AND into banned_terms.txt as a regex, so it can never recur.

## positioning.md — depth per service

```
# Positioning

- <service A>: primary. Full pages, deep coverage.
- <service B>: secondary. Mentioned, not sold hard.
- <audience note>: e.g. "resellers/brokers are CUSTOMERS — never write copy that insults them."
```

## Why this works

The failure mode of AI writing isn't grammar — it's confident invention. A model will state a plausible spec that doesn't exist. This file makes "plausible" irrelevant: the page can only say what the client already confirmed. Sounds paranoid until an AI invents a spec for you once.
