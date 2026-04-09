# Phase 2A: Enhanced Agent Design Spec
**Date:** 2026-04-09
**Project:** Mithra — AI Email Agent

---

## Overview

Upgrade the email agent from a hardcoded script to an interactive CLI tool that supports multiple brands. Users are prompted for campaign details at runtime. Brand identity (primary color, optional logo) is loaded from a config file and injected into the prompt, producing brand-styled MJML output. The active MiniMax model is globally configurable via `config.json` for easy model comparison.

---

## What Changes vs Phase 1

| Concern | Phase 1 | Phase 2A |
|---|---|---|
| Interface | Hardcoded `main.py` | Interactive CLI |
| Brand | None (generic style) | `brands.json` + custom entry |
| Model | Hardcoded `MiniMax-Text-01` | `config.json`, switchable |
| Output naming | `email.mjml` | `<brand-id>_email.mjml` |
| Prompt | Static system prompt | Brand-aware user prompt |

---

## New Files

### `brands.json`
Pre-defined brand registry. Users edit this file to add brands.

```json
{
  "brands": [
    {
      "id": "starbucks",
      "name": "Starbucks",
      "primary_color": "#00704A",
      "logo_url": null
    }
  ]
}
```

Fields:
- `id` — slug used for output file naming (e.g. `starbucks_email.mjml`)
- `name` — display name shown in CLI
- `primary_color` — hex color for buttons, headers, dividers (optional)
- `logo_url` — URL of brand logo image, added as `mj-image` at top of email (optional)

### `config.json`
Global model configuration.

```json
{
  "model": "MiniMax-Text-01"
}
```

To compare models, edit `model` and re-run.

### `brand.py`
`BrandConfig` dataclass and config loaders.

```python
@dataclass
class BrandConfig:
    id: str
    name: str
    primary_color: str | None = None
    logo_url: str | None = None

def load_brands() -> list[BrandConfig]:
    """Load brands from brands.json."""

def load_model() -> str:
    """Load active model name from config.json."""
```

---

## Modified Files

### `prompts.py`

**`SYSTEM_PROMPT`:** Remove the hardcoded "no brand colors or logos" rule. Keep all MJML and best-practice rules.

**`build_user_prompt()`:** Add `brand: BrandConfig` parameter. Inject brand fields conditionally:

```
Create a marketing email with the following details:

Brand: {brand.name}
Primary color: {brand.primary_color}    ← only if set
Logo URL: {brand.logo_url}              ← only if set

Email type: {email_type}
Classification: {email_classification}
Target customers: {target_customers}
Goal: {goal}

Brand styling instructions:
- Use {primary_color} as the accent color for buttons, headers, and dividers
- If a logo URL is provided, add it as mj-image at the top of the email
- If no color is provided, use a clean neutral palette (#333333 for text, #0066CC for buttons)

Return a single JSON object with keys: subject_lines, preheader, mjml, rationale.
```

### `agent.py`

`generate()` signature extends to:
```python
def generate(
    self,
    brand: BrandConfig,
    email_type: str,
    email_classification: str,
    target_customers: str,
    goal: str,
    model: str,
) -> dict:
```

- `model` replaces the hardcoded `MINIMAX_MODEL` constant in the API payload
- `brand` is passed through to `build_user_prompt()`

### `main.py`

Replaced entirely with interactive CLI:

```
=== Email Agent ===

Available brands:
  1. Starbucks
  0. Enter custom brand

Select brand [0-1]: 1

Brand: Starbucks (#00704A)

Email type: promotional
Email classification: B2C
Target customers: ...
Goal: ...

Generating email...

=== SUBJECT LINES ===  ...
=== PREHEADER ===  ...
=== RATIONALE ===  ...
=== OUTPUT FILES ===
  MJML:    output/starbucks_email.mjml
  Package: output/starbucks_email_package.json
```

Custom brand flow (option 0):
```
Brand name: Nike
Primary color (hex, optional): #111111
Logo URL (optional):
```
Custom brands get `id` derived from name (lowercased, spaces → underscores).

---

## Output File Naming

Files are saved as `output/<brand-id>_email.mjml` and `output/<brand-id>_email_package.json`. Multiple brands can be generated without overwriting each other.

The `.gitignore` already excludes `output/email.mjml` and `output/email_package.json` — update it to exclude `output/*_email.mjml` and `output/*_email_package.json`.

---

## Phase 2A Scope

- Interactive CLI replacing hardcoded `main.py`
- Brand config: pre-defined brands in `brands.json` + custom entry
- Brand fields: name + primary color (required), logo URL (optional)
- Model: globally configurable via `config.json`
- Output naming: per-brand file names

## Out of Scope (future phases)

- Web UI
- Brand validation (color format checking)
- Multiple simultaneous brand generation
- Email evaluation (Phase 2B)
