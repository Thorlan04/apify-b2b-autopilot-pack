---
name: eu-b2b-compliance-auditor
description: Comprehensive EU & French B2B compliance auditor for AI agents. Queries official French government registry (recherche-entreprises.api.gouv.fr) for SIREN, SIRET, NAF/APE code, legal representatives, and addresses. Calculates exact mathematical Intra-EU VAT numbers (modulo 97). Audits websites for GDPR legal notices, European Accessibility Act (EAA 2025) compliance, and AI agent readiness (llms.txt, robots.txt, schema.org).
version: 1.0.0
author: Cedric Jover
tags:
  - compliance
  - b2b-enrichment
  - siren-siret
  - eu-vat
  - gdpr-audit
  - eaa-accessibility
  - mcp-tools
---

# EU B2B Compliance & Legal Auditor Skill

An autonomous AI agent skill and MCP toolset engineered for B2B intelligence, compliance verification, and sales prospecting across European and French enterprises.

## When to Use This Skill
Activate this skill whenever the user asks to:
- Verify French corporate entities, find SIREN or SIRET numbers, or list corporate officers/executives.
- Calculate or validate Intra-Community EU VAT numbers from French SIREN identifiers.
- Conduct a GDPR compliance audit (detection of *Mentions Légales*, *Politique de Confidentialité*, CMP cookie banners, and marketing trackers).
- Verify European Accessibility Act (EAA 2025) and WCAG 2.1 compliance (`lang` tags, image `alt` attributes, form labels, HTML5 landmarks).
- Inspect AI Agent & Generative Engine Readiness (presence of `/llms.txt`, permissions for `GPTBot`, `ClaudeBot`, and `PerplexityBot` in `robots.txt`, and Schema.org JSON-LD).

## Available Tools & Capabilities

### 1. Official French Enterprise Registry Search (`query_api_gouv_entreprise`)
Queries the official French State open API (`https://recherche-entreprises.api.gouv.fr/search`) without requiring any API keys.
- **Input**: Company name or domain (e.g., `doctolib.fr`, `ovhcloud.com`).
- **Output**:
  - `siren`: 9-digit official identifier.
  - `siret`: 14-digit establishment identifier.
  - `company_name`: Official legal denomination.
  - `naf_code`: Main economic activity code (e.g., `62.01Z`).
  - `employee_bracket`: Official staff bracket.
  - `address`: Registered head office address.
  - `legal_representatives`: List of directors and legal officers with their titles.

### 2. Intra-Community EU VAT Calculation (`compute_french_vat`)
Applies the official European modulo 97 mathematical key algorithm:
$$\text{Key} = (12 + 3 \times (\text{SIREN} \pmod{97})) \pmod{97}$$
Formatted as `FR{Key:02d}{SIREN}`.

### 3. Website Compliance & Accessibility Auditor (`audit_website_compliance`)
Performs automated multi-point audits yielding 3 actionable scores (0-100):
- **GDPR Score**: Verifies mandatory legal disclosure pages and prior consent mechanisms.
- **EAA 2025 Score**: Tests accessibility barriers for screen readers.
- **AI Readiness Score**: Confirms domain discoverability by LLMs and AI search engines.
- **Actionable Fixes**: Generates ready-to-sell remediation recommendations.

## Usage Instructions for AI Agents (Claude Code, Cursor, Copilot)

When an agent needs to perform an audit:
1. Call the compliance script or MCP tool with the target domain.
2. Return a structured executive table with legal identifiers and compliance scores.
3. List prioritized actionable fixes for any detected non-compliance.
