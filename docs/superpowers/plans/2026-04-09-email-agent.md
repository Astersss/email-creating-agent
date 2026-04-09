# Email Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python script that uses MiniMax LLM to generate a full marketing email package (MJML + subject lines + preheader + rationale) from structured campaign inputs.

**Architecture:** Single-prompt agent — one MiniMax API call with an engineered system prompt returns a JSON object containing all output fields. The script runs with hardcoded Starbucks promo inputs and saves output to `output/`.

**Tech Stack:** Python 3.12, httpx (HTTP client), pytest (tests), MJML 4 (output format), MiniMax Text API (`MiniMax-Text-01`)

---

## File Map

| File | Responsibility |
|---|---|
| `requirements.txt` | httpx, pytest |
| `prompts.py` | System prompt constant + `build_user_prompt()` function |
| `agent.py` | `EmailAgent` class — API call, response parsing |
| `main.py` | Hardcoded inputs, runs agent, prints + saves output |
| `output/<brand-id>_<email-type>_<YYYYMMDD_HHMM>.mjml` | Generated MJML (created at runtime) |
| `output/<brand-id>_<email-type>_<YYYYMMDD_HHMM>_package.json` | Full output package (created at runtime) |
| `tests/test_prompts.py` | Tests for prompt building |
| `tests/test_agent.py` | Tests for response parsing (mocked API) |

---

## Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `output/.gitkeep`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create requirements.txt**

```
httpx==0.27.0
pytest==8.3.5
```

- [ ] **Step 2: Create output directory placeholder**

```bash
mkdir -p /Users/asun/Documents/email-creating-agent/output
touch /Users/asun/Documents/email-creating-agent/output/.gitkeep
mkdir -p /Users/asun/Documents/email-creating-agent/tests
touch /Users/asun/Documents/email-creating-agent/tests/__init__.py
```

- [ ] **Step 3: Install dependencies**

```bash
cd /Users/asun/Documents/email-creating-agent && .venv/bin/pip install httpx==0.27.0 pytest==8.3.5
```

Expected output: `Successfully installed httpx-0.27.0 pytest-8.3.5` (versions may vary slightly)

- [ ] **Step 4: Verify install**

```bash
cd /Users/asun/Documents/email-creating-agent && .venv/bin/python -c "import httpx; import pytest; print('OK')"
```

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
cd /Users/asun/Documents/email-creating-agent && git init && git add requirements.txt output/.gitkeep tests/__init__.py && git commit -m "chore: project setup with dependencies"
```

---

## Task 2: Prompts Module

**Files:**
- Create: `prompts.py`
- Create: `tests/test_prompts.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_prompts.py`:

```python
from prompts import SYSTEM_PROMPT, build_user_prompt


def test_system_prompt_is_string():
    assert isinstance(SYSTEM_PROMPT, str)
    assert len(SYSTEM_PROMPT) > 100


def test_system_prompt_mentions_mjml():
    assert "MJML" in SYSTEM_PROMPT


def test_system_prompt_mentions_json_output():
    assert "JSON" in SYSTEM_PROMPT


def test_build_user_prompt_includes_all_fields():
    prompt = build_user_prompt(
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
        email_type="promotional",
        email_classification="B2C",
        target_customers="coffee lovers",
        goal="sell more coffee",
    )
    assert isinstance(prompt, str)
    assert len(prompt) > 20
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/asun/Documents/email-creating-agent && .venv/bin/pytest tests/test_prompts.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'prompts'`

- [ ] **Step 3: Implement prompts.py**

Create `prompts.py`:

```python
SYSTEM_PROMPT = """You are an expert email marketer and MJML developer. Your job is to create high-performing marketing emails.

MJML RULES:
- Use only valid MJML 4 tags: mj-mjml, mj-head, mj-attributes, mj-all, mj-body, mj-section, mj-column, mj-text, mj-button, mj-image, mj-divider, mj-spacer
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
- Clean, professional aesthetic — no brand colors or logos

OUTPUT FORMAT:
Return ONLY a valid JSON object with exactly these four keys:
- "subject_lines": array of exactly 3 subject line strings (under 50 chars each)
- "preheader": string (under 100 chars, teases the email content)
- "mjml": string (complete, valid MJML markup)
- "rationale": string (2-3 sentences explaining key design decisions)

Do not include any text outside the JSON object. Do not use markdown code fences."""


def build_user_prompt(
    email_type: str,
    email_classification: str,
    target_customers: str,
    goal: str,
) -> str:
    return f"""Create a marketing email with the following details:

Email type: {email_type}
Classification: {email_classification}
Target customers: {target_customers}
Goal: {goal}

Return a single JSON object with keys: subject_lines (array of 3 strings), preheader (string), mjml (string), rationale (string)."""
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /Users/asun/Documents/email-creating-agent && .venv/bin/pytest tests/test_prompts.py -v
```

Expected: all 5 tests PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/asun/Documents/email-creating-agent && git add prompts.py tests/test_prompts.py && git commit -m "feat: add prompts module with system prompt and user prompt builder"
```

---

## Task 3: Agent Response Parsing

**Files:**
- Create: `agent.py`
- Create: `tests/test_agent.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_agent.py`:

