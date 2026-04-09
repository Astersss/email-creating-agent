# Phase 2A: Enhanced Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the email agent from a hardcoded script to an interactive CLI with multi-brand support and switchable model configuration.

**Architecture:** Brand configs live in `brands.json`, model config in `config.json`, loaded by a new `brand.py` module. `prompts.py` and `agent.py` gain brand+model parameters. `main.py` is replaced with an interactive CLI that prompts the user to pick a brand and enter campaign details.

**Tech Stack:** Python 3.12, httpx, pytest, stdlib only (no new dependencies)

---

## File Map

| File | Change | Responsibility |
|---|---|---|
| `brands.json` | Create | Pre-defined brand registry |
| `config.json` | Create | Global model setting |
| `brand.py` | Create | `BrandConfig` dataclass + `load_brands()` + `load_model()` |
| `prompts.py` | Modify | Brand-aware `build_user_prompt(brand, ...)` |
| `agent.py` | Modify | `generate(brand, ..., model)` — remove hardcoded model |
| `main.py` | Replace | Interactive CLI |
| `.gitignore` | Modify | Wildcard output file exclusions |
| `tests/test_brand.py` | Create | Tests for brand.py |
| `tests/test_prompts.py` | Modify | Update for new `build_user_prompt` signature |
| `tests/test_agent.py` | Modify | Update for new `generate` signature |
| `tests/test_main.py` | Create | Tests for `make_brand_id` and `save_output` |

---

## Task 1: Brand Config Files + BrandConfig Module

**Files:**
- Create: `brands.json`
- Create: `config.json`
- Create: `brand.py`
- Create: `tests/test_brand.py`

- [ ] **Step 1: Create brands.json**

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

- [ ] **Step 2: Create config.json**

```json
{
  "model": "MiniMax-Text-01"
}
```

- [ ] **Step 3: Write failing tests**

Create `tests/test_brand.py`:

```python
import json
import pytest
from brand import BrandConfig, load_brands, load_model


def test_brand_config_required_fields():
    brand = BrandConfig(id="test", name="Test Brand")
    assert brand.id == "test"
    assert brand.name == "Test Brand"
    assert brand.primary_color is None
    assert brand.logo_url is None


def test_brand_config_all_fields():
    brand = BrandConfig(
        id="sb",
        name="Starbucks",
        primary_color="#00704A",
        logo_url="https://example.com/logo.png",
    )
    assert brand.primary_color == "#00704A"
    assert brand.logo_url == "https://example.com/logo.png"


def test_load_brands(tmp_path):
    brands_file = tmp_path / "brands.json"
    brands_file.write_text(
        json.dumps({
            "brands": [
                {"id": "starbucks", "name": "Starbucks", "primary_color": "#00704A", "logo_url": None}
            ]
        }),
        encoding="utf-8",
    )
    brands = load_brands(path=brands_file)
    assert len(brands) == 1
    assert brands[0].id == "starbucks"
    assert brands[0].name == "Starbucks"
    assert brands[0].primary_color == "#00704A"
    assert brands[0].logo_url is None


def test_load_brands_multiple(tmp_path):
    brands_file = tmp_path / "brands.json"
    brands_file.write_text(
        json.dumps({
            "brands": [
                {"id": "a", "name": "Brand A", "primary_color": "#FF0000", "logo_url": None},
                {"id": "b", "name": "Brand B", "primary_color": None, "logo_url": None},
            ]
        }),
        encoding="utf-8",
    )
    brands = load_brands(path=brands_file)
    assert len(brands) == 2
    assert brands[1].id == "b"
    assert brands[1].primary_color is None


def test_load_model(tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"model": "MiniMax-Text-01"}), encoding="utf-8")
    assert load_model(path=config_file) == "MiniMax-Text-01"


def test_load_model_custom(tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"model": "MiniMax-M1"}), encoding="utf-8")
    assert load_model(path=config_file) == "MiniMax-M1"
```

- [ ] **Step 4: Run tests to verify they fail**

```bash
cd /Users/asun/Documents/mithra && .venv/bin/pytest tests/test_brand.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'brand'`

- [ ] **Step 5: Implement brand.py**

Create `brand.py`:

