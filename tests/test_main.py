import json
import pytest
from unittest.mock import patch
from main import make_brand_id, save_output

VALID_PACKAGE = {
    "subject_lines": ["Sub 1", "Sub 2", "Sub 3"],
    "preheader": "A great email",
    "mjml": "<mjml><mj-body></mj-body></mjml>",
    "rationale": "Good design choices.",
}


def test_make_brand_id_lowercases():
    assert make_brand_id("Nike") == "nike"


def test_make_brand_id_replaces_spaces():
    assert make_brand_id("My Brand") == "my_brand"


def test_make_brand_id_strips_whitespace():
    assert make_brand_id("  Nike  ") == "nike"


def test_save_output_writes_mjml(tmp_path):
    with patch("main.OUTPUT_DIR", tmp_path):
        mjml_path, _ = save_output("starbucks", VALID_PACKAGE)
    assert mjml_path.read_text(encoding="utf-8") == VALID_PACKAGE["mjml"]


def test_save_output_writes_package_json(tmp_path):
    with patch("main.OUTPUT_DIR", tmp_path):
        _, package_path = save_output("starbucks", VALID_PACKAGE)
    data = json.loads(package_path.read_text(encoding="utf-8"))
    assert data == VALID_PACKAGE


def test_save_output_uses_brand_id_in_filename(tmp_path):
    with patch("main.OUTPUT_DIR", tmp_path):
        mjml_path, package_path = save_output("nike", VALID_PACKAGE)
    assert mjml_path.name == "nike_email.mjml"
    assert package_path.name == "nike_email_package.json"
