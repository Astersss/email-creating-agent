# Email Agent Design Spec
**Date:** 2026-04-09
**Project:** Email Creating Agent

---

## Overview

An AI agent that generates high-performing marketing/promotional emails. Given structured campaign inputs, the agent produces a full email package: valid MJML markup, subject line options, preheader text, and a rationale for the design choices. Powered by the MiniMax LLM API.

---

## Inputs

The agent accepts four fields describing the campaign:

| Field | Description | Example |
|---|---|---|
| `email_type` | Category of email | `"promotional"` |
| `email_classification` | Audience segment type | `"B2C"` |
| `target_customers` | Who receives the email | `"Starbucks loyalty members aged 18-35, coffee and tea enthusiasts"` |
| `goal` | Campaign objective | `"Drive trial purchases of a newly launched seasonal drink"` |

For Phase 1, these are hardcoded in `main.py` using the Starbucks promo scenario above.

---

## Output

The agent produces two output files in `output/`, named using brand ID, email type slug, and timestamp:

### `output/<brand-id>_<email-type>_<YYYYMMDD_HHMM>_package.json`
```json
{
  "subject_lines": ["Option 1", "Option 2", "Option 3"],
  "preheader": "Short preview text shown in inbox",
  "mjml": "<mjml>...</mjml>",
  "rationale": "Brief explanation of design and copy decisions"
}
```

### `output/<brand-id>_<email-type>_<YYYYMMDD_HHMM>.mjml`
The MJML string extracted from the package, saved separately for easy rendering/previewing.

Example: `output/starbucks_promotional_20260409_1944.mjml`

---

## Architecture

Single-prompt agent — one LLM call with a carefully engineered system prompt.

```
[Input: type, classification, target, goal]
        │
        ▼
┌──────────────────────────┐
│  EmailAgent              │
│  - Builds system prompt  │
│  - Builds user prompt    │
│  - Calls MiniMax API     │
│  - Parses JSON response  │
└──────────────────────────┘
        │
        ▼
[Structured JSON response]
  - subject_lines: [3 options]
  - preheader: string
  - mjml: full MJML string
  - rationale: string
        │
        ▼
[Saved to output/]
```

---

## File Structure

```
email-creating-agent/
├── main.py              # Entry point — interactive CLI, runs agent, saves output
├── agent.py             # EmailAgent class — prompt construction, API call, response parsing
├── prompts.py           # System prompt and user prompt templates
├── brand.py             # BrandConfig dataclass + load_brands() / load_model()
├── brands.json          # Brand registry
├── config.json          # Active model configuration
├── output/
│   ├── <brand-id>_<email-type>_<YYYYMMDD_HHMM>.mjml          # Generated MJML
│   └── <brand-id>_<email-type>_<YYYYMMDD_HHMM>_package.json  # Full output package
└── requirements.txt     # httpx
```

---

## System Prompt Design

The system prompt instructs the model to act as an expert email marketer and MJML developer. Key directives:

- **MJML 4 compliance** — use only valid MJML tags: `mj-section`, `mj-column`, `mj-text`, `mj-button`, `mj-image`, `mj-divider`, `mj-spacer`, `mj-attributes`, `mj-all`
- **Email best practices** — single clear CTA, above-the-fold hook, benefit-led headline, urgency/scarcity where appropriate, mobile-first layout
- **Generic clean style** — no brand colors or logos; use a clean, professional aesthetic that works across brands
- **Structured JSON output only** — the model must return a single JSON object with exactly four keys: `subject_lines`, `preheader`, `mjml`, `rationale`. No prose outside the JSON.

---

## User Prompt Template

```
You are creating a marketing email with the following details:

Email type: {email_type}
Classification: {email_classification}
Target customers: {target_customers}
Goal: {goal}

Return a single JSON object with keys: subject_lines (array of 3 strings), preheader (string), mjml (string), rationale (string).
```

---

## MiniMax API Integration

- **Endpoint:** `https://api.minimaxi.chat/v1/text/chatcompletion_v2`
- **Model:** `MiniMax-Text-01`
- **Auth:** Bearer token via `MINIMAX_API_KEY` environment variable (key provided separately)
- **HTTP client:** `httpx` (synchronous)
- **Response format:** JSON mode (`response_format: { type: "json_object" }`) to ensure parseable output
- **Error handling:** raise on non-200 status, print clear error message

---

## Phase 1 Scope

- Single hardcoded Starbucks promo scenario
- Script run via `python main.py`
- Output printed to console and saved to `output/`
- No brand customization, no web UI, no CLI flags

## Future Phases (out of scope for Phase 1)

- Accept dynamic inputs via CLI args or a web form
- Brand customization (colors, logo, fonts)
- Multi-step chain (strategist → builder → copywriter)
- MJML rendering preview (compile to HTML)
- Evaluation/scoring of generated emails