```python
import json
from dataclasses import dataclass
from pathlib import Path

BRANDS_FILE = Path(__file__).parent / "brands.json"
CONFIG_FILE = Path(__file__).parent / "config.json"


@dataclass
class BrandConfig:
    id: str
    name: str
    primary_color: str | None = None
    logo_url: str | None = None


def load_brands(path: Path = BRANDS_FILE) -> list[BrandConfig]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [BrandConfig(**b) for b in data["brands"]]


def load_model(path: Path = CONFIG_FILE) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["model"]
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
cd /Users/asun/Documents/mithra && .venv/bin/pytest tests/test_brand.py -v
```

Expected: all 6 tests PASS

- [ ] **Step 7: Commit**

```bash
cd /Users/asun/Documents/mithra && git add brands.json config.json brand.py tests/test_brand.py && git commit -m "feat: add brand config files and BrandConfig module"
```

---

## Task 2: Brand-Aware Prompts

**Files:**
- Modify: `prompts.py`
- Modify: `tests/test_prompts.py`

- [ ] **Step 1: Replace prompts.py in full**

```python
from brand import BrandConfig

SYSTEM_PROMPT = """You are an expert email marketer and MJML developer. Your job is to create high-performing marketing emails.

MJML RULES:
- Use only valid MJML 4 tags: mjml, mj-head, mj-attributes, mj-all, mj-body, mj-section, mj-column, mj-text, mj-button, mj-image, mj-divider, mj-spacer
- Every email must start with <mjml> and end with </mjml>
- Sections contain columns, columns contain content elements
- Use mj-attributes in mj-head to set global styles (font-family, padding, color)
- Buttons must use mj-button with href="#" as placeholder

EMAIL BEST PRACTICES:
- Single, clear call-to-action (CTA)
- Benefit-led headline above the fold
- Short, punchy body copy (under 80 words)
- Create urgency or excitement without being spammy
- Mobile-first: single-column layout

OUTPUT FORMAT:
Return ONLY a valid JSON object with exactly these four keys:
- "subject_lines": array of exactly 3 subject line strings (under 50 chars each)
- "preheader": string (under 100 chars, teases the email content)
- "mjml": string (complete, valid MJML markup)
- "rationale": string (2-3 sentences explaining key design decisions)

Do not include any text outside the JSON object. Do not use markdown code fences."""


def build_user_prompt(
    brand: BrandConfig,
    email_type: str,
    email_classification: str,
    target_customers: str,
    goal: str,
) -> str:
    brand_lines = [f"Brand: {brand.name}"]
    if brand.primary_color:
        brand_lines.append(f"Primary color: {brand.primary_color}")
    if brand.logo_url:
        brand_lines.append(f"Logo URL: {brand.logo_url}")
    brand_section = "\n".join(brand_lines)

    if brand.primary_color:
        styling = (
            f"- Use {brand.primary_color} as the accent color for buttons, headers, and dividers"
        )
    else:
        styling = "- Use a clean neutral palette (#333333 for text, #0066CC for buttons)"

    if brand.logo_url:
        styling += "\n- Add the logo as mj-image at the top of the email"

    return f"""Create a marketing email with the following details:

{brand_section}

Email type: {email_type}
Classification: {email_classification}
Target customers: {target_customers}
Goal: {goal}

Brand styling instructions:
{styling}

Return a single JSON object with keys: subject_lines (array of 3 strings), preheader (string), mjml (string), rationale (string)."""
```

- [ ] **Step 2: Replace tests/test_prompts.py in full**

