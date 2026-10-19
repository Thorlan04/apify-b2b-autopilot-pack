# ⚖️ EU B2B Compliance & Legal Auditor (SIREN, VAT, GDPR, EAA 2025, AI Readiness)

> **The ultimate B2B lead enrichment & compliance auditing Actor on Apify Store.**  
> Extract verified French and European corporate registry records (SIREN, SIRET, Intra-EU VAT, NAF, Executives) while automatically auditing websites for **GDPR legal compliance**, the mandatory **European Accessibility Act (EAA 2025)**, and **AI Agent & GEO Readiness** (`llms.txt`, `robots.txt`, `schema.org`).

---

## 🚀 Key Value Propositions

1. **Zero-Proxy Cost (100% Free Public Rails)**: Uses the official French State open data API (`recherche-entreprises.api.gouv.fr`) and direct lightweight HTTP requests. No expensive residential proxies required!
2. **Instant B2B Lead Enrichment**: Given a domain or brand name, instantly retrieves legal company name, head office address, SIREN, SIRET, NAF/APE activity code, employee bracket, and calculates the exact mathematical EU VAT number.
3. **Triple Compliance Scoring (0 to 100)**:
   - **GDPR Score**: Mentions légales detection, Privacy Policy presence, CMP / Cookie consent banner audit, and tracking scripts detection.
   - **European Accessibility Act (EAA) Score**: Checks `<html>` lang tag, image `alt` attributes coverage, labeled form inputs, and HTML5 semantic structure.
   - **AI Agent & GEO Readiness Score**: Verifies `/llms.txt`, detects AI bot blocks (`GPTBot`, `ClaudeBot`, `PerplexityBot`), and validates Schema.org JSON-LD.
4. **Actionable Fixes List**: Returns ready-to-sell audit findings that digital agencies, web developers, and legal consultants can directly include in commercial proposals.

---

## 📋 Input Configuration

You can provide domains or company names:

```json
{
  "targets": [
    "doctolib.fr",
    "ovhcloud.com"
  ],
  "timeout_seconds": 15,
  "deep_scan": true
}
```

### Input Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `targets` | Array of Strings | `["doctolib.fr", "ovhcloud.com"]` | Domains or business names to audit |
| `timeout_seconds` | Integer | `15` | Network timeout per domain |
| `deep_scan` | Boolean | `true` | Audit subpages (`/mentions-legales`, `/privacy`, `/llms.txt`) |

---

## 📊 Sample Output Data

```json
{
  "target": "doctolib.fr",
  "audited_url": "https://doctolib.fr",
  "company_name": "DOCTOLIB",
  "siren": "794598813",
  "siret": "79459881300054",
  "vat_number": "FR14794598813",
  "naf_code": "62.01Z",
  "employee_bracket": "1000 à 1999 salariés",
  "address": "54 Quai Charles Pasqua 92300 Levallois-Perret",
  "legal_representatives": [
    "Stanislas NIOX-CHATEAU (Président)",
    "Thomas DUPONT (Directeur Général)"
  ],
  "gdpr_compliance_score": 100,
  "european_accessibility_eaa_score": 90,
  "ai_agent_readiness_score": 65,
  "actionable_fixes": [
    "AI READINESS: Deploy a standardized /llms.txt file to allow Claude, ChatGPT, and Perplexity to index your documentation."
  ],
  "scanned_at": "2026-10-18T10:00:00Z"
}
```

---

## ⚡ Integration Workflows

### 1. Make.com (Integromat)
1. Add an **Apify** module: **Run an Actor**.
2. Actor ID: `your-username/eu-b2b-compliance-auditor`.
3. Input JSON:
   ```json
   {
     "targets": ["{{1.domain}}"]
   }
   ```
4. Map the resulting `actionable_fixes`, `vat_number`, and `gdpr_compliance_score` to your CRM (HubSpot, Salesforce, Airtable) or automatically draft a cold outreach email in Gmail.

### 2. n8n
```json
{
  "nodes": [
    {
      "name": "Apify Auditor",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "https://api.apify.com/v2/acts/your-username~eu-b2b-compliance-auditor/run-sync-get-dataset-items?token=YOUR_APIFY_TOKEN",
        "method": "POST",
        "body": {
          "targets": ["={{ $json.domain }}"]
        }
      }
    }
  ]
}
```

### 3. Python / cURL
```bash
curl -X POST "https://api.apify.com/v2/acts/your-username~eu-b2b-compliance-auditor/run-sync-get-dataset-items?token=YOUR_APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"targets": ["ovhcloud.com"]}'
```

---

## 💰 Compute & Pricing Economics
- **Memory Consumption**: 256 MB RAM
- **Average Run Duration**: ~2 to 4 seconds per target
- **Cost per run**: ~$0.0003 per company audit
- On Apify's **$5 Free Monthly Credit Tier**, you can audit **over 12,000 businesses per month** completely free of charge!

---

*Last Automated Maintenance: 2026-10-19*
