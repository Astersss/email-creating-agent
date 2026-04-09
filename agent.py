import json
import re
import httpx
from enum import Enum
from brand import BrandConfig
from prompts import SYSTEM_PROMPT, build_user_prompt


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


def patch_image_url(mjml: str, url: str) -> str:
    return mjml.replace("{{IMAGE_URL}}", url)


def strip_image_marker(mjml: str) -> str:
    return re.sub(r'<mj-image[^>]*\{\{IMAGE_URL\}\}[^>]*/>', '', mjml)


MINIMAX_API_URL = "https://api.minimaxi.chat/v1/text/chatcompletion_v2"
MINIMAX_IMAGE_API_URL = "https://api.minimax.io/v1/image_generation"
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