```python
from brand import BrandConfig
from prompts import SYSTEM_PROMPT, build_user_prompt

STARBUCKS = BrandConfig(id="starbucks", name="Starbucks", primary_color="#00704A")
MINIMAL_BRAND = BrandConfig(id="test", name="TestBrand")


def test_system_prompt_is_string():
    assert isinstance(SYSTEM_PROMPT, str)
    assert len(SYSTEM_PROMPT) > 100


def test_system_prompt_mentions_mjml():
    assert "MJML" in SYSTEM_PROMPT


def test_system_prompt_mentions_json_output():
    assert "JSON" in SYSTEM_PROMPT


def test_build_user_prompt_includes_all_campaign_fields():
    prompt = build_user_prompt(
        brand=STARBUCKS,
        email_type="promotional",
        email_classification="B2C",
        target_customers="coffee lovers aged 18-35",
        goal="drive trial of new seasonal drink",
    )
    assert "promotional" in prompt
    assert "B2C" in prompt
    assert "coffee lovers aged 18-35" in prompt
    assert "drive trial of new seasonal drink" in prompt


def test_build_user_prompt_returns_string():
    prompt = build_user_prompt(
        brand=STARBUCKS,
        email_type="promotional",
        email_classification="B2C",
        target_customers="coffee lovers",
        goal="sell more coffee",
    )
    assert isinstance(prompt, str)
    assert len(prompt) > 20


def test_build_user_prompt_field_labels_are_correct():
    prompt = build_user_prompt(
        brand=BrandConfig(id="t", name="BRAND_SENTINEL"),
        email_type="TYPE_SENTINEL",
        email_classification="CLASS_SENTINEL",
        target_customers="CUSTOMERS_SENTINEL",
        goal="GOAL_SENTINEL",
    )
    assert "Email type: TYPE_SENTINEL" in prompt
    assert "Classification: CLASS_SENTINEL" in prompt
    assert "Target customers: CUSTOMERS_SENTINEL" in prompt
    assert "Goal: GOAL_SENTINEL" in prompt


def test_build_user_prompt_includes_brand_name():
    prompt = build_user_prompt(
        brand=STARBUCKS,
        email_type="promo",
        email_classification="B2C",
        target_customers="all",
        goal="sell",
    )
    assert "Starbucks" in prompt


def test_build_user_prompt_includes_primary_color_when_set():
    prompt = build_user_prompt(
        brand=STARBUCKS,
        email_type="promo",
        email_classification="B2C",
        target_customers="all",
        goal="sell",
    )
    assert "#00704A" in prompt


def test_build_user_prompt_uses_neutral_palette_when_no_color():
    prompt = build_user_prompt(
        brand=MINIMAL_BRAND,
        email_type="promo",
        email_classification="B2C",
        target_customers="all",
        goal="sell",
    )
    assert "#0066CC" in prompt


def test_build_user_prompt_includes_logo_url_when_set():
    brand_with_logo = BrandConfig(
        id="test", name="Test", logo_url="https://example.com/logo.png"
    )
    prompt = build_user_prompt(
        brand=brand_with_logo,
        email_type="promo",
        email_classification="B2C",
        target_customers="all",
        goal="sell",
    )
    assert "https://example.com/logo.png" in prompt


def test_build_user_prompt_no_logo_section_when_logo_absent():
    prompt = build_user_prompt(
        brand=MINIMAL_BRAND,
        email_type="promo",
        email_classification="B2C",
        target_customers="all",
        goal="sell",
    )
    assert "Logo URL" not in prompt
```

- [ ] **Step 3: Run tests to verify they pass**

```bash
cd /Users/asun/Documents/mithra && .venv/bin/pytest tests/test_prompts.py -v
```

Expected: all 10 tests PASS

- [ ] **Step 4: Commit**

```bash
cd /Users/asun/Documents/mithra && git add prompts.py tests/test_prompts.py && git commit -m "feat: brand-aware prompts with dynamic color and logo injection"
```

---

## Task 3: Brand-Aware Agent

**Files:**
- Modify: `agent.py`
- Modify: `tests/test_agent.py`

- [ ] **Step 1: Replace agent.py in full**

