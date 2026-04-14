import json
import re
import time
import xml.etree.ElementTree as ET
import httpx
from brand import BrandConfig
from prompts import SYSTEM_PROMPT, build_user_prompt

MINIMAX_API_URL = "https://api.minimaxi.chat/v1/text/chatcompletion_v2"
MINIMAX_IMAGE_API_URL = "https://api.minimax.io/v1/image_generation"

_VALID_MJML_TAGS = frozenset({
    "mjml", "mj-head", "mj-body", "mj-attributes", "mj-all",
    "mj-font", "mj-section", "mj-group", "mj-column", "mj-text",
    "mj-button", "mj-image", "mj-divider", "mj-spacer",
    "mj-social", "mj-social-element", "mj-navbar", "mj-navbar-link",
    "mj-hero", "mj-raw",
})

_MOOD_TYPES = frozenset({
    "seasonal", "re-engagement", "win-back", "loyalty reward",
    "welcome", "milestone", "event invitation",
})
_PRODUCT_TYPES = frozenset({
    "promotional", "sale", "product launch", "new arrival", "abandoned cart",
})

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "review_email",
            "description": (
                "Use an LLM to review email content quality, brand guideline compliance, and subject line "
                "effectiveness. Call this after validate_email passes and before generate_image or save_email. "
                "If issues are returned, fix them and call review_email again until it passes."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "subject_lines": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "The 3 subject line options to review",
                    },
                    "preheader": {"type": "string", "description": "The preheader text to review"},
                    "mjml": {"type": "string", "description": "The complete MJML email body to review"},
                    "email_type": {"type": "string", "description": "Email type for context"},
                },
                "required": ["subject_lines", "preheader", "mjml", "email_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_image",
            "description": (
                "Generate an atmospheric mood image for mood-type emails: "
                "seasonal, re-engagement, win-back, loyalty reward, welcome, milestone, event invitation. "
                "Returns {url: string} on success or {error: string} on failure."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Atmospheric image description (max 200 chars, no brand logos or real products)",
                    }
                },
                "required": ["prompt"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "validate_email",
            "description": (
                "Check MJML markup for structural errors. Call this after drafting the email and "
                "before calling save_email. Fix any reported issues, then validate again if needed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "mjml": {"type": "string", "description": "Complete MJML markup to validate"},
                    "email_type": {"type": "string", "description": "Email type (e.g. promotional, seasonal, transactional)"},
                },
                "required": ["mjml", "email_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_email",
            "description": (
                "Finalize and save the email. Call this only after validate_email returns no issues. "
                "Pass image_url if an image was generated or the user provided a product image URL."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "subject_lines": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Exactly 3 subject line options, each under 50 characters",
                    },
                    "preheader": {"type": "string", "description": "Preheader text, under 100 characters"},
                    "mjml": {"type": "string", "description": "Complete, valid MJML markup"},
                    "rationale": {"type": "string", "description": "2-3 sentences on key design decisions"},
                    "image_url": {
                        "type": "string",
                        "description": "URL to inject into {{IMAGE_URL}} placeholder (from generate_image result or user-provided product URL)",
                    },
                },
                "required": ["subject_lines", "preheader", "mjml", "rationale"],
            },
        },
    },
]


