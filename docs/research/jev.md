# TypeSafe Jev API research

Verified against public official sources on 2026-10-03 (America/Denver). No authenticated console was opened, no payment was made, no secret was inspected, and no live request was sent. Built-in web search and fetch supplied usable official pages; Firecrawl was unnecessary. This research supports Phase 9 without changing the sacred build documents.

## HTTP contract

Use `POST https://api.typesafe.ai/v1/systemone`, `Authorization: Bearer <key>`, and JSON content. Required top-level request fields are `model` (string), `state` (string/object/array), and a nonempty `questions` object keyed by caller-selected IDs. Successful responses require `model`, `answers`, and `usage`; answers reuse the question IDs. `usage.input_tokens` and `usage.output_tokens` are integers. The response model can differ from a requested alias. `GET /v1/models` lists account-visible models or aliases. [Published OpenAPI 0.2.0](https://api.typesafe.ai/openapi.json)

Do not send OpenAI-style `messages`, `response_format`, or sampling parameters. The project requires direct HTTP with `httpx`, not installation of TypeSafe's SDK. Bound request size locally; there is no documented `max_tokens` request field in this contract.

| Primitive | Request question fields | Required answer fields |
|---|---|---|
| Choice | `type: "choice"`, meaningful `instructions`, `criteria` map of option name to description | `type: "choice"`, `choice` string, `probabilities` map, numeric `confidence` |
| Score | `type: "score"`, meaningful `instructions`, ordered `criteria` array | `type: "score"`, numeric `score`, numeric `confidence`, `legend` map, `probabilities` map |
| Noul | `type: "noul"`, meaningful `instructions`, optional `criteria` with `true`/`false` descriptions | `type: "noul"`, numeric `noul` |

Choice selects one option and supports up to 255 options. Descriptions can be strings, objects, arrays, or null. The model sees option names and descriptions, but **does not see question IDs**. Put code definitions in the instructions or criteria, never only in a routing key. [Choice](https://docs.typesafe.ai/primitives/choice)

Score levels are indexed from zero by array position. Its score is the probability-weighted mean, potentially fractional. HTTP `legend` and `probabilities` use stringified level indices, not integer JSON keys. Use 2–10 descriptive levels, per prose guidance. [Score](https://docs.typesafe.ai/primitives/score)

Noul is probability of yes/true, bounded 0–1, **not a boolean or a severity score**. It has no separate confidence field. Several Noul questions can represent independently applicable qualitative codes; this is an integration recommendation, not a provider mandate. [Noul](https://docs.typesafe.ai/primitives/noul)

Choice/Score confidence describes the returned distribution. It is not identical to the chosen option's probability and does not guarantee empirical accuracy. Noul uncertainty is greatest near 0.5. If derived Noul confidence is needed, the documented formula is `abs(2*p - 1)`; label this as derived, not provider-returned. Preserve raw probability for calibration and provenance. [Confidence](https://docs.typesafe.ai/confidence)

## Known documentation differences

The OpenAPI schema makes `instructions` optional/null-capable, whereas the prose API page labels it required. OpenAPI Score declares one minimum item and no maximum; prose recommends at least two and permits up to ten. The prose `legend` shorthand mentions strings, while OpenAPI also admits structured descriptions. [OpenAPI](https://api.typesafe.ai/openapi.json), [API reference](https://docs.typesafe.ai/api)

Qualia should use the safe intersection: always supply nonempty string instructions, string descriptions, 2–10 Score levels, and explicitly validated probabilities. That avoids relying on ambiguous permissiveness without changing the build contract. Fixture validation must reject missing/mismatched question IDs, wrong primitive types, unknown choices, non-finite/out-of-range values, and invalid usage. A hand-authored fixture is not a recorded live response; label its provenance accurately.

## Synthetic shape example

Original example for Qualia; the response below is illustrative, **not a recorded API result**.

```json
{
  "model": "jev-1.13.0",
  "state": "The participant says: I asked my neighbour to help carry the boxes.",
  "questions": {
    "code_7": {
      "type": "noul",
      "instructions": "Does the participant explicitly describe seeking practical assistance?",
      "criteria": {
        "true": "The speaker explicitly asks another person for help with a task.",
        "false": "There is no explicit request for practical help."
      }
    }
  }
}
```

```json
{
  "model": "jev-1.13.0",
  "answers": {"code_7": {"type": "noul", "noul": 0.96}},
  "usage": {"input_tokens": 100, "output_tokens": 10}
}
```

## Model, limits, and cost

Pin `jev-1.13.0`, matching the build runbook. Both `jev-latest` and `jev-preview` currently resolve to it, but aliases can move. Record the returned model in provenance. Published limits: 64k tokens per request; state plus longest question must fit 32k. Listed throughput is 100k tokens/second and 80 requests/second, explicitly subject to change. Version IDs remain accepted even when model-list results show only aliases. [Model reference](https://docs.typesafe.ai/models)

Current public pricing is $0.042 per million input tokens, with free outputs. Estimate ledger dollars as `input_tokens * 0.042 / 1_000_000`; retain output usage separately. Prices and account terms need rechecking before live use. [TypeSafe launch pricing](https://typesafe.ai/blog/introducing-system-one-models-and-jev)

For `429` and `529`, official guidance is exponential backoff. HTTP `401` is an authentication failure; `422` is request validation failure. Qualia must bound retries and log every external attempt under its egress/budget rules rather than silently multiplying calls. Do not log raw validation bodies: these may echo supplied text. [API errors](https://docs.typesafe.ai/api)

## Account, billing, and retention evidence

The public quick start says to obtain an API key in the dashboard. It does not verify a current sidebar label or the owner's account status. [Quick start](https://docs.typesafe.ai/introduction/quickstart)

The customer agreement describes credits as required for use, promotional credits as discretionary, and automatic purchased-credit refills as opt-in. No evidence here proves the owner's balance, that free credits were granted, the minimum top-up, or an active card. Its data clause says customer data is not used to change AI model weights without prior consent; it also permits specified telemetry, fraud/abuse, and legal processing. This is not a zero-retention promise. [Customer agreement §§4, 8](https://typesafe.ai/legal/mca)

Public legal docs offer ZDR to enterprise customers by contacting sales. The privacy policy identifies US hosting and gives no fixed general retention duration. These sources support keeping Jev off by default for Qualia and never treating ordinary sign-up as ZDR enrollment. [Enterprise ZDR](https://docs.typesafe.ai/legal), [privacy policy](https://typesafe.ai/legal/privacy-policy)

Owner steps are in [JEV-SETUP.md](../JEV-SETUP.md). A future live smoke test must use synthetic content, keep the key server-side, and establish actual access. Until then, contract knowledge is verified; live compatibility and billing are unverified.
