# AGENTS.md

Shared operating instructions for Cursor Cloud Agents, Codex, ChatGPT Work, and Muse (Jack) working in this repository.

GitHub pull requests are the review and approval boundary. Do not merge or deploy unless a human explicitly approves that step.

## What this project is

- **Vancouver Island Pro Roofing** — a static lead-generation website for Justin's roofing business. Live site: https://vancouverislandproroofing.com
- Hand-written **HTML + CSS** with optimized WebP imagery. No framework, no JavaScript build, no package manager.
- Files: `index.html`, `services.html`, `contact.html`, `404.html`, `styles.css`, `sitemap.xml`, `robots.txt`, `_headers` (Cloudflare response headers), `Galleries/` and image assets. The contact/quote flow runs through Formspree.

## Commands

- **There is no build step and no test suite in this repo — do not invent one.** No `package.json` exists and none should be added without a human asking.
- Validate changes by opening the edited HTML files directly and checking rendering, links, and the contact flow by eye.
- Keep the site dependency-free and fast. Do not introduce a framework, bundler, or build step without explicit human direction.

## Deployment

- Cloudflare **Pages** project `justin-roofing`, connected to this repo: pushes to `main` auto-deploy via the Cloudflare Git integration, serving the repo root as static files.
- A failed deploy never replaces live production — the previous deployment keeps serving.
- "Deployed" means a deployment record tying the live version to the exact commit, plus one runtime check of the changed behaviour (e.g. loading the changed page live). Anything less is "reported", not deployed.

## Team conventions (bind every agent here)

1. Before merging any PR, fetch its **reviews AND review comments** and disposition every finding. Codex review triggers when a draft PR is marked ready or on "@codex review" — it does not run on drafts, so mark ready and wait for that window before merging.
2. Verify code from **source bytes** in the repo — never from another agent's transcription or summary of code.
3. Evidence discipline: "reviewed" names the exact commit; "deployed" requires the deployment record + runtime check described above.
4. Small, focused, reversible changes. No drive-by refactors. No PRs beyond the assigned task.
5. PR bodies and commit messages must not include a "Do not merge" line unless a human explicitly asks for one.

## Owner's hard constraints

- **No customer or third-party sends or posts without David's approval.**
- **No spending.** Free tiers only.
- **Never publish David's home address** — it is private; hidden verification-only fields at most.
- **Truthful marketing only** — no invented claims, prices, reviews, service areas, or clients for the roofing business. **EuroPools is a separate, gated business** (David's father's company) and is NOT a EuroDigital client — take no EuroPools actions from this repo and never list it as a client.
- Never commit secrets, form endpoints beyond the existing Formspree setup, or customer data.
