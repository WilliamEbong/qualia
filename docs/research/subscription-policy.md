# Subscription CLI use: official documentation review

Verified 2026-10-03. Scope: one account owner using the providers' unmodified native CLIs noninteractively. This is a documentation assessment, not provider approval of Qualia or a legal determination. No credentials were read, copied or generated; no provider calls, account changes or backend activation were performed.

## Finding

Both providers document programmatic use of their native tools. Their documentation distinguishes that use from sharing an account, collecting subscription credentials, or operating a service through another person's subscription. This supports a narrower statement than either “subscription automation is forbidden” or “any subscription integration is approved.” The applicable account agreement, product integration conditions and usage limits still matter.

Qualia's native classification and improvement backends remain unavailable. Documentation about permitted authentication does not resolve the separately observed generation bounds, request accounting and operator isolation gaps.

## OpenAI: documented functionality and limits

| Official source, accessed 2026-10-03 | What it establishes |
| --- | --- |
| [Non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode), sections Permissions and safety / Authenticate in automation | Documents `codex exec` for scripts and CI, machine-readable output and a read-only sandbox default. Exact quote: “`codex exec` reuses saved CLI authentication by default.” Its advanced account-auth section expressly discusses ChatGPT-managed CI/CD when a Codex account is needed; API keys remain the recommended automation default. It excludes that account-auth workflow from public/open-source repositories and treats stored authentication as a secret. This review does not recommend copying credential files. |
| [Authentication](https://learn.chatgpt.com/docs/auth), sections OpenAI authentication / Login on headless devices | Separates subscription access through ChatGPT login from usage-billed API keys. Documents native browser login and device-code login for headless devices, subject to account/workspace settings. Recommends API keys for programmatic workflows and warns against exposing execution in public or untrusted environments. Cached tokens must be protected like passwords. |
| [Codex SDK](https://learn.chatgpt.com/docs/codex-sdk) | Documents programmatic control, including internal workflows and application integrations. SDK availability alone does not establish which authentication or contractual terms apply to a particular deployed application. |
| [Terms of Use, non-EEA/Switzerland/UK](https://openai.com/policies/row-terms-of-use/), effective 2026-01-01 | Prohibits account sharing, programmatic extraction of data/output, and bypassing rate limits or protective measures. It also requires compliance with applicable documentation and policies. The general extraction restriction and specific automation documentation should be read together; this review cannot conclusively interpret their boundary for every workload. Business/developer offerings and other regions have different agreements. |
| [Account Sharing Policy](https://help.openai.com/en/articles/10471989-openai-account-sharing-policy) | Distinguishes an individual's use across devices from making the account available to other people. Subscription and activity limits still apply. |

The former `developers.openai.com/codex/{noninteractive,auth,sdk}` addresses redirected to the official ChatGPT Learn pages above during this check. These are rolling documents, not evidence that every current option exists in the locally audited Codex 0.160.0.

## Anthropic: native sign-in versus credential intermediation

[Claude Code legal and compliance](https://code.claude.com/docs/en/legal-and-compliance), accessed 2026-10-03, explicitly preserves an end user's own subscription sign-in to the unmodified Claude Code binary. It also describes hosting that binary in products, subject to Commercial Terms, preserving built-in authentication methods and each user authenticating/bearing their own usage. Developers must not collect or intermediate Claude.ai credentials or route users' requests through Free/Pro/Max credentials. Products using Claude capabilities, including SDK products, are directed toward API keys or supported cloud providers. This is not permission to implement a substitute Claude.ai login inside Qualia.

Exact excerpt: “sign-in to a Claude account must complete through Anthropic’s own flow.”

The page ties advertised Pro/Max capacity to ordinary individual Claude Code/Agent SDK use; it is not an unlimited automated workload entitlement. Free/Pro/Max and Team/Enterprise/API use have different governing agreements. These distinctions require reassessment before distributing or hosting an integration; this review establishes no commercial agreement acceptance or provider endorsement.

| Official source, accessed 2026-10-03 | What it establishes |
| --- | --- |
| [Run Claude Code programmatically](https://code.claude.com/docs/en/headless) | Documents `claude -p` and Python/TypeScript Agent SDK interfaces, including scripts and structured output. It warns that normal print mode can load hooks/MCP configuration without interactive trust prompts. Current recommended bare mode does not use subscription login. Qualia's prohibition on `--bare` remains unchanged; this source is not an activation recipe. |
| [Authentication](https://code.claude.com/docs/en/authentication), Generate a long-lived token | Documents an official subscription-backed CI/script token flow for eligible plans. This establishes that some script authentication is explicitly supported, not permission for a third-party application to collect that token. No such token was requested or created here. |
| [CLI reference](https://code.claude.com/docs/en/cli-reference) | Describes `--max-turns` as an agentic-turn limit and `--max-budget-usd` as an API-spend limit. Neither description establishes one HTTP request per invocation or a total generation-token ceiling for Qualia. |
| [Consumer Terms](https://www.anthropic.com/legal/consumer-terms) | The retrieved page was the EEA/Swiss consumer variant, effective 2025-10-08; it is not asserted to be the owner's applicable regional agreement. It prohibits credential/account sharing and automated access except API-key access or otherwise explicit permission, as well as bypassing protective systems. The applicable regional and account terms must be checked before making a contractual conclusion. |

## Consequences for Qualia

The intended boundary is an owner-controlled local invocation of a genuine provider CLI, with authentication completed through that CLI's official flow. Qualia must not read subscription token files, expose them to its UI, implement an authentication proxy, share the owner's entitlement, or evade provider limits. SDK documentation is not a shortcut around those requirements.

The existing [CLI evidence](cli-classification.md) remains controlling for implementation readiness: Claude 2.1.284 can issue multiple model requests within a bounded invocation; Codex 0.160.0 has unresolved generation-token and authentication-retry accounting limits. Operator filesystem isolation is a separate requirement. Current rolling documentation does not erase those version-specific observations.

Before any future activation: resolve those engineering gates, recheck the provider's current documentation against the exact installed version and intended personal/product use, and obtain any genuinely required owner/provider decision. Until then, manual work, rules and fake backends remain the supported offline paths. No subscription-policy approval, successful live subscription classification, or production-native readiness is claimed by this research.
