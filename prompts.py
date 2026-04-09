from brand import BrandConfig

SYSTEM_PROMPT = """You are an expert email marketer and MJML developer. Your job is to create high-performing marketing emails.

MJML RULES:
- Use only valid MJML 4 tags: mjml, mj-head, mj-attributes, mj-all, mj-body, mj-section, mj-column, mj-text, mj-button, mj-image, mj-divider, mj-spacer
- Every email must start with <mjml> and end with </mjml>
- Sections contain columns, columns contain content elements
- Use mj-attributes in mj-head to set global styles (font-family, padding, color)
- Buttons must use mj-button with href="#" as placeholder
- Do NOT include mj-image unless a real image URL is explicitly provided — never use placeholder image services (via.placeholder.com, placekitten.com, picsum.photos, etc.)

EMAIL BEST PRACTICES:
- Single, clear call-to-action (CTA)
- Benefit-led headline above the fold
- Short, punchy body copy (under 80 words)
- Create urgency or excitement without being spammy
- Mobile-first: single-column layout

OUTPUT FORMAT:
Return ONLY a valid JSON object with exactly these four keys:
- "subject_lines": array of exactly 3 subject line strings (under 50 chars each)
- "preheader": string (under 100 chars, teases the email content)
- "mjml": string (complete, valid MJML markup)
- "rationale": string (2-3 sentences explaining key design decisions)

Do not include any text outside the JSON object. Do not use markdown code fences."""


def build_user_prompt(
    brand: BrandConfig,
    email_type: str,
    email_classification: str,
    target_customers: str,
    goal: str,
) -> str:
    brand_lines = [f"Brand: {brand.name}"]
    if brand.primary_color:
        brand_lines.append(f"Primary color: {brand.primary_color}")
    if brand.logo_url:
        brand_lines.append(f"Logo URL: {brand.logo_url}")
    brand_section = "\n".join(brand_lines)

    if brand.primary_color:
        styling = (
            f"- Use {brand.primary_color} as the accent color for buttons, headers, and dividers"
        )
    else:
        styling = "- Use a clean neutral palette (#333333 for text, #0066CC for buttons)"

    if brand.logo_url:
        styling += "\n- Add the logo as mj-image at the top of the email"

    return f"""Create a marketing email with the following details:

{brand_section}

Email type: {email_type}
Classification: {email_classification}
Target customers: {target_customers}
Goal: {goal}

Brand styling instructions:
{styling}

Return a single JSON object with keys: subject_lines (array of 3 strings), preheader (string), mjml (string), rationale (string)."""
