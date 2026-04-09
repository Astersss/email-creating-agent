import json
import os
import re
from datetime import datetime
from pathlib import Path
from brand import BrandConfig, load_brands, load_model
from agent import EmailAgent, resolve_image_strategy, ImageStrategy

MINIMAX_API_KEY = "sk-api-A3aHSpnsft2LIJcji5z45FFC4Qx3S0Ed8RV7LuTJSJC1XH9XcWN1Adw6HjJS2mrljHSQqyowBR1Hph9g65simY8d_5ypq6C7ka8_6dolS8iDR5pBS3AdtCI"
OUTPUT_DIR = Path(__file__).parent / "output"


def make_brand_id(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def select_brand(brands: list[BrandConfig]) -> BrandConfig:
    print("\nAvailable brands:")
    for i, brand in enumerate(brands, 1):
        color_info = f" ({brand.primary_color})" if brand.primary_color else ""
        print(f"  {i}. {brand.name}{color_info}")
    print("  0. Enter custom brand")

    while True:
        choice = input(f"\nSelect brand [0-{len(brands)}]: ").strip()
        if choice == "0":
            return _enter_custom_brand()
        if choice.isdigit() and 1 <= int(choice) <= len(brands):
            return brands[int(choice) - 1]
        print(f"Please enter a number between 0 and {len(brands)}.")


def _enter_custom_brand() -> BrandConfig:
    while True:
        name = input("Brand name: ").strip()
        if name:
            break
        print("Brand name cannot be empty.")
    color = input("Primary color (hex, optional — press Enter to skip): ").strip() or None
    logo = input("Logo URL (optional — press Enter to skip): ").strip() or None
    return BrandConfig(id=make_brand_id(name), name=name, primary_color=color, logo_url=logo)


def prompt_campaign_inputs() -> dict:
    print()
    required_fields = [
        (
            "email_type",
            "Email type",
            "What kind of email is this?",
            "e.g. promotional, announcement, seasonal, re-engagement, loyalty reward",
        ),
        (
            "email_classification",
            "Email classification",
            "Who is the relationship between sender and recipient?",
            "e.g. B2C (brand to consumer), B2B (brand to business), loyalty members only",
        ),
        (
            "target_customers",
            "Target customers",
            "Describe the audience receiving this email — their demographics, interests, or relationship with the brand.",
            "e.g. Starbucks loyalty members aged 18-35, coffee and tea enthusiasts",
        ),
        (
            "goal",
            "Campaign goal",
            "What do you want recipients to do after reading this email?",
            "e.g. Drive trial purchases of a new seasonal drink, increase app downloads, boost weekend foot traffic",
        ),
    ]
    inputs = {}
    for key, label, description, example in required_fields:
        print(f"\n{label}")
        print(f"  {description}")
        print(f"  Example: {example}")
        while True:
            value = input(f"  > ").strip()
            if value:
                break
            print(f"  {label} cannot be empty.")
        inputs[key] = value
    return inputs


_TINY_PNG = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="


def _strip_base64_for_preview(mjml: str) -> str:
    import re
    return re.sub(r'data:[^;]+;base64,[A-Za-z0-9+/=]+', _TINY_PNG, mjml)


def _make_slug(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '_', text.strip().lower()).strip('_')


def save_output(brand_id: str, email_type: str, package: dict) -> tuple[Path, Path]:
    OUTPUT_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    stem = f"{brand_id}_{_make_slug(email_type)}_{ts}"
    mjml_path = OUTPUT_DIR / f"{stem}.mjml"
    package_path = OUTPUT_DIR / f"{stem}_package.json"
    mjml_path.write_text(_strip_base64_for_preview(package["mjml"]), encoding="utf-8")
    package_path.write_text(json.dumps(package, indent=2, ensure_ascii=False), encoding="utf-8")
    return mjml_path, package_path


def print_results(package: dict, mjml_path: Path, package_path: Path) -> None:
    print("\n=== SUBJECT LINES ===")
    for i, line in enumerate(package["subject_lines"], 1):
        print(f"  {i}. {line}")
    print(f"\n=== PREHEADER ===\n  {package['preheader']}")
    if "_warning" in package:
        print(f"\n⚠️  WARNING: {package['_warning']}")
    print(f"\n=== RATIONALE ===\n  {package['rationale']}")
    print("\n=== OUTPUT FILES ===")
    print(f"  MJML:    {mjml_path}")
    print(f"  Package: {package_path}")


def main():
    api_key = os.environ.get("MINIMAX_API_KEY", MINIMAX_API_KEY)
    brands = load_brands()
    model = load_model()

    print("=== Email Agent ===")
    brand = select_brand(brands)

    color_info = f" ({brand.primary_color})" if brand.primary_color else ""
    print(f"\nBrand: {brand.name}{color_info}")
    print(f"Model: {model}")

    inputs = prompt_campaign_inputs()

    product_image_url = None
    if resolve_image_strategy(inputs["email_type"]) == ImageStrategy.PRODUCT_PHOTO:
        print("\nProduct image URL (optional — press Enter to skip for text-only email)")
        product_image_url = input("  > ").strip() or None

    print("\nGenerating email...")
    agent = EmailAgent(api_key=api_key)
    package = agent.generate(brand=brand, model=model, product_image_url=product_image_url, **inputs)

    mjml_path, package_path = save_output(brand.id, inputs["email_type"], package)
    print_results(package, mjml_path, package_path)


if __name__ == "__main__":
    main()