```python
import json
import httpx
from brand import BrandConfig
from prompts import SYSTEM_PROMPT, build_user_prompt

MINIMAX_API_URL = "https://api.minimaxi.chat/v1/text/chatcompletion_v2"
REQUIRED_KEYS = {"subject_lines", "preheader", "mjml", "rationale"}


class EmailAgent:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def _parse_response(self, content: str) -> dict:
        if not isinstance(content, str):
            raise ValueError(f"Expected string content from model, got {type(content).__name__}")

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON from model: {e}")

        missing = REQUIRED_KEYS - data.keys()
        if missing:
            raise ValueError(f"Missing required keys: {missing}")

        if not isinstance(data["subject_lines"], list):
            raise ValueError("subject_lines must be a list")

        if len(data["subject_lines"]) == 0:
            raise ValueError("subject_lines must contain at least one entry")

        return data

    def generate(
        self,
        brand: BrandConfig,
        email_type: str,
        email_classification: str,
        target_customers: str,
        goal: str,
        model: str,
    ) -> dict:
        user_prompt = build_user_prompt(
            brand=brand,
            email_type=email_type,
            email_classification=email_classification,
            target_customers=target_customers,
            goal=goal,
        )

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        response = httpx.post(
            MINIMAX_API_URL,
            json=payload,
            headers=headers,
            timeout=60.0,
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"MiniMax API error {response.status_code}: {response.text}"
            )

        body = response.json()
        choices = body.get("choices")
        if not choices:
            raise RuntimeError(f"MiniMax API returned no choices: {body}")
        message = choices[0].get("message", {})
        content = message.get("content")
        if content is None:
            raise RuntimeError(f"MiniMax API choice missing content: {choices[0]}")
        return self._parse_response(content)
```

- [ ] **Step 2: Replace tests/test_agent.py in full**

```python
import json
import pytest
from unittest.mock import MagicMock, patch
from brand import BrandConfig
from agent import EmailAgent

STARBUCKS = BrandConfig(id="starbucks", name="Starbucks", primary_color="#00704A")

VALID_PACKAGE = {
    "subject_lines": ["Try our new drink", "New arrival at Starbucks", "Sip something new"],
    "preheader": "A bold new flavor is here — made for you.",
    "mjml": "<mjml><mj-body><mj-section><mj-column><mj-text>Hello</mj-text></mj-column></mj-section></mj-body></mjml>",
    "rationale": "Single CTA drives click-through. Benefit-led headline creates curiosity.",
}


def test_parse_response_valid_json():
    agent = EmailAgent(api_key="test-key")
    result = agent._parse_response(json.dumps(VALID_PACKAGE))
    assert result["subject_lines"] == VALID_PACKAGE["subject_lines"]
    assert result["preheader"] == VALID_PACKAGE["preheader"]
    assert result["mjml"] == VALID_PACKAGE["mjml"]
    assert result["rationale"] == VALID_PACKAGE["rationale"]


def test_parse_response_raises_on_invalid_json():
    agent = EmailAgent(api_key="test-key")
    with pytest.raises(ValueError, match="Invalid JSON"):
        agent._parse_response("this is not json")


def test_parse_response_raises_on_missing_keys():
    agent = EmailAgent(api_key="test-key")
    incomplete = {"subject_lines": ["a"], "preheader": "b"}
    with pytest.raises(ValueError, match="Missing required keys"):
        agent._parse_response(json.dumps(incomplete))


def test_parse_response_raises_on_wrong_subject_lines_type():
    agent = EmailAgent(api_key="test-key")
    bad = {**VALID_PACKAGE, "subject_lines": "not a list"}
    with pytest.raises(ValueError, match="subject_lines must be a list"):
        agent._parse_response(json.dumps(bad))


def test_agent_init_stores_api_key():
    agent = EmailAgent(api_key="my-secret-key")
    assert agent.api_key == "my-secret-key"


@patch("agent.httpx.post")
def test_generate_calls_api_and_returns_parsed_package(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": json.dumps(VALID_PACKAGE)}}]
    }
    mock_post.return_value = mock_response

    agent = EmailAgent(api_key="test-key")
    result = agent.generate(
        brand=STARBUCKS,
        email_type="promotional",
        email_classification="B2C",
        target_customers="coffee lovers",
        goal="sell more coffee",
        model="MiniMax-Text-01",
    )
    assert result == VALID_PACKAGE
    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args.kwargs
    assert call_kwargs["json"]["model"] == "MiniMax-Text-01"


@patch("agent.httpx.post")
def test_generate_uses_provided_model(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": json.dumps(VALID_PACKAGE)}}]
    }
    mock_post.return_value = mock_response

    agent = EmailAgent(api_key="test-key")
    agent.generate(
        brand=STARBUCKS,
        email_type="promo",
        email_classification="B2C",
        target_customers="all",
        goal="sell",
        model="MiniMax-M1",
    )
    call_kwargs = mock_post.call_args.kwargs
    assert call_kwargs["json"]["model"] == "MiniMax-M1"


@patch("agent.httpx.post")
def test_generate_raises_on_non_200(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.text = "rate limit"
    mock_post.return_value = mock_response

    agent = EmailAgent(api_key="test-key")
    with pytest.raises(RuntimeError, match="MiniMax API error 429"):
        agent.generate(
            brand=STARBUCKS,
            email_type="promo",
            email_classification="B2C",
            target_customers="all",
            goal="sell",
            model="MiniMax-Text-01",
        )
```

