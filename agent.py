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