```python
import json
import pytest
from unittest.mock import MagicMock, patch
from agent import EmailAgent


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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/asun/Documents/email-creating-agent && .venv/bin/pytest tests/test_agent.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'agent'`

- [ ] **Step 3: Implement agent.py with parsing logic**

Create `agent.py`:

```python
import json
import httpx
from prompts import SYSTEM_PROMPT, build_user_prompt


MINIMAX_API_URL = "https://api.minimaxi.chat/v1/text/chatcompletion_v2"
MINIMAX_MODEL = "MiniMax-Text-01"
REQUIRED_KEYS = {"subject_lines", "preheader", "mjml", "rationale"}


class EmailAgent:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def _parse_response(self, content: str) -> dict:
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON from model: {e}")

        missing = REQUIRED_KEYS - data.keys()
        if missing:
            raise ValueError(f"Missing required keys: {missing}")

        if not isinstance(data["subject_lines"], list):
            raise ValueError("subject_lines must be a list")

        return data

    def generate(
        self,
        email_type: str,
        email_classification: str,
        target_customers: str,
        goal: str,
    ) -> dict:
        user_prompt = build_user_prompt(
            email_type=email_type,
            email_classification=email_classification,
            target_customers=target_customers,
            goal=goal,
        )

        payload = {
            "model": MINIMAX_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
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

        content = response.json()["choices"][0]["message"]["content"]
        return self._parse_response(content)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /Users/asun/Documents/email-creating-agent && .venv/bin/pytest tests/test_agent.py -v
```

Expected: all 5 tests PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/asun/Documents/email-creating-agent && git add agent.py tests/test_agent.py && git commit -m "feat: add EmailAgent with MiniMax API call and response parsing"
```

---

## Task 4: Main Script

**Files:**
- Create: `main.py`

- [ ] **Step 1: Implement main.py**

Create `main.py`:

```python
import json
import os
from pathlib import Path
from agent import EmailAgent


INPUTS = {
    "email_type": "promotional",
    "email_classification": "B2C",
    "target_customers": "Starbucks loyalty members aged 18-35, coffee and tea enthusiasts",
    "goal": "Drive trial purchases of a newly launched seasonal drink",
}

OUTPUT_DIR = Path("output")


def main():
    api_key = os.environ.get("MINIMAX_API_KEY")
    if not api_key:
        raise EnvironmentError("MINIMAX_API_KEY environment variable is not set")

    print("Generating email package...")
    print(f"Campaign: {INPUTS['goal']}")
    print(f"Audience: {INPUTS['target_customers']}\n")

    agent = EmailAgent(api_key=api_key)
    package = agent.generate(**INPUTS)

    OUTPUT_DIR.mkdir(exist_ok=True)

    mjml_path = OUTPUT_DIR / "email.mjml"
    mjml_path.write_text(package["mjml"], encoding="utf-8")

    package_path = OUTPUT_DIR / "email_package.json"
    package_path.write_text(json.dumps(package, indent=2, ensure_ascii=False), encoding="utf-8")

    print("=== SUBJECT LINES ===")
    for i, line in enumerate(package["subject_lines"], 1):
        print(f"  {i}. {line}")

    print(f"\n=== PREHEADER ===\n  {package['preheader']}")
    print(f"\n=== RATIONALE ===\n  {package['rationale']}")
    print(f"\n=== OUTPUT FILES ===")
    print(f"  MJML:    {mjml_path}")
    print(f"  Package: {package_path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Set the API key and run the script**

```bash
cd /Users/asun/Documents/email-creating-agent && MINIMAX_API_KEY=sk-api-A3aHSpnsft2LIJcji5z45FFC4Qx3S0Ed8RV7LuTJSJC1XH9XcWN1Adw6HjJS2mrljHSQqyowBR1Hph9g65simY8d_5ypq6C7ka8_6dolS8iDR5pBS3AdtCI .venv/bin/python main.py
```

Expected output:
```
Generating email package...
Campaign: Drive trial purchases of a newly launched seasonal drink
Audience: Starbucks loyalty members aged 18-35, coffee and tea enthusiasts

=== SUBJECT LINES ===
  1. ...
  2. ...
  3. ...

=== PREHEADER ===
  ...

=== RATIONALE ===
  ...

=== OUTPUT FILES ===
  MJML:    output/email.mjml
  Package: output/email_package.json
```

- [ ] **Step 3: Verify output files exist and MJML is valid**

```bash
cd /Users/asun/Documents/email-creating-agent && head -5 output/email.mjml && echo "---" && cat output/email_package.json | .venv/bin/python -c "import json,sys; d=json.load(sys.stdin); print('Keys:', list(d.keys())); print('Subject lines:', d['subject_lines'])"
```

Expected: MJML starts with `<mjml>`, package has all 4 keys, 3 subject lines printed.

- [ ] **Step 4: Run full test suite to confirm nothing is broken**

```bash
cd /Users/asun/Documents/email-creating-agent && .venv/bin/pytest tests/ -v
```

Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/asun/Documents/email-creating-agent && git add main.py output/.gitkeep && git commit -m "feat: add main script with hardcoded Starbucks promo inputs"
```
