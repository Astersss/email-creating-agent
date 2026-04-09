# Email Image Strategy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace unreliable model-generated image URLs with a deterministic image strategy: real product photos from brand config, AI-generated mood imagery via MiniMax `image-01`, or text-only fallback.

**Architecture:** The text model emits an optional `{{IMAGE_URL}}` marker in MJML plus an optional `image_prompt` field. Python code resolves `ImageStrategy` from `email_type`, fetches the appropriate image URL (brand asset or `image-01` API), and patches or strips the marker. Brand config is enriched with 6 new optional fields to improve copy quality and visual fidelity.

**Tech Stack:** Python 3.12, httpx, MiniMax text API (`MiniMax-Text-01`), MiniMax image API (`image-01`), pytest

---

## File Map

| File | Change |
|---|---|
| `brand.py` | Add 6 new optional fields to `BrandConfig` |
| `brands.json` | Populate new fields for Starbucks |
| `prompts.py` | Update system prompt (marker + `image_prompt` rules) and user prompt (new brand fields) |
| `agent.py` | Add `ImageStrategy` enum, `resolve_image_strategy()`, `generate_mood_image()`, `_patch_or_strip_image()`, wire into `generate()` |
| `tests/test_brand.py` | Tests for new `BrandConfig` fields |
| `tests/test_prompts.py` | Tests for new brand fields in user prompt |
| `tests/test_agent.py` | Tests for strategy resolution, image generation, patching/stripping, generate() integration |

---

## Task 1: Extend BrandConfig with 6 new optional fields

**Files:**
- Modify: `brand.py`
- Test: `tests/test_brand.py`

- [ ] **Step 1: Write failing tests for new BrandConfig fields**

Add to `tests/test_brand.py`:

```python
def test_brand_config_new_fields_default_to_none():
    brand = BrandConfig(id="test", name="Test Brand")
    assert brand.secondary_color is None
    assert brand.product_image_url is None
    assert brand.font_family is None
    assert brand_voice is None  # will fail — field doesn't exist yet
    assert brand.website_url is None
    assert brand.tagline is None

def test_brand_config_new_fields_accepted():
    brand = BrandConfig(
        id="sb", name="Starbucks",
        secondary_color="#CBA258",
        product_image_url="https://example.com/drink.jpg",
        font_family="Sodo Sans, Arial, sans-serif",
        brand_voice="warm, welcoming",
        website_url="https://www.starbucks.com",
        tagline="It starts with you",
    )
    assert brand.secondary_color == "#CBA258"
    assert brand.product_image_url == "https://example.com/drink.jpg"
    assert brand.font_family == "Sodo Sans, Arial, sans-serif"
    assert brand.brand_voice == "warm, welcoming"
    assert brand.website_url == "https://www.starbucks.com"
    assert brand.tagline == "It starts with you"

def test_load_brands_ignores_unknown_fields(tmp_path):
    brands_file = tmp_path / "brands.json"
    brands_file.write_text(
        json.dumps({"brands": [{"id": "x", "name": "X", "unknown_field": "ignored"}]}),
        encoding="utf-8",
    )
    brands = load_brands(path=brands_file)
    assert brands[0].id == "x"

def test_load_brands_loads_new_fields(tmp_path):
    brands_file = tmp_path / "brands.json"
    brands_file.write_text(
        json.dumps({"brands": [{
            "id": "sb", "name": "Starbucks",
            "primary_color": "#00704A",
            "logo_url": None,
            "secondary_color": "#CBA258",
            "product_image_url": "https://example.com/drink.jpg",
            "font_family": "Sodo Sans, Arial, sans-serif",
            "brand_voice": "warm, welcoming",
            "website_url": "https://www.starbucks.com",
            "tagline": "It starts with you",
        }]}),
        encoding="utf-8",
    )
    brands = load_brands(path=brands_file)
    assert brands[0].secondary_color == "#CBA258"
    assert brands[0].product_image_url == "https://example.com/drink.jpg"
    assert brands[0].brand_voice == "warm, welcoming"
    assert brands[0].website_url == "https://www.starbucks.com"
    assert brands[0].tagline == "It starts with you"
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
.venv/bin/python -m pytest tests/test_brand.py::test_brand_config_new_fields_default_to_none tests/test_brand.py::test_brand_config_new_fields_accepted tests/test_brand.py::test_load_brands_loads_new_fields -v
```

