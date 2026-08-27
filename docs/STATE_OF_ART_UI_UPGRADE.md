# PSB State-of-the-Art UI/UX Upgrade

This release applies the supplied PSB crest and a trust-first enterprise design system to the hardened qualification and digital authorization platform.

## Product direction
- Regulated maritime enterprise product, not a marketing-style SaaS dashboard.
- Deep navy and PSB green are the only strong brand accents.
- Moderate information density, restrained motion, clear current-task emphasis.
- Existing Streamlit architecture retained; no risky framework migration.

## Key UX changes
- High-resolution PSB crest master used throughout the application.
- Login renamed to **Qualification & Digital Authorization Portal**.
- Task navigation now uses direct page buttons instead of section select boxes.
- Current page is explicitly highlighted with a PSB-green state indicator.
- Desktop navigation remains fixed; mobile uses the controlled Streamlit drawer.
- Sign out remains visually separated and sticky at the bottom.
- Header, metrics, forms, tables, tabs, alerts and empty states use one tokenized design language.
- Keyboard focus indicators and reduced-motion behavior are included.
- Tabs remain horizontally scrollable rather than wrapping into unreadable stacks on narrow screens.
- Certificate styling now matches the PSB navy/green institutional brand.

## Brand tokens
- Ink Navy: `#010819`
- Deep Navy: `#061B36`
- Operational Navy: `#0A2F5D`
- PSB Green: `#095B25`
- Mist Background: `#F4F7F6`
- Surface: `#FFFFFF`
- Border: `#D9E2E0`

## Design quality contract
Automated tests verify the high-resolution logo, global brand tokens, explicit active navigation, reduced-motion/focus support and current product naming.
