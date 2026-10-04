# Jev setup for Qualia

Checked 2026-10-03 (America/Denver). Jev is an optional classifier with its own TypeSafe account and usage billing. This guide covers setup on a new installation.

Implementation and test evidence is recorded in [BUILD-STATE.md](BUILD-STATE.md).

**This installation is now verified:** after you saved the key and requested the remaining setup, two tiny synthetic requests succeeded on 2026-10-03. The demo project has Jev/external processing enabled with its existing $1 daily local limit; new projects still default to off. Recorded combined test cost was $0.00003570. Account balance and billing controls were not changed. The steps below remain the installation guide for other devices and users.

## 1. Check your account and spending settings

1. Open the [TypeSafe console](https://console.typesafe.ai/) in your own browser and sign in to the account you created.
2. Find the account's billing or credits area. Check the available balance and the purchase amount before paying. The authenticated screen and its exact labels have not been inspected here.
3. If the balance is zero and the console requires purchased credits, choose the smallest amount you are comfortable spending and complete payment yourself. Account creation alone does not prove that usable credits exist.
4. Leave automatic credit refills disabled unless you deliberately want recurring replenishment. Check for an existing refill setting as well as a checkbox during checkout.

TypeSafe's agreement describes purchased credits, discretionary promotional credits, and opt-in automatic refills. It does **not** establish that every new account receives free credit. Your actual balance, minimum purchase, taxes, and payment status are account-specific. [Customer agreement, §8.2](https://typesafe.ai/legal/mca)

The published Jev 1.13 rate is **$0.042 per million input tokens**, with output tokens free. At that rate, 10,000 billed input tokens cost $0.00042; this is an estimate of token usage charges, not the minimum amount you can purchase. Check the displayed account terms before payment. [Current model pricing](https://docs.typesafe.ai/models)

## 2. Create a dedicated key

1. In the console, locate **API Keys** (the project owner's manual uses this label; the current signed-in layout is unverified).
2. Create a key for this installation. If a name is offered, use `Qualia local` so you can identify and revoke it later.
3. Save the full key in your password manager when it is shown. Do not assume the console will show it again.
4. Do not paste the key in this chat, a screenshot, a GitHub issue, or any frontend configuration file.

The official quick start directs you to obtain the key from the dashboard; API authentication uses a bearer key. [TypeSafe quick start](https://docs.typesafe.ai/introduction/quickstart)

## 3. Put the key in the local environment file

Open PowerShell and run:

```powershell
notepad "C:\Users\Owner\OneDrive\Documents\Qualia\.env"
```

If Notepad asks to create the file, allow it. Preserve any existing lines. Find the existing `TYPESAFE_API_KEY=` line and replace only its value, or add the line once if it is absent:

```dotenv
TYPESAFE_API_KEY=PASTE_YOUR_ACTUAL_KEY_HERE
```

Replace the placeholder in Notepad, then save. Do not put the actual key into a PowerShell command; that can leave it in shell history. If using **Save As**, choose **All Files**, filename `.env`, and the Qualia folder shown above; avoid `.env.txt`.

The repository's `.gitignore` excludes `.env`. To check this without displaying its contents:

```powershell
git -C "C:\Users\Owner\OneDrive\Documents\Qualia" check-ignore .env
```

Expected output is `.env`. If it prints nothing, do not stage or commit the file; ask the coding agent to repair the ignore configuration. Never edit `.env.example` to contain the real key. These are Qualia's local secret-handling rules, not TypeSafe account requirements.

## 4. Verify the installed adapter

From PowerShell in the application folder, run:

```powershell
Set-Location "C:\Users\Owner\OneDrive\Documents\Qualia"
uv run qualia jev check --project demo
```

This sends **zero network requests** and prints only readiness, the pinned model and budget settings.
After saving a valid-looking key, `key_configured` should be `true`; this does not yet prove authentication
or credit balance. `allow_external` and `jev_enabled` stay `false` until you explicitly enable a project.
The per-request reservation is at most $0.002752512 under the currently published input-token rate;
the default daily local limit is $1.00. The ledger charges the returned usage, or conservatively retains
the reservation when actual usage is unknown. These are local safeguards, not changes to account billing.

For a first tiny, non-sensitive live check, use a separate synthetic project:

```powershell
uv run qualia init jev-check
uv run qualia codebook add Possibility --definition "Language describing a possible positive change." --project jev-check
uv run qualia codebook freeze --project jev-check
$samplePath = Join-Path $env:TEMP 'qualia-jev-smoke.txt'
Set-Content -LiteralPath $samplePath -Value 'I could try a different approach tomorrow.' -Encoding utf8
uv run qualia import $samplePath --project jev-check
uv run qualia jev enable --project jev-check
uv run qualia classify --project jev-check --backend jev --model jev-1.13.0
uv run qualia jev disable --project jev-check
```

`enable` is the explicit choice to permit external processing for that project; it preserves the budgets.
`disable` turns external AI and Jev off again. The main demo and other projects are unaffected.
If you prefer the agent to perform the live check, say only **“The Jev key is saved in .env; run the
synthetic live check.”** Never include the key. Your current installation has already passed this check; another user/device needs its own local key and verification.

Success means a synthetic, non-sensitive request returns a validated answer, records the returned model ID and token usage, and never prints the key. Jev remains off by default. Saving a key must not turn on external processing for existing projects; a project still needs an explicit egress setting and a deliberate backend choice.

If verification fails, report only the sanitized status: `401` means missing or invalid authentication; `422` means an invalid request; `429` means rate limiting; `529` means temporary overload. Billing failures need the console's balance checked. Never paste a raw request header or full error dump containing research text. [API errors](https://docs.typesafe.ai/api)

## 5. Choose suitable data

For ordinary accounts, do not assume zero retention. TypeSafe publicly offers zero data retention for enterprise customers through sales. Its privacy policy describes US hosting and retention according to business need rather than a fixed deletion window. [Enterprise ZDR](https://docs.typesafe.ai/legal), [privacy policy](https://typesafe.ai/legal/privacy-policy)

Qualia's default is therefore synthetic or non-sensitive/de-identified material only for this optional backend. The app should keep external processing disabled for a project until you choose otherwise. De-identification is your research decision; an API key or a low price does not establish permission to send a transcript.

For technical details and what was independently verified, see [Jev API research](research/jev.md).
