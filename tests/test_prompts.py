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


def test_build_user_prompt_field_labels_are_correct():
    prompt = build_user_prompt(
        email_type="TYPE_SENTINEL",
        email_classification="CLASS_SENTINEL",
        target_customers="CUSTOMERS_SENTINEL",
        goal="GOAL_SENTINEL",
    )
    assert "Email type: TYPE_SENTINEL" in prompt
    assert "Classification: CLASS_SENTINEL" in prompt
    assert "Target customers: CUSTOMERS_SENTINEL" in prompt
    assert "Goal: GOAL_SENTINEL" in prompt