Expected: FAIL with `AttributeError` or similar — fields don't exist yet.

- [ ] **Step 3: Add the 6 new fields to BrandConfig in `brand.py`**

Replace the `BrandConfig` dataclass:

```python
@dataclass
class BrandConfig:
    id: str
    name: str
    primary_color: str | None = None
    logo_url: str | None = None
    secondary_color: str | None = None
    product_image_url: str | None = None
    font_family: str | None = None
    brand_voice: str | None = None
    website_url: str | None = None
    tagline: str | None = None
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
.venv/bin/python -m pytest tests/test_brand.py -v
```

Expected: all PASS including the 4 new tests.

- [ ] **Step 5: Commit**

```bash
git add brand.py tests/test_brand.py
git commit -m "feat: extend BrandConfig with secondary_color, product_image_url, font_family, brand_voice, website_url, tagline"
```

---

## Task 2: Update brands.json with enriched Starbucks data

**Files:**
- Modify: `brands.json`

- [ ] **Step 1: Update brands.json**

Replace the contents of `brands.json`:

```json
{
  "brands": [
    {
      "id": "starbucks",
      "name": "Starbucks",
      "primary_color": "#00704A",
      "secondary_color": "#CBA258",
      "logo_url": null,
      "product_image_url": null,
      "font_family": "Sodo Sans, Arial, sans-serif",
      "brand_voice": "warm, welcoming, community-driven",
      "website_url": "https://www.starbucks.com",
      "tagline": "It starts with you"
    }
  ]
}
```

- [ ] **Step 2: Verify brands.json loads cleanly**

```bash
.venv/bin/python -c "from brand import load_brands; b = load_brands(); print(b[0])"
```

Expected: `BrandConfig(id='starbucks', name='Starbucks', primary_color='#00704A', secondary_color='#CBA258', ...)`

- [ ] **Step 3: Run full test suite to confirm nothing is broken**

```bash
.venv/bin/python -m pytest tests/ -q
```

Expected: all pass.

- [ ] **Step 4: Commit**

```bash
git add brands.json
git commit -m "feat: enrich Starbucks brand config with voice, palette, font, tagline, website"
```

---

## Task 3: Update prompts to use new brand fields and image marker

**Files:**
- Modify: `prompts.py`
- Test: `tests/test_prompts.py`

- [ ] **Step 1: Write failing tests for updated prompts**

Add to `tests/test_prompts.py`:

```python
def test_build_user_prompt_includes_secondary_color():
    brand = BrandConfig(id="sb", name="Starbucks", primary_color="#00704A", secondary_color="#CBA258")
    prompt = build_user_prompt(brand=brand, email_type="promo", email_classification="B2C",
                               target_customers="all", goal="sell")
    assert "#CBA258" in prompt

def test_build_user_prompt_includes_brand_voice():
    brand = BrandConfig(id="sb", name="Starbucks", brand_voice="warm, welcoming")
    prompt = build_user_prompt(brand=brand, email_type="promo", email_classification="B2C",
                               target_customers="all", goal="sell")
    assert "warm, welcoming" in prompt

def test_build_user_prompt_includes_website_url():
    brand = BrandConfig(id="sb", name="Starbucks", website_url="https://www.starbucks.com")
    prompt = build_user_prompt(brand=brand, email_type="promo", email_classification="B2C",
                               target_customers="all", goal="sell")
    assert "https://www.starbucks.com" in prompt

def test_build_user_prompt_includes_tagline():
    brand = BrandConfig(id="sb", name="Starbucks", tagline="It starts with you")
    prompt = build_user_prompt(brand=brand, email_type="promo", email_classification="B2C",
                               target_customers="all", goal="sell")
    assert "It starts with you" in prompt

def test_build_user_prompt_includes_font_family():
    brand = BrandConfig(id="sb", name="Starbucks", font_family="Sodo Sans, Arial, sans-serif")
    prompt = build_user_prompt(brand=brand, email_type="promo", email_classification="B2C",
                               target_customers="all", goal="sell")
    assert "Sodo Sans, Arial, sans-serif" in prompt

def test_system_prompt_requires_image_url_marker():
    assert "{{IMAGE_URL}}" in SYSTEM_PROMPT

def test_system_prompt_requires_image_prompt_field():
    assert "image_prompt" in SYSTEM_PROMPT

def test_system_prompt_forbids_external_image_urls():
    assert "{{IMAGE_URL}}" in SYSTEM_PROMPT
    # system prompt should instruct to never use real URLs in src
    assert "never" in SYSTEM_PROMPT.lower() or "do not" in SYSTEM_PROMPT.lower()
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
.venv/bin/python -m pytest tests/test_prompts.py::test_build_user_prompt_includes_secondary_color tests/test_prompts.py::test_build_user_prompt_includes_brand_voice tests/test_prompts.py::test_system_prompt_requires_image_url_marker -v
```

