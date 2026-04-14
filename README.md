# Email Creating Agent

An AI agent that generates professional, brand-customized marketing emails using the MiniMax API. Unlike a simple LLM call, it runs a real agent loop: the model drafts the email, validates it, generates images when needed, self-corrects any issues, and saves the result — all driven by tool calls.

## Features

- **Real agent loop** — up to 20 LLM turns; the model decides what tools to call and when
- **Self-validating** — agent calls `validate_email` after drafting, reads the issues, fixes them, and re-validates until it passes
- **LLM content review** — agent calls `review_email` after structural validation; a separate LLM acts as a senior reviewer checking subject line quality, brand voice, copy conciseness, and CTA clarity — fixes and re-reviews until it passes
- **Brand-aware generation** — respects brand colors, fonts, voice, and guidelines
- **Multiple email types** — promotional, seasonal, loyalty reward, re-engagement, welcome, transactional, and more
- **Smart image handling** — uses product URLs for product emails, generates mood images via AI for seasonal/re-engagement/welcome types, omits images for transactional
- **MJML output** — valid, mobile-first responsive email templates
- **Flexible brand management** — choose from pre-configured brands or enter a custom brand at runtime; color picker included for easy primary color selection
- **Resilient API calls** — automatic retry with backoff on transient MiniMax API errors

## Requirements

- Python 3.10+
- MiniMax API key

## Installation

```bash
git clone https://github.com/Astersss/email-creating-agent.git
cd email-creating-agent

python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

## Configuration

### API Key (required)

The app reads your MiniMax API key from the `MINIMAX_API_KEY` environment variable. It will not start without it.

```bash
export MINIMAX_API_KEY="sk-..."
```

To make this permanent, add the line above to your `~/.zshrc` or `~/.bashrc`.

> **Never hardcode your API key in source files or commit it to version control.**

### Model (optional)

Edit `config.json` to change the MiniMax model (default: `MiniMax-M2.7`).

**Brands**: add entries to `brands.json` to pre-configure additional brands. Custom brands can also be entered interactively at runtime.

## Usage

```bash
python main.py
```

The CLI will walk you through:

1. Selecting a brand (or entering a custom one)
2. Specifying email type, classification, target audience, and campaign goal
3. Providing a product image URL (for promotional/product emails)

The agent then runs autonomously — drafting, validating, fixing issues, generating images if needed, and saving.

Output files are saved to the `output/` directory:

- `{brand}_{type}_{timestamp}.mjml` — MJML template for preview
- `{brand}_{type}_{timestamp}_package.json` — full package (subject lines, preheader, MJML, rationale, image_url)

## Email Types & Image Strategies

| Email Type | Image Strategy |
|---|---|
| promotional, sale, product launch, new arrival | Uses provided product image URL |
| seasonal, loyalty reward, re-engagement, welcome, milestone | AI-generated mood image |
| transactional, newsletter | No image |

## How the agent works

```
User input
    │
    ▼
LLM drafts MJML email
    │
    ▼
validate_email()  ◄─── fixes & retries if structural issues found
    │ no issues
    ▼
review_email()    ◄─── fixes & retries if content/brand issues found
    │ no issues
    ▼
generate_image()  (mood/product emails only)
    │
    ▼
save_email()  → injects image URL, strips orphaned placeholders, writes files
```

The model drives the loop. Each tool result is fed back so the agent can read it and decide the next step.

## MJML validation checks

The `validate_email` tool catches:

| Check | What it catches |
|-------|----------------|
| XML well-formedness | Unclosed tags, mismatched tags, unescaped characters |
| Tag whitelist | Invented or MJML-3-only tags (`mj-carousel`, `<div>`, etc.) |
| Image placeholder | Missing `{{IMAGE_URL}}` for email types that require an image |
| External placeholder URLs | `picsum.photos`, `via.placeholder.com`, etc. in `src` attributes |
| Nesting | `mj-text`/`mj-button`/`mj-image` directly under `mj-section` instead of `mj-column` |
| Font sizes | Any `font-size` exceeding 32px |

## Project structure

```
email-creating-agent/
├── main.py          # CLI entry point and output management
├── agent.py         # EmailAgent: tool definitions, agent loop, validation
├── brand.py         # BrandConfig dataclass and JSON loaders
├── prompts.py       # System prompt and user prompt builder
├── brands.json      # Pre-configured brand database
├── config.json      # Model selection (default: MiniMax-M2.7)
├── requirements.txt
├── output/          # Generated email files (git-ignored)
└── tests/           # Unit tests
```

## Running Tests

```bash
pytest
pytest -v                        # verbose
pytest tests/test_agent.py       # single file
```

## Output example

```json
{
  "subject_lines": [
    "Your new seasonal favorite has arrived",
    "Exclusive taste test: Try it before anyone else",
    "Limited-time seasonal drink, just for Rewards members"
  ],
  "preheader": "A new seasonal drink crafted for you — available now...",
  "mjml": "<mjml>...</mjml>",
  "rationale": "Hero section opens with brand green (#00704A)...",
  "image_url": "https://cdn.minimax.io/..."
}
```
