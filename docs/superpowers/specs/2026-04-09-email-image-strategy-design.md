# Email Image Strategy Design

**Date:** 2026-04-09
**Status:** Approved

## Problem

The current system produces broken/unreliable images in generated MJML because the text model freely inserts arbitrary external URLs (e.g. Wikipedia images). The layout is also visually weak: no branded header, poor visual hierarchy, generic copy tone.

## Goals

1. Replace unreliable image URLs with a deterministic, type-driven image strategy
2. Support AI-generated mood imagery (MiniMax `image-01`) where appropriate, with text-only fallback
3. Enrich brand configuration to improve copy quality and visual fidelity

---

## Image Strategy

### Decision Tree

```
email_type → ImageStrategy enum
  PRODUCT_PHOTO  → use brand.product_image_url (or omit if absent)
  MOOD_GENERATED → call image-01 API; on any failure, omit image
  NONE           → no image block at all
```

### Strategy Mapping (from email_type, case-insensitive)

| Strategy | Email types |
|---|---|
| `PRODUCT_PHOTO` | promotional, sale, product launch, new arrival, abandoned cart |
| `MOOD_GENERATED` | seasonal, loyalty reward, milestone, re-engagement, win-back, welcome, event invitation |
| `NONE` | transactional, newsletter, unrecognized (safe default) |

**Rationale:**
- Product-focused emails require authentic brand assets — AI-generated product shots erode trust
- Mood/seasonal emails benefit from atmospheric imagery where authenticity isn't required
- Unknown email types default to `NONE` to avoid any image-related failures
- Logo is always sourced from `brand.logo_url` — never generated, never faked

### Fallback Rules

- `PRODUCT_PHOTO` + no `brand.product_image_url` → omit image block
- `MOOD_GENERATED` + `image-01` API failure (any error or content safety block) → omit image block
- No `mj-image` with broken/unresolved `src` is ever emitted

---

## Implementation Approach (Option A: Two-step agent)

1. **Text model call** — generates `mjml`, `subject_lines`, `preheader`, `rationale`, and optionally `image_prompt`
   - System prompt instructs: emit `image_prompt` only for mood/seasonal/celebratory emails; include `{{IMAGE_URL}}` marker in MJML where image should appear
   - For product/promotional emails: no `mj-image` block in MJML, no `image_prompt`
   - For no-image emails: no `mj-image` block, no `image_prompt`

2. **Agent image resolution** — Python code owns the strategy decision:
   - Resolve `ImageStrategy` from `email_type`
   - `PRODUCT_PHOTO` → `brand.product_image_url`
   - `MOOD_GENERATED` → call `POST https://api.minimax.io/v1/image_generation` with `image_prompt`; catch all exceptions
   - Patch resolved URL into MJML by replacing `{{IMAGE_URL}}` marker
   - If no URL resolved → strip the `mj-image` block containing the marker from MJML

3. **Output** — clean MJML with either a real image or no image block; never a broken src

---

## Brand Config Enhancements (`brands.json`)

New fields added to `BrandConfig`:

| Field | Type | Purpose |
|---|---|---|
| `secondary_color` | `str \| None` | Background/accent color for two-tone palette |
| `product_image_url` | `str \| None` | Real product photo for promotional emails |
| `font_family` | `str \| None` | Brand typography (falls back to `Avenir, Helvetica, Arial, sans-serif`) |
| `brand_voice` | `str \| None` | Copy tone descriptor fed into the user prompt |
| `website_url` | `str \| None` | Used as CTA button href instead of `#` |
| `tagline` | `str \| None` | Brand tagline to inform headline generation |

---

## Files Changed

| File | Change |
|---|---|
| `brand.py` | Add 6 new optional fields to `BrandConfig` |
| `brands.json` | Populate new fields for existing brands |
| `agent.py` | Add `ImageStrategy` enum, `resolve_image_strategy()`, `generate_mood_image()`, MJML patching logic |
| `prompts.py` | Update system prompt (no external URLs, emit `{{IMAGE_URL}}` marker + `image_prompt`) and user prompt (include new brand fields) |

---

## Out of Scope

- Per-campaign `product_image_url` override (brand-level only for now)
- Image caching (24h URL expiry is acceptable for current use)
- B2B vs B2C image strategy differentiation
