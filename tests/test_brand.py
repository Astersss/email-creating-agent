import json
from brand import BrandConfig, load_brands, load_model, find_logo_data_uri


def test_brand_config_required_fields():
    brand = BrandConfig(id="test", name="Test Brand")
    assert brand.id == "test"
    assert brand.name == "Test Brand"
    assert brand.primary_color is None
    assert brand.logo_url is None


def test_brand_config_all_fields():
    brand = BrandConfig(
        id="sb",
        name="Starbucks",
        primary_color="#00704A",
        logo_url="https://example.com/logo.png",
    )
    assert brand.primary_color == "#00704A"
    assert brand.logo_url == "https://example.com/logo.png"


def test_load_brands(tmp_path):
    brands_file = tmp_path / "brands.json"
    brands_file.write_text(
        json.dumps({
            "brands": [
                {"id": "starbucks", "name": "Starbucks", "primary_color": "#00704A", "logo_url": None}
            ]
        }),
        encoding="utf-8",
    )
    brands = load_brands(path=brands_file)
    assert len(brands) == 1
    assert brands[0].id == "starbucks"
    assert brands[0].name == "Starbucks"
    assert brands[0].primary_color == "#00704A"
    assert brands[0].logo_url is None


def test_load_brands_multiple(tmp_path):
    brands_file = tmp_path / "brands.json"
    brands_file.write_text(
        json.dumps({
            "brands": [
                {"id": "a", "name": "Brand A", "primary_color": "#FF0000", "logo_url": None},
                {"id": "b", "name": "Brand B", "primary_color": None, "logo_url": None},
            ]
        }),
        encoding="utf-8",
    )
    brands = load_brands(path=brands_file)
    assert len(brands) == 2
    assert brands[1].id == "b"
    assert brands[1].primary_color is None


def test_load_model(tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"model": "MiniMax-Text-01"}), encoding="utf-8")
    assert load_model(path=config_file) == "MiniMax-Text-01"


def test_load_model_custom(tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"model": "MiniMax-M1"}), encoding="utf-8")
    assert load_model(path=config_file) == "MiniMax-M1"


def test_brand_config_new_fields_default_to_none():
    brand = BrandConfig(id="test", name="Test Brand")
    assert brand.secondary_color is None
    assert brand.font_family is None
    assert brand.brand_voice is None
    assert brand.website_url is None
    assert brand.tagline is None


def test_brand_config_new_fields_accepted():
    brand = BrandConfig(
        id="sb", name="Starbucks",
        secondary_color="#CBA258",
        font_family="Sodo Sans, Arial, sans-serif",
        brand_voice="warm, welcoming",
        website_url="https://www.starbucks.com",
        tagline="It starts with you",
    )
    assert brand.secondary_color == "#CBA258"
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
            "font_family": "Sodo Sans, Arial, sans-serif",
            "brand_voice": "warm, welcoming",
            "website_url": "https://www.starbucks.com",
            "tagline": "It starts with you",
        }]}),
        encoding="utf-8",
    )
    brands = load_brands(path=brands_file)
    assert brands[0].secondary_color == "#CBA258"
    assert brands[0].brand_voice == "warm, welcoming"
    assert brands[0].website_url == "https://www.starbucks.com"
    assert brands[0].tagline == "It starts with you"


def test_find_logo_data_uri_returns_none_when_no_file(tmp_path):
    assert find_logo_data_uri("starbucks", logos_dir=tmp_path) is None


def test_find_logo_data_uri_returns_data_uri_for_png(tmp_path):
    (tmp_path / "starbucks.png").write_bytes(b"\x89PNG\r\n")
    result = find_logo_data_uri("starbucks", logos_dir=tmp_path)
    assert result is not None
    assert result.startswith("data:image/png;base64,")


def test_find_logo_data_uri_returns_data_uri_for_jpg(tmp_path):
    (tmp_path / "nike.jpg").write_bytes(b"\xff\xd8\xff")
    result = find_logo_data_uri("nike", logos_dir=tmp_path)
    assert result is not None
    assert result.startswith("data:image/jpeg;base64,")


def test_find_logo_data_uri_prefers_png_over_jpg(tmp_path):
    (tmp_path / "brand.png").write_bytes(b"\x89PNG")
    (tmp_path / "brand.jpg").write_bytes(b"\xff\xd8")
    result = find_logo_data_uri("brand", logos_dir=tmp_path)
    assert result.startswith("data:image/png;base64,")