Expected: FAIL — new fields not yet in prompts.

- [ ] **Step 3: Rewrite `prompts.py`**

Replace the entire file:

```python
from brand import BrandConfig

SYSTEM_PROMPT = """You are an expert email marketer and MJML developer. Your job is to create high-performing marketing emails.

MJML RULES:
- Use only valid MJML 4 tags: mjml, mj-head, mj-attributes, mj-all, mj-body, mj-section, mj-column, mj-text, mj-button, mj-image, mj-divider, mj-spacer
- Every email must start with <mjml> and end with </mjml>
- Sections contain columns, columns contain content elements
- Use mj-attributes in mj-head to set global styles (font-family, padding, color)
- Buttons must use the brand website URL as href, or "#" if none provided
- Do NOT use any real image URLs in src attributes — never use external URLs, placeholder services, or Wikipedia images

IMAGE RULES:
- For mood/seasonal/celebratory/re-engagement/loyalty emails: include exactly one <mj-image src="{{IMAGE_URL}}" alt="..." width="600px" align="center" /> in the MJML where an image would appear, AND include an "image_prompt" field in your JSON output describing the image to generate (max 200 chars, atmospheric/mood-focused, no brand logos or real products)
- For product/promotional/sale/launch emails: include exactly one <mj-image src="{{IMAGE_URL}}" alt="..." width="600px" align="center" /> where the product image should appear, but do NOT include "image_prompt" (a real product photo will be substituted)
- For transactional emails: include no mj-image at all, no {{IMAGE_URL}}, no image_prompt
- If logo_url is provided: always include it as the first mj-image in the email using the exact logo_url as src (logos are exempt from the URL rule)

EMAIL BEST PRACTICES:
- Single, clear call-to-action (CTA)
- Benefit-led headline above the fold
- Short, punchy body copy (under 80 words)
- Create urgency or excitement without being spammy
- Mobile-first: single-column layout
- Use brand voice and tagline to inform copy tone

OUTPUT FORMAT:
Return ONLY a valid JSON object with exactly these keys:
- "subject_lines": array of exactly 3 subject line strings (under 50 chars each)
- "preheader": string (under 100 chars, teases the email content)
- "mjml": string (complete, valid MJML markup — never use real image URLs except logo_url)
- "rationale": string (2-3 sentences explaining key design decisions)
- "image_prompt": string (only for mood/seasonal/celebratory emails — omit this key entirely for all other types)

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
    if brand.secondary_color:
        brand_lines.append(f"Secondary color: {brand.secondary_color}")
    if brand.logo_url:
        brand_lines.append(f"Logo URL: {brand.logo_url}")
    if brand.font_family:
        brand_lines.append(f"Font family: {brand.font_family}")
    if brand.brand_voice:
        brand_lines.append(f"Brand voice: {brand.brand_voice}")
    if brand.website_url:
        brand_lines.append(f"Website URL: {brand.website_url}")
    if brand.tagline:
        brand_lines.append(f"Tagline: {brand.tagline}")
    brand_section = "\n".join(brand_lines)

    if brand.primary_color:
        styling = f"- Use {brand.primary_color} as the accent color for buttons, headers, and dividers"
        if brand.secondary_color:
            styling += f"\n- Use {brand.secondary_color} for background sections or subtle accents"
    else:
        styling = "- Use a clean neutral palette (#333333 for text, #0066CC for buttons)"

    if brand.logo_url:
        styling += f"\n- Add the logo as the first mj-image using src=\"{brand.logo_url}\""

    font = brand.font_family or "Avenir, Helvetica, Arial, sans-serif"
    styling += f"\n- Use font-family: {font}"

    return f"""Create a marketing email with the following details:

{brand_section}

Email type: {email_type}
Classification: {email_classification}
Target customers: {target_customers}
Goal: {goal}

Brand styling instructions:
{styling}

Return a single JSON object with keys: subject_lines (array of 3 strings), preheader (string), mjml (string), rationale (string), and optionally image_prompt (string, mood emails only)."""
```

