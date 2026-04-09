import json
import os
from pathlib import Path
from agent import EmailAgent


INPUTS = {
    "email_type": "promotional",
    "email_classification": "B2C",
    "target_customers": "Starbucks loyalty members aged 18-35, coffee and tea enthusiasts",
    "goal": "Drive trial purchases of a newly launched seasonal drink",
}

OUTPUT_DIR = Path(__file__).parent / "output"


def main():
    api_key = os.environ.get("MINIMAX_API_KEY")
    if not api_key:
        raise EnvironmentError("MINIMAX_API_KEY environment variable is not set")

    print("Generating email package...")
    print(f"Campaign: {INPUTS['goal']}")
    print(f"Audience: {INPUTS['target_customers']}\n")

    agent = EmailAgent(api_key=api_key)
    package = agent.generate(**INPUTS)

    OUTPUT_DIR.mkdir(exist_ok=True)

    mjml_path = OUTPUT_DIR / "email.mjml"
    mjml_path.write_text(package["mjml"], encoding="utf-8")

    package_path = OUTPUT_DIR / "email_package.json"
    package_path.write_text(json.dumps(package, indent=2, ensure_ascii=False), encoding="utf-8")

    print("=== SUBJECT LINES ===")
    for i, line in enumerate(package["subject_lines"], 1):
        print(f"  {i}. {line}")

    print(f"\n=== PREHEADER ===\n  {package['preheader']}")
    print(f"\n=== RATIONALE ===\n  {package['rationale']}")
    print("\n=== OUTPUT FILES ===")
    print(f"  MJML:    {mjml_path}")
    print(f"  Package: {package_path}")


if __name__ == "__main__":
    main()