class EmailAgent:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def _call_llm(self, model: str, messages: list[dict]) -> dict:
        last_error: Exception | None = None
        for attempt in range(3):
            if attempt > 0:
                time.sleep(3 * attempt)
            try:
                response = httpx.post(
                    MINIMAX_API_URL,
                    json={"model": model, "messages": messages, "tools": TOOLS, "tool_choice": "auto"},
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    timeout=180.0,
                )
                if response.status_code != 200:
                    raise RuntimeError(f"MiniMax API error {response.status_code}: {response.text}")
                body = response.json()
                choices = body.get("choices")
                if not choices:
                    status = body.get("base_resp", {})
                    raise RuntimeError(
                        f"MiniMax API returned no choices "
                        f"(code={status.get('status_code')} msg={status.get('status_msg')!r})"
                    )
                return choices[0]["message"]
            except RuntimeError as e:
                last_error = e
                print(f"  [retry {attempt + 1}/3] {e}")
        raise last_error

    def _generate_image(self, prompt: str) -> str | None:
        try:
            response = httpx.post(
                MINIMAX_IMAGE_API_URL,
                json={"model": "image-01", "prompt": prompt, "response_format": "url", "n": 1},
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                timeout=60.0,
            )
            if response.status_code != 200:
                return None
            urls = response.json().get("data", {}).get("image_urls", [])
            return urls[0] if urls else None
        except Exception:
            return None

    def _review_email_content(
        self, subject_lines: list[str], preheader: str, mjml: str, email_type: str
    ) -> list[str]:
        brand = self._brand
        brand_lines = [f"Brand: {brand.name}"]
        if brand.primary_color:
            brand_lines.append(f"Primary color: {brand.primary_color}")
        if brand.secondary_color:
            brand_lines.append(f"Secondary color: {brand.secondary_color}")
        if brand.brand_voice:
            brand_lines.append(f"Brand voice: {brand.brand_voice}")
        if brand.tagline:
            brand_lines.append(f"Tagline: {brand.tagline}")
        brand_section = "\n".join(brand_lines)

        numbered_subjects = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(subject_lines))

        review_prompt = f"""You are a senior email marketing reviewer. Evaluate this email draft strictly.

{brand_section}
Email type: {email_type}

Subject lines:
{numbered_subjects}

Preheader: {preheader}

MJML:
{mjml}

Check each of the following criteria:
1. Subject lines are compelling and specific (not generic), each under 50 characters, and meaningfully distinct from each other
2. Preheader complements the subject line and is under 100 characters
3. Body copy is concise (2-3 sentences max), matches the brand voice, and avoids filler phrases
4. CTA copy is clear and action-oriented
5. No invented promo codes, discounts, or offers that were not in the brief

Respond with ONLY valid JSON — no markdown, no explanation:
{{"valid": true, "issues": []}}
or
{{"valid": false, "issues": ["specific issue 1", "specific issue 2"]}}"""

        try:
            response = httpx.post(
                MINIMAX_API_URL,
                json={"model": self._model, "messages": [{"role": "user", "content": review_prompt}]},
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                timeout=60.0,
            )
            if response.status_code != 200:
                return []
            content = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if not json_match:
                return []
            data = json.loads(json_match.group())
            return data.get("issues", [])
        except Exception:
            return []

    def _validate_mjml(self, mjml: str, email_type: str) -> list[str]:
        issues = []
        normalized = email_type.strip().lower()

        if not mjml.strip().startswith("<mjml>"):
            issues.append("MJML must start with <mjml>")
        if not mjml.strip().endswith("</mjml>"):
            issues.append("MJML must end with </mjml>")

        # XML well-formedness — catches unclosed tags, unescaped & < >, mismatched tags
        try:
            root = ET.fromstring(mjml)
            # Tag whitelist — catches invented or wrong-version tags
            unknown_tags = {el.tag for el in root.iter()} - _VALID_MJML_TAGS
            if unknown_tags:
                issues.append(f"Unknown or unsupported MJML tags: {sorted(unknown_tags)}")
        except ET.ParseError as e:
            issues.append(f"Invalid XML — {e} (check for unclosed tags or unescaped characters)")

        needs_image = normalized in _MOOD_TYPES or normalized in _PRODUCT_TYPES
        if needs_image and "{{IMAGE_URL}}" not in mjml:
            issues.append(
                f'Email type "{email_type}" requires exactly one '
                '<mj-image src="{{IMAGE_URL}}" .../> placeholder'
            )

        suspicious = re.findall(
            r'src="(https?://(?:picsum|via\.placeholder|placehold|dummyimage|lorempixel)[^"]*)"',
            mjml,
        )
        if suspicious:
            issues.append(f"Remove external placeholder image URLs from src attributes: {suspicious[:2]}")

        bad_nest = re.findall(r"<mj-section[^>]*>\s*<(?:mj-text|mj-button|mj-image)\b", mjml)
        if bad_nest:
            issues.append(
                "mj-text, mj-button, and mj-image must be inside mj-column, not directly under mj-section"
            )

        oversized = [f for f in re.findall(r'font-size="(\d+)px"', mjml) if int(f) > 32]
        if oversized:
            issues.append(f"Font sizes exceeding 32px: {', '.join(f + 'px' for f in oversized)} — max is 32px")

        return issues

    def _finalize(self, inputs: dict, generated_image_url: str | None, product_image_url: str | None) -> dict:
        mjml = inputs["mjml"]
        image_url = inputs.get("image_url") or generated_image_url or product_image_url

        if image_url and "{{IMAGE_URL}}" in mjml:
            mjml = mjml.replace("{{IMAGE_URL}}", image_url)
        elif "{{IMAGE_URL}}" in mjml:
            mjml = re.sub(r"<mj-image[^>]*\{\{IMAGE_URL\}\}[^>]*/?>", "", mjml)

        return {
            "subject_lines": inputs["subject_lines"],
            "preheader": inputs["preheader"],
            "mjml": mjml,
            "rationale": inputs["rationale"],
            "image_url": image_url,
        }

    def run(
        self,
        brand: BrandConfig,
        email_type: str,
        email_classification: str,
        target_customers: str,
        goal: str,
        model: str,
        product_image_url: str | None = None,
    ) -> dict:
        self._brand = brand
        self._model = model

        messages: list[dict] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": build_user_prompt(
                    brand=brand,
                    email_type=email_type,
                    email_classification=email_classification,
                    target_customers=target_customers,
                    goal=goal,
                    product_image_url=product_image_url,
                ),
            },
        ]
        generated_image_url: str | None = None

        for iteration in range(20):
            message = self._call_llm(model, messages)

            # Strip <think> reasoning blocks if present (MiniMax reasoning models)
            content = message.get("content") or ""
            if isinstance(content, str):
                content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()

            tool_calls = message.get("tool_calls") or []

            # Append assistant turn to history (keep original content for context)
            assistant_msg: dict = {"role": "assistant", "content": content}
            if tool_calls:
                assistant_msg["tool_calls"] = tool_calls
            messages.append(assistant_msg)

            if not tool_calls:
                raise RuntimeError(
                    f"Agent stopped without saving the email (iteration {iteration + 1}). "
                    f"Last response: {content[:300]!r}"
                )

            tool_results: list[dict] = []
            final_package: dict | None = None

            for call in tool_calls:
                call_id = call["id"]
                fn_name = call["function"]["name"]
                try:
                    fn_args = json.loads(call["function"]["arguments"])
                except json.JSONDecodeError as e:
                    result: dict = {"error": f"Failed to parse tool arguments: {e}"}
                    tool_results.append({"role": "tool", "tool_call_id": call_id, "content": json.dumps(result)})
                    continue

                if fn_name == "review_email":
                    issues = self._review_email_content(
                        fn_args["subject_lines"],
                        fn_args["preheader"],
                        fn_args["mjml"],
                        fn_args["email_type"],
                    )
                    result = {"valid": not issues, "issues": issues}

                elif fn_name == "generate_image":
                    url = self._generate_image(fn_args["prompt"])
                    if url:
                        generated_image_url = url
                        result = {"url": url}
                    else:
                        result = {"error": "Image generation failed — you may proceed without an image"}

                elif fn_name == "validate_email":
                    issues = self._validate_mjml(fn_args["mjml"], fn_args["email_type"])
                    result = {"valid": not issues, "issues": issues}

                elif fn_name == "save_email":
                    final_package = self._finalize(fn_args, generated_image_url, product_image_url)
                    result = {"status": "saved"}

                else:
                    result = {"error": f"Unknown tool: {fn_name}"}

                tool_results.append({"role": "tool", "tool_call_id": call_id, "content": json.dumps(result)})

            messages.extend(tool_results)

            if final_package is not None:
                return final_package

        raise RuntimeError("Agent exceeded 20 iterations without completing the email.")
