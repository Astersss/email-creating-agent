import json
import pytest
from unittest.mock import MagicMock, patch
from brand import BrandConfig
from agent import EmailAgent, ImageStrategy, resolve_image_strategy, patch_image_url, strip_image_marker

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