- [ ] **Step 3: Run tests to verify they pass**

```bash
cd /Users/asun/Documents/mithra && .venv/bin/pytest tests/test_agent.py -v
```

Expected: all 8 tests PASS

- [ ] **Step 4: Run full test suite**

```bash
cd /Users/asun/Documents/mithra && .venv/bin/pytest tests/ -v
```

Expected: all tests PASS (test_brand + test_prompts + test_agent)

- [ ] **Step 5: Commit**

```bash
cd /Users/asun/Documents/mithra && git add agent.py tests/test_agent.py && git commit -m "feat: agent accepts brand and model params, removes hardcoded model"
```

---

## Task 4: Interactive CLI + gitignore

**Files:**
- Replace: `main.py`
- Create: `tests/test_main.py`
- Modify: `.gitignore`

- [ ] **Step 1: Write failing tests for main.py helpers**

Create `tests/test_main.py`:

```python
import json
import pytest
from unittest.mock import patch
from main import make_brand_id, save_output

VALID_PACKAGE = {
    "subject_lines": ["Sub 1", "Sub 2", "Sub 3"],
    "preheader": "A great email",
    "mjml": "<mjml><mj-body></mj-body></mjml>",
    "rationale": "Good design choices.",
}


def test_make_brand_id_lowercases():
    assert make_brand_id("Nike") == "nike"


def test_make_brand_id_replaces_spaces():
    assert make_brand_id("My Brand") == "my_brand"


def test_make_brand_id_strips_whitespace():
    assert make_brand_id("  Nike  ") == "nike"


def test_save_output_writes_mjml(tmp_path):
    with patch("main.OUTPUT_DIR", tmp_path):
        mjml_path, _ = save_output("starbucks", VALID_PACKAGE)
    assert mjml_path.read_text(encoding="utf-8") == VALID_PACKAGE["mjml"]


def test_save_output_writes_package_json(tmp_path):
    with patch("main.OUTPUT_DIR", tmp_path):
        _, package_path = save_output("starbucks", VALID_PACKAGE)
    data = json.loads(package_path.read_text(encoding="utf-8"))
    assert data == VALID_PACKAGE


def test_save_output_uses_brand_id_in_filename(tmp_path):
    with patch("main.OUTPUT_DIR", tmp_path):
        mjml_path, package_path = save_output("nike", VALID_PACKAGE)
    assert mjml_path.name == "nike_email.mjml"
    assert package_path.name == "nike_email_package.json"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/asun/Documents/mithra && .venv/bin/pytest tests/test_main.py -v
```

Expected: FAIL — `make_brand_id` and `save_output` not yet in `main.py`

- [ ] **Step 3: Replace main.py in full**

