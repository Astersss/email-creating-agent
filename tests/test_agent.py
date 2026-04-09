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
