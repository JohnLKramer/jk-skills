---
name: writing-readmes
description: Use when creating a new README or substantially rewriting an existing one for a developer-facing tool, library, or service.
---

# Writing READMEs

## Overview

A README's job is to sell the *why* before it explains the *how*. A developer decides in the first few seconds whether this is worth their time — lead with the problem it solves and the payoff (speed, safety, simplicity, security), not a dry technical definition.

## When to Use

- Writing a README from scratch for a new project.
- Substantially rewriting an existing README for tone, structure, or skimmability.
- **Not for:** inline code comments (see `writing-code-comments`), generated API reference docs, or internal design docs nobody outside the team reads.

## Process

1. **Read what already exists** — current README, CHANGELOG, LICENSE, CONTRIBUTING, package manifest, any logo/badge assets. This is your only source of truth for features and status.
2. **Propose a section outline to the user before drafting** the full rewrite. Show the structure (below), flag anything you couldn't find (no logo, no CHANGELOG, etc.), and get a nod before writing prose.
3. **Draft** following the structure and voice rules below.
4. **Diff against the original** before finishing — every code block, command, config snippet, and link that existed must still be present. Style changes, not content changes.

## Structure (top to bottom)

1. **Logo** — if one exists in the repo, centered, near the very top. Don't invent one.
2. **Doc tabs** — a row of links to other top-level docs, directly under the title/badges, so they read like tabs:
   ```markdown
   [Changelog](CHANGELOG.md) · [License](LICENSE) · [Contributing](CONTRIBUTING.md)
   ```
   Only link docs that actually exist in the repo.
3. **The Hook** — 2–4 sentences. What problem this solves and why a developer should care, before any technical definition of what it *is*.
4. **Table of Contents** — anchor links matching the real headings below.
5. **Quickstart** — the minimum copy-pasteable steps to get it running.
6. **Feature / deep-dive sections** — one per major capability, ordered by what a new user hits first, progressing from overview to detail.
7. **Deeper technical sections** (architecture, security model, protocol specifics) — explain the *why* in plain English before dropping into RFCs, tables, or spec-level detail.

## Voice

- Active, confident, second person ("you get X"). Avoid "This repository contains..." openings.
- Bullets lead with a verb or outcome: "Restores your dotfiles in one command," not "Dotfile restoration is supported."
- Short paragraphs, bold key terms, visual hierarchy over dense blocks.

## What NOT to Do

- Don't omit, assume, or invent feature/status details — rewrite for style only, never for content.
- Don't drop code blocks, commands, config references, or links during a rewrite.
- Don't bury the hook under a badge wall or a spec-first technical definition.
- Don't add a logo, badge, or doc-tab link for something that doesn't exist in the source material.

## Quick Reference

| Section | Purpose | Placement |
|---|---|---|
| Logo | Brand/recognition | Top, centered |
| Doc tabs (Changelog/License/Contributing) | Wayfinding to other top-level docs | Just under title/badges |
| Hook | Why a developer should care | First prose, before any spec definition |
| Table of Contents | Skimmability | Before the first section |
| Quickstart | Get running fast | Early, before feature deep-dives |
| Feature sections | Depth on demand | After quickstart, progressive disclosure |
| Architecture/security | Rigor for those who need it | Last, why-in-plain-English before specs |

## Reference READMEs

Good examples of hook, skimmability, and humanized voice:
- https://github.com/aimeos/aimeos-typo3#readme
- https://github.com/alichtman/shallow-backup#readme
- https://github.com/Abblix/Oidc.Server#readme
- https://github.com/AntonioFalcaoJr/EventualShop#readme

## Common Mistakes

- Opening with "X is a Y that does Z" instead of the problem/benefit.
- A Table of Contents whose anchors don't match the actual headings.
- Paraphrasing a claim during rewrite until it's no longer factually the same claim.
- Adding polish (logo, tabs, badges) that isn't backed by a real asset or file in the repo.