```python
import json
import os
from pathlib import Path
from brand import BrandConfig, load_brands, load_model
from agent import EmailAgent

MINIMAX_API_KEY = "sk-api-A3aHSpnsft2LIJcji5z45FFC4Qx3S0Ed8RV7LuTJSJC1XH9XcWN1Adw6HjJS2mrljHSQqyowBR1Hph9g65simY8d_5ypq6C7ka8_6dolS8iDR5pBS3AdtCI"
OUTPUT_DIR = Path(__file__).parent / "output"


def make_brand_id(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def select_brand(brands: list[BrandConfig]) -> BrandConfig:
    print("\nAvailable brands:")
    for i, brand in enumerate(brands, 1):
        color_info = f" ({brand.primary_color})" if brand.primary_color else ""
        print(f"  {i}. {brand.name}{color_info}")
    print("  0. Enter custom brand")

    while True:
        choice = input(f"\nSelect brand [0-{len(brands)}]: ").strip()
        if choice == "0":
            return _enter_custom_brand()
        if choice.isdigit() and 1 <= int(choice) <= len(brands):
            return brands[int(choice) - 1]
        print(f"Please enter a number between 0 and {len(brands)}.")


def _enter_custom_brand() -> BrandConfig:
    name = input("Brand name: ").strip()
    color = input("Primary color (hex, optional — press Enter to skip): ").strip() or None
    logo = input("Logo URL (optional — press Enter to skip): ").strip() or None
    return BrandConfig(id=make_brand_id(name), name=name, primary_color=color, logo_url=logo)


def prompt_campaign_inputs() -> dict:
    print()
    email_type = input("Email type (e.g. promotional, announcement): ").strip()
    email_classification = input("Email classification (e.g. B2C, B2B): ").strip()
    target_customers = input("Target customers: ").strip()
    goal = input("Goal: ").strip()
    return {
        "email_type": email_type,
        "email_classification": email_classification,
        "target_customers": target_customers,
        "goal": goal,
    }


def save_output(brand_id: str, package: dict) -> tuple[Path, Path]:
    OUTPUT_DIR.mkdir(exist_ok=True)
    mjml_path = OUTPUT_DIR / f"{brand_id}_email.mjml"
    package_path = OUTPUT_DIR / f"{brand_id}_email_package.json"
    mjml_path.write_text(package["mjml"], encoding="utf-8")
    package_path.write_text(json.dumps(package, indent=2, ensure_ascii=False), encoding="utf-8")
    return mjml_path, package_path


def print_results(package: dict, mjml_path: Path, package_path: Path) -> None:
    print("\n=== SUBJECT LINES ===")
    for i, line in enumerate(package["subject_lines"], 1):
        print(f"  {i}. {line}")
    print(f"\n=== PREHEADER ===\n  {package['preheader']}")
    print(f"\n=== RATIONALE ===\n  {package['rationale']}")
    print("\n=== OUTPUT FILES ===")
    print(f"  MJML:    {mjml_path}")
    print(f"  Package: {package_path}")


def main():
    api_key = os.environ.get("MINIMAX_API_KEY", MINIMAX_API_KEY)
    brands = load_brands()
    model = load_model()

    print("=== Email Agent ===")
    brand = select_brand(brands)

    color_info = f" ({brand.primary_color})" if brand.primary_color else ""
    print(f"\nBrand: {brand.name}{color_info}")
    print(f"Model: {model}")

    inputs = prompt_campaign_inputs()

    print("\nGenerating email...")
    agent = EmailAgent(api_key=api_key)
    package = agent.generate(brand=brand, model=model, **inputs)

    mjml_path, package_path = save_output(brand.id, package)
    print_results(package, mjml_path, package_path)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Update .gitignore**

Replace the two specific output lines with wildcards:

Old lines to remove:
```
output/email.mjml
output/email_package.json
```

New lines to add:
```
output/*.mjml
output/*.json
```

The updated `.gitignore` should look like:
```
# Python
__pycache__/
*.pyc
*.pyo
.venv/

# IDE
.idea/

# Runtime output (generated at runtime, not source)
output/*.mjml
output/*.json
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd /Users/asun/Documents/mithra && .venv/bin/pytest tests/test_main.py -v
```

Expected: all 6 tests PASS

- [ ] **Step 6: Run full test suite**

```bash
cd /Users/asun/Documents/mithra && .venv/bin/pytest tests/ -v
```

Expected: all tests PASS

- [ ] **Step 7: Run the interactive CLI to verify end-to-end**

```bash
cd /Users/asun/Documents/mithra && .venv/bin/python main.py
```

When prompted:
- Select `1` for Starbucks
- Enter `promotional` for email type
- Enter `B2C` for classification
- Enter `Starbucks loyalty members aged 18-35` for target customers
- Enter `Drive trial of a new seasonal drink` for goal

Expected: subject lines, preheader, rationale printed, `output/starbucks_email.mjml` and `output/starbucks_email_package.json` created.

- [ ] **Step 8: Commit**

```bash
cd /Users/asun/Documents/mithra && git add main.py tests/test_main.py .gitignore && git commit -m "feat: interactive CLI with brand selection and per-brand output files"
```
