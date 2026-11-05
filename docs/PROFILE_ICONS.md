# Portfolio icon standard

Argus Overview and hygiene (`BRAND-ICON-MISSING`) expect a **canonical square brand mark** in each public product repo.

## Canonical paths (preferred first)

1. `branding/assets/app-icon-512.png`
2. `branding/assets/logo-mark.png`
3. `docs/brand/logo-official.png`
4. `docs/assets/app-icon-512.png`
5. `docs/assets/icon.png`
6. `branding/assets/app-icon-512.svg` (only if larger than the Golden Path stub; see below)

Config source of truth: [`config/profile_icons.yaml`](../config/profile_icons.yaml).

## Naming

| File | Meaning |
|------|---------|
| `app-icon-512.png` | Square app icon ≥512px, no wordmark |
| `logo-mark.png` | Square brand mark for README / Overview |
| `logo-official.png` | Product brand plate under `docs/brand/` |
| `app-icon-512.svg` | Same role as PNG when it is a real mark |

## Do not

- Leave `branding/assets/app-icon-512.svg` as the tiny Golden Path triangle stub (≤400 bytes).
- Rely on Open Graph social cards as the only “icon”.
- Put the only mark under `.cursor/` (ignored for Overview discovery).

## Fallbacks Argus still discovers

Tauri `examples/desktop/src-tauri/icons/icon.png`, Android `mipmap-xxxhdpi/ic_launcher.png`, Fastlane `icon.png`, `branding/template/logo-mark.png` (when assets are still stubs). Hygiene still prefers a canonical PNG (or a non-stub SVG).
