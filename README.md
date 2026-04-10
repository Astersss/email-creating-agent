# Email Creating Agent

An AI-powered CLI tool that generates professional, brand-customized marketing emails using the MiniMax API. It produces complete email packages including subject lines, preheaders, responsive MJML templates, and design rationale.

## Features

- **Brand-aware generation** — respects brand colors, fonts, voice, and guidelines
- **Multiple email types** — promotional, seasonal, loyalty reward, re-engagement, welcome, transactional, and more
- **Smart image handling** — uses product URLs, generates mood images via AI, or omits images based on email type
- **MJML output** — valid, mobile-first responsive email templates
- **Flexible brand management** — choose from pre-configured brands or enter a custom brand at runtime

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

Output files are saved to the `output/` directory:

- `{brand}_{type}_{timestamp}.mjml` — MJML template for preview
- `{brand}_{type}_{timestamp}_package.json` — full package (subject lines, preheader, MJML, rationale)

## Email Types & Image Strategies

| Email Type | Image Strategy |
|---|---|
| promotional, sale, product launch, new arrival | Uses provided product image URL |
| seasonal, loyalty reward, re-engagement, welcome, milestone | AI-generated mood image |
| transactional, newsletter | No image |

## Project Structure

```
email-creating-agent/
├── main.py          # CLI entry point and output management
├── agent.py         # EmailAgent: API calls and image resolution
├── brand.py         # BrandConfig dataclass and JSON loaders
├── prompts.py       # System and user prompt templates
├── brands.json      # Pre-configured brand database
├── config.json      # Model selection
├── requirements.txt
├── output/          # Generated email files
└── tests/           # Unit and integration tests
```

## Running Tests

```bash
pytest
pytest -v                        # verbose
pytest tests/test_agent.py       # single file
```

## Output Example

```json
{
  "subject_lines": [
    "Your new seasonal favorite has arrived",
    "Exclusive taste test: Try it before anyone else",
    "Limited-time seasonal drink, just for Rewards members"
  ],
  "preheader": "A new seasonal drink crafted for you — available now...",
  "mjml": "<mjml>...</mjml>",
  "rationale": "Hero section opens with brand green (#00704A)..."
}
```
