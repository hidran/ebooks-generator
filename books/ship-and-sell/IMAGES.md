# Image inventory (sources/images/)

Every file in `sources/images/` with the manual stage it illustrates. When
authoring chapters, copy the needed files into `figures/cap-XX/` and reference
them book-root-relative (`figures/cap-XX/<name>.png`) per the repo playbook.
All are real production assets from the app the manual was distilled from.

## Stage 3 — App icon & assets

| File | What it shows |
|---|---|
| `stage03-icon-source-svg.png` | The icon's SOURCE artwork (a single SVG) rendered at 1024×1024 — the input side of the asset-generation pipeline. Full-bleed, square corners: iOS applies its own mask. |
| `stage03-splash-source-svg.png` | The splash-screen source SVG, same pipeline. |
| `stage03-app-icon-1024-rgb-no-alpha.png` | The GENERATED 1024×1024 marketing icon exactly as uploaded: 8-bit RGB, **no alpha channel** (an alpha channel is rejected at upload with ITMS-90717 — the Stage 3 trap), no rounded corners. |

## Stage 4 — Screenshots

| File | What it shows |
|---|---|
| `stage04-iphone69-1320x2868-dashboard.png` | A real App Store screenshot at the EXACT 6.9" requirement (1320×2868). First slot of the submitted set. |
| `stage04-iphone69-1320x2868-conversation.png` | Another 6.9" shot — the core feature, framed as the "story" slot. |
| `stage04-ipad13-2064x2752-dashboard.png` | The iPad 13" companion at its EXACT requirement (2064×2752) — both device classes are mandatory. |
| `stage04-iphone69-contact-sheet.png` | All 13 submitted iPhone screenshots as one 5×3 grid — shows how a full set tells the product story in order (dashboard → courses → lesson → conversation → …). Good as the stage's opening figure. |

## Stages 2, 6, 7 — referenced by the source HTML (keep filenames)

| File | Stage | What it shows |
|---|---|---|
| `signin-with-apple-auth-page.png` | 2 | The app's real sign-in screen: email/password plus Google, Facebook, GitHub **and Apple** buttons — Guideline 4.8 satisfied, Apple as an equal option. |
| `xcode-product-menu-archive.png` | 6 | Xcode with the Product menu open: Run/Test/Profile/Analyze/**Archive**, toolbar scheme + destination visible (the greyed-Archive trap context). |
| `xcode-organizer-distribute.png` | 7 | Xcode Organizer, Archives tab: the real v1.0 history — builds 1.0 (1) and 1.0 (2) both "Uploaded to Apple" (Appendix B's build-number story), Distribute App / Validate App buttons, archive details. |

## Part III — Payments (already referenced by the source HTML)

These are referenced from `sources/ship-and-sell.html` as `images/<name>` and
belong to Stages 21, 25 and 26; keep their filenames when moving to `figures/`.

| File | Stage | What it shows |
|---|---|---|
| `subscription-tab-free.png` | 21 | The rendered offering: one card per RevenueCat package, monthly/yearly toggle. |
| `checkout-sandbox.png` | 25 | Paddle sandbox checkout — Test Mode badge, €0.00 trial framing, static "Qty: 1", return link: every element verifies a config step. |
| `subscription-tab-plus.png` | 26 | Subscriber status screen: plan card, dunning banner, Paddle notice, Manage + Cancel. |
| `billing-issue-banner.png` | 26 | The "fix payment method" dunning banner on the home screen. |
| `cancel-dialog.png` | 26 | Period-end cancellation confirm dialog ("keep access until {date}; progress never deleted"). |
