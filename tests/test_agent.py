import json
import pytest
from unittest.mock import MagicMock, patch
from brand import BrandConfig
from agent import EmailAgent, ImageStrategy, resolve_image_strategy

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
def test_generate_embeds_brand_in_prompt_payload(mock_post):
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
        model="MiniMax-Text-01",
    )
    user_message_content = mock_post.call_args.kwargs["json"]["messages"][1]["content"]
    assert "Starbucks" in user_message_content
    assert "#00704A" in user_message_content


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