- [ ] **Step 4: Run tests to confirm new tests pass and existing tests still pass**

```bash
.venv/bin/python -m pytest tests/test_prompts.py -v
```

Expected: all PASS. If `test_build_user_prompt_no_logo_section_when_logo_absent` fails, check that "Logo URL" label is no longer emitted when `logo_url` is None (it shouldn't be, since the new code uses `brand.logo_url` directly in the styling string).

- [ ] **Step 5: Commit**

```bash
git add prompts.py tests/test_prompts.py
git commit -m "feat: update prompts with image marker rules, image_prompt field, and new brand fields"
```

---

## Task 4: Add ImageStrategy enum and resolution logic to `agent.py`

**Files:**
- Modify: `agent.py`
- Test: `tests/test_agent.py`

- [ ] **Step 1: Write failing tests for ImageStrategy**

Add to `tests/test_agent.py`:

```python
from agent import EmailAgent, ImageStrategy, resolve_image_strategy

def test_resolve_image_strategy_product_types():
    for email_type in ["promotional", "sale", "product launch", "new arrival", "abandoned cart",
                       "Promotional", "SALE"]:
        assert resolve_image_strategy(email_type) == ImageStrategy.PRODUCT_PHOTO, email_type

def test_resolve_image_strategy_mood_types():
    for email_type in ["seasonal", "loyalty reward", "milestone", "re-engagement",
                       "win-back", "welcome", "event invitation", "Seasonal"]:
        assert resolve_image_strategy(email_type) == ImageStrategy.MOOD_GENERATED, email_type

def test_resolve_image_strategy_none_types():
    for email_type in ["transactional", "newsletter", "unknown", "", "TRANSACTIONAL"]:
        assert resolve_image_strategy(email_type) == ImageStrategy.NONE, email_type
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
.venv/bin/python -m pytest tests/test_agent.py::test_resolve_image_strategy_product_types tests/test_agent.py::test_resolve_image_strategy_mood_types tests/test_agent.py::test_resolve_image_strategy_none_types -v
```

Expected: FAIL with `ImportError` — `ImageStrategy` and `resolve_image_strategy` don't exist yet.

- [ ] **Step 3: Add ImageStrategy enum and resolve_image_strategy() to `agent.py`**

Add at the top of `agent.py` (after the imports):

```python
import re
from enum import Enum

class ImageStrategy(Enum):
    PRODUCT_PHOTO = "product_photo"
    MOOD_GENERATED = "mood_generated"
    NONE = "none"


_PRODUCT_PHOTO_TYPES = {
    "promotional", "sale", "product launch", "new arrival", "abandoned cart",
}
_MOOD_GENERATED_TYPES = {
    "seasonal", "loyalty reward", "milestone", "re-engagement",
    "win-back", "welcome", "event invitation",
}


def resolve_image_strategy(email_type: str) -> ImageStrategy:
    normalized = email_type.strip().lower()
    if normalized in _PRODUCT_PHOTO_TYPES:
        return ImageStrategy.PRODUCT_PHOTO
    if normalized in _MOOD_GENERATED_TYPES:
        return ImageStrategy.MOOD_GENERATED
    return ImageStrategy.NONE
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
.venv/bin/python -m pytest tests/test_agent.py::test_resolve_image_strategy_product_types tests/test_agent.py::test_resolve_image_strategy_mood_types tests/test_agent.py::test_resolve_image_strategy_none_types -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add agent.py tests/test_agent.py
git commit -m "feat: add ImageStrategy enum and resolve_image_strategy()"
```

---

## Task 5: Add MJML image patching/stripping logic to `agent.py`

**Files:**
- Modify: `agent.py`
- Test: `tests/test_agent.py`

- [ ] **Step 1: Write failing tests for patch/strip**

Add to `tests/test_agent.py`:

```python
from agent import EmailAgent, ImageStrategy, resolve_image_strategy, patch_image_url, strip_image_marker

MJML_WITH_MARKER = '<mjml><mj-body><mj-section><mj-column><mj-image src="{{IMAGE_URL}}" alt="drink" width="600px" align="center" /><mj-text>Hello</mj-text></mj-column></mj-section></mj-body></mjml>'
MJML_NO_MARKER = '<mjml><mj-body><mj-section><mj-column><mj-text>Hello</mj-text></mj-column></mj-section></mj-body></mjml>'

def test_patch_image_url_replaces_marker():
    result = patch_image_url(MJML_WITH_MARKER, "https://example.com/img.jpg")
    assert 'src="https://example.com/img.jpg"' in result
    assert "{{IMAGE_URL}}" not in result

def test_patch_image_url_no_marker_returns_unchanged():
    result = patch_image_url(MJML_NO_MARKER, "https://example.com/img.jpg")
    assert result == MJML_NO_MARKER

def test_strip_image_marker_removes_mj_image_tag():
    result = strip_image_marker(MJML_WITH_MARKER)
    assert "{{IMAGE_URL}}" not in result
    assert "<mj-image" not in result
    assert "<mj-text>Hello</mj-text>" in result

def test_strip_image_marker_no_marker_returns_unchanged():
    result = strip_image_marker(MJML_NO_MARKER)
    assert result == MJML_NO_MARKER
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
.venv/bin/python -m pytest tests/test_agent.py::test_patch_image_url_replaces_marker tests/test_agent.py::test_strip_image_marker_removes_mj_image_tag -v
```

Expected: FAIL with `ImportError`.

- [ ] **Step 3: Add patch_image_url() and strip_image_marker() to `agent.py`**

Add as module-level functions (below `resolve_image_strategy`):

```python
def patch_image_url(mjml: str, url: str) -> str:
    return mjml.replace("{{IMAGE_URL}}", url)


def strip_image_marker(mjml: str) -> str:
    return re.sub(r'<mj-image[^>]*\{\{IMAGE_URL\}\}[^>]*/>', '', mjml)
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
.venv/bin/python -m pytest tests/test_agent.py::test_patch_image_url_replaces_marker tests/test_agent.py::test_patch_image_url_no_marker_returns_unchanged tests/test_agent.py::test_strip_image_marker_removes_mj_image_tag tests/test_agent.py::test_strip_image_marker_no_marker_returns_unchanged -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add agent.py tests/test_agent.py
git commit -m "feat: add patch_image_url() and strip_image_marker() for MJML image resolution"
```

---

## Task 6: Add generate_mood_image() to EmailAgent

**Files:**
- Modify: `agent.py`
- Test: `tests/test_agent.py`

- [ ] **Step 1: Write failing tests for generate_mood_image()**

Add to `tests/test_agent.py`:

```python
MINIMAX_IMAGE_API_URL = "https://api.minimax.io/v1/image_generation"

@patch("agent.httpx.post")
def test_generate_mood_image_returns_url_on_success(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {"image_urls": ["https://cdn.minimax.io/generated/abc.jpg"]},
        "base_resp": {"status_code": 0, "status_msg": "success"},
    }
    mock_post.return_value = mock_response

    agent = EmailAgent(api_key="test-key")
    url = agent.generate_mood_image("A cozy autumn coffee scene")
    assert url == "https://cdn.minimax.io/generated/abc.jpg"
    call_kwargs = mock_post.call_args.kwargs
    assert call_kwargs["json"]["model"] == "image-01"
    assert call_kwargs["json"]["prompt"] == "A cozy autumn coffee scene"

@patch("agent.httpx.post")
def test_generate_mood_image_returns_none_on_api_error(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "internal error"
    mock_post.return_value = mock_response

    agent = EmailAgent(api_key="test-key")
    url = agent.generate_mood_image("A cozy autumn coffee scene")
    assert url is None

@patch("agent.httpx.post")
def test_generate_mood_image_returns_none_on_content_safety_block(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {"image_urls": []},
        "metadata": {"success_count": 0, "failed_count": 1},
        "base_resp": {"status_code": 0, "status_msg": "success"},
    }
    mock_post.return_value = mock_response

    agent = EmailAgent(api_key="test-key")
    url = agent.generate_mood_image("A cozy autumn coffee scene")
    assert url is None

@patch("agent.httpx.post")
def test_generate_mood_image_returns_none_on_exception(mock_post):
    mock_post.side_effect = Exception("network error")

    agent = EmailAgent(api_key="test-key")
    url = agent.generate_mood_image("prompt")
    assert url is None
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
.venv/bin/python -m pytest tests/test_agent.py::test_generate_mood_image_returns_url_on_success tests/test_agent.py::test_generate_mood_image_returns_none_on_api_error -v
```

Expected: FAIL with `AttributeError` — method doesn't exist.

- [ ] **Step 3: Add generate_mood_image() to EmailAgent in `agent.py`**

Add as a method on `EmailAgent` (after `_parse_response`):

```python
MINIMAX_IMAGE_API_URL = "https://api.minimax.io/v1/image_generation"

# (inside EmailAgent class)
def generate_mood_image(self, image_prompt: str) -> str | None:
    try:
        response = httpx.post(
            MINIMAX_IMAGE_API_URL,
            json={"model": "image-01", "prompt": image_prompt, "response_format": "url", "n": 1},
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            timeout=60.0,
        )
        if response.status_code != 200:
            return None
        urls = response.json().get("data", {}).get("image_urls", [])
        return urls[0] if urls else None
    except Exception:
        return None
```

Note: `MINIMAX_IMAGE_API_URL` is a module-level constant added above `MINIMAX_API_URL`.

- [ ] **Step 4: Run tests to confirm they pass**

```bash
.venv/bin/python -m pytest tests/test_agent.py::test_generate_mood_image_returns_url_on_success tests/test_agent.py::test_generate_mood_image_returns_none_on_api_error tests/test_agent.py::test_generate_mood_image_returns_none_on_content_safety_block tests/test_agent.py::test_generate_mood_image_returns_none_on_exception -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add agent.py tests/test_agent.py
git commit -m "feat: add generate_mood_image() with text-only fallback on any failure"
```

---

## Task 7: Wire image strategy into generate() and update _parse_response()

**Files:**
- Modify: `agent.py`
- Test: `tests/test_agent.py`

- [ ] **Step 1: Write failing integration tests**

Add to `tests/test_agent.py`:

```python
VALID_PACKAGE_WITH_IMAGE_PROMPT = {
    "subject_lines": ["Try our new drink", "New arrival", "Sip something new"],
    "preheader": "A bold new flavor is here.",
    "mjml": '<mjml><mj-body><mj-section><mj-column><mj-image src="{{IMAGE_URL}}" alt="seasonal" width="600px" align="center" /><mj-text>Hello</mj-text></mj-column></mj-section></mj-body></mjml>',
    "rationale": "Single CTA drives click-through.",
    "image_prompt": "A cozy autumn coffee scene with warm lighting",
}

VALID_PACKAGE_PRODUCT = {
    "subject_lines": ["Try our new drink", "New arrival", "Sip something new"],
    "preheader": "A bold new flavor is here.",
    "mjml": '<mjml><mj-body><mj-section><mj-column><mj-image src="{{IMAGE_URL}}" alt="product" width="600px" align="center" /><mj-text>Hello</mj-text></mj-column></mj-section></mj-body></mjml>',
    "rationale": "Single CTA drives click-through.",
}

STARBUCKS_WITH_PRODUCT_IMAGE = BrandConfig(
    id="starbucks", name="Starbucks", primary_color="#00704A",
    product_image_url="https://brand.starbucks.com/drink.jpg"
)

@patch("agent.httpx.post")
def test_generate_seasonal_calls_image_api_and_patches_mjml(mock_post):
    text_response = MagicMock()
    text_response.status_code = 200
    text_response.json.return_value = {"choices": [{"message": {"content": json.dumps(VALID_PACKAGE_WITH_IMAGE_PROMPT)}}]}

    image_response = MagicMock()
    image_response.status_code = 200
    image_response.json.return_value = {"data": {"image_urls": ["https://cdn.minimax.io/abc.jpg"]}, "base_resp": {"status_code": 0}}

    mock_post.side_effect = [text_response, image_response]

    agent = EmailAgent(api_key="test-key")
    result = agent.generate(
        brand=STARBUCKS, email_type="seasonal", email_classification="B2C",
        target_customers="all", goal="seasonal engagement", model="MiniMax-Text-01",
    )
    assert 'src="https://cdn.minimax.io/abc.jpg"' in result["mjml"]
    assert "{{IMAGE_URL}}" not in result["mjml"]
    assert mock_post.call_count == 2

@patch("agent.httpx.post")
def test_generate_seasonal_strips_image_on_image_api_failure(mock_post):
    text_response = MagicMock()
    text_response.status_code = 200
    text_response.json.return_value = {"choices": [{"message": {"content": json.dumps(VALID_PACKAGE_WITH_IMAGE_PROMPT)}}]}

    image_response = MagicMock()
    image_response.status_code = 500
    image_response.text = "error"

    mock_post.side_effect = [text_response, image_response]

    agent = EmailAgent(api_key="test-key")
    result = agent.generate(
        brand=STARBUCKS, email_type="seasonal", email_classification="B2C",
        target_customers="all", goal="seasonal engagement", model="MiniMax-Text-01",
    )
    assert "{{IMAGE_URL}}" not in result["mjml"]
    assert "<mj-image" not in result["mjml"]

@patch("agent.httpx.post")
def test_generate_promotional_uses_product_image_url(mock_post):
    text_response = MagicMock()
    text_response.status_code = 200
    text_response.json.return_value = {"choices": [{"message": {"content": json.dumps(VALID_PACKAGE_PRODUCT)}}]}
    mock_post.return_value = text_response

    agent = EmailAgent(api_key="test-key")
    result = agent.generate(
        brand=STARBUCKS_WITH_PRODUCT_IMAGE, email_type="promotional", email_classification="B2C",
        target_customers="all", goal="sell", model="MiniMax-Text-01",
    )
    assert 'src="https://brand.starbucks.com/drink.jpg"' in result["mjml"]
    assert "{{IMAGE_URL}}" not in result["mjml"]
    assert mock_post.call_count == 1  # no image API call

@patch("agent.httpx.post")
def test_generate_promotional_strips_image_when_no_product_image_url(mock_post):
    text_response = MagicMock()
    text_response.status_code = 200
    text_response.json.return_value = {"choices": [{"message": {"content": json.dumps(VALID_PACKAGE_PRODUCT)}}]}
    mock_post.return_value = text_response

    agent = EmailAgent(api_key="test-key")
    result = agent.generate(
        brand=STARBUCKS, email_type="promotional", email_classification="B2C",
        target_customers="all", goal="sell", model="MiniMax-Text-01",
    )
    assert "{{IMAGE_URL}}" not in result["mjml"]
    assert "<mj-image" not in result["mjml"]
    assert mock_post.call_count == 1
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
.venv/bin/python -m pytest tests/test_agent.py::test_generate_seasonal_calls_image_api_and_patches_mjml tests/test_agent.py::test_generate_promotional_uses_product_image_url -v
```

Expected: FAIL — generate() doesn't do image resolution yet.

- [ ] **Step 3: Update _parse_response() to accept optional image_prompt**

In `agent.py`, update `REQUIRED_KEYS` and `_parse_response`:

```python
REQUIRED_KEYS = {"subject_lines", "preheader", "mjml", "rationale"}
# image_prompt is optional — do not add to REQUIRED_KEYS
```

`_parse_response` already handles this correctly since it only checks `REQUIRED_KEYS`. No changes needed there.

- [ ] **Step 4: Update generate() to wire image resolution**

Replace the `generate()` method body in `agent.py`:

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

    package = self._parse_response(content)

    # Resolve image URL based on email type strategy
    strategy = resolve_image_strategy(email_type)
    image_url: str | None = None

    if strategy == ImageStrategy.PRODUCT_PHOTO:
        image_url = brand.product_image_url
    elif strategy == ImageStrategy.MOOD_GENERATED:
        image_prompt = package.get("image_prompt")
        if image_prompt:
            image_url = self.generate_mood_image(image_prompt)

    if image_url:
        package["mjml"] = patch_image_url(package["mjml"], image_url)
    else:
        package["mjml"] = strip_image_marker(package["mjml"])

    return package
```

- [ ] **Step 5: Run the full test suite**

```bash
.venv/bin/python -m pytest tests/ -v
```

Expected: all PASS. If any existing tests break, check whether the MJML in `VALID_PACKAGE` contains `{{IMAGE_URL}}` — it doesn't, so `strip_image_marker` is a no-op and tests should pass unchanged.

- [ ] **Step 6: Commit**

```bash
git add agent.py tests/test_agent.py
git commit -m "feat: wire ImageStrategy into generate() — patch product/mood images, strip on fallback"
```

---

## Final Check

- [ ] **Run full test suite**

```bash
.venv/bin/python -m pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Smoke test: load brands and verify new fields visible**

```bash
.venv/bin/python -c "
from brand import load_brands
b = load_brands()[0]
print('name:', b.name)
print('secondary_color:', b.secondary_color)
print('brand_voice:', b.brand_voice)
print('website_url:', b.website_url)
print('tagline:', b.tagline)
"
```

Expected output:
```
name: Starbucks
secondary_color: #CBA258
brand_voice: warm, welcoming, community-driven
website_url: https://www.starbucks.com
tagline: It starts with you
```
