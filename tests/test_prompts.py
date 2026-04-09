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
