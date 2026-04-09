from brand import BrandConfig

SYSTEM_PROMPT = """You are an expert email marketer and MJML developer. Your job is to create high-performing marketing emails.

MJML RULES:
- Use only valid MJML 4 tags: mjml, mj-head, mj-attributes, mj-all, mj-body, mj-section, mj-column, mj-text, mj-button, mj-image, mj-divider, mj-spacer
- Every email must start with <mjml> and end with </mjml>
- Sections contain columns, columns contain content elements (mj-text, mj-button, mj-image, mj-divider, mj-spacer must always be inside mj-column — never directly under mj-section or mj-body)
- Use mj-attributes in mj-head to set global styles (font-family, padding, color)
- Buttons must use the brand website URL as href, or "#" if none provided
- Do NOT use any real image URLs in src attributes — never use external URLs, placeholder services, or Wikipedia images

IMAGE RULES (CRITICAL — follow exactly):
- For product/promotional/sale/launch/abandoned cart emails: you MUST include exactly one <mj-image src="{{IMAGE_URL}}" alt="..." width="600px" align="center" /> in the MJML body to show the product. This is REQUIRED. Place it prominently after the headline. Do NOT skip this.
- For mood/seasonal/celebratory/re-engagement/loyalty/welcome/event emails: you MUST include exactly one <mj-image src="{{IMAGE_URL}}" alt="..." width="600px" align="center" /> AND include an "image_prompt" field in your JSON output (max 200 chars, atmospheric/mood-focused, no brand logos or real products)
- For transactional emails only: no mj-image, no {{IMAGE_URL}}, no image_prompt
- The literal string {{IMAGE_URL}} must appear as the src value — do not replace it with anything else
- If logo is provided: always include it as the first mj-image using src="{{LOGO_URL}}" exactly as written

EMAIL BEST PRACTICES:
- Single, clear call-to-action (CTA)
- Benefit-led headline above the fold
- Short, punchy body copy (under 80 words)
- Create urgency or excitement without being spammy
- Mobile-first: single-column layout
- Use brand voice and tagline to inform copy tone

OUTPUT FORMAT:
Return ONLY a valid JSON object with exactly these keys:
- "subject_lines": array of exactly 3 subject line strings (under 50 chars each)
- "preheader": string (under 100 chars, teases the email content)
- "mjml": string (complete, valid MJML markup — never use real image URLs except logo_url)
- "rationale": string (2-3 sentences explaining key design decisions)
- "image_prompt": string (only for mood/seasonal/celebratory emails — omit this key entirely for all other types)

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
    if brand.secondary_color:
        brand_lines.append(f"Secondary color: {brand.secondary_color}")
    if brand.logo_url:
        brand_lines.append("Logo: provided")
    if brand.font_family:
        brand_lines.append(f"Font family: {brand.font_family}")
    if brand.brand_voice:
        brand_lines.append(f"Brand voice: {brand.brand_voice}")
    if brand.website_url:
        brand_lines.append(f"Website URL: {brand.website_url}")
    if brand.tagline:
        brand_lines.append(f"Tagline: {brand.tagline}")
    brand_section = "\n".join(brand_lines)

    if brand.primary_color:
        styling = f"- Use {brand.primary_color} as the accent color for buttons, headers, and dividers"
        if brand.secondary_color:
            styling += f"\n- Use {brand.secondary_color} for background sections or subtle accents"
    else:
        styling = "- Use a clean neutral palette (#333333 for text, #0066CC for buttons)"

    if brand.logo_url:
        styling += '\n- Add the logo as the first mj-image using src="{{LOGO_URL}}"'

    font = brand.font_family or "Avenir, Helvetica, Arial, sans-serif"
    styling += f"\n- Use font-family: {font}"

    return f"""Create a marketing email with the following details:

{brand_section}

Email type: {email_type}
Classification: {email_classification}
Target customers: {target_customers}
Goal: {goal}

Brand styling instructions:
{styling}

Return a single JSON object with keys: subject_lines (array of 3 strings), preheader (string), mjml (string), rationale (string), and optionally image_prompt (string, mood emails only)."""
