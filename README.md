# 🛸 Apify B2B Autopilot Pack

> **A 100% autonomous monorepo hosting 3 high-demand B2B Apify Actors**, engineered to run with **zero paid proxies**, powered by an automated **Weekly Self-Maintenance Engine**, and backed by a turnkey **French Micro-Entreprise BNC Tax & Accounting module**.

---

## 🏛️ Monorepo Architecture

```
apify-b2b-autopilot-pack/
├── .github/
│   └── workflows/
│       └── weekly_pack_updater.yml         # GitHub Actions cron (Mondays 04:00 UTC) + rebuild trigger
├── actors/
│   ├── 1-eu-b2b-compliance-auditor/        # Legal B2B Registry (SIREN/VAT) & GDPR/EAA/AI Audit
│   │   ├── .actor/
│   │   │   ├── actor.json
│   │   │   ├── input_schema.json
│   │   │   └── dataset_schema.json
│   │   ├── src/
│   │   │   └── main.py
│   │   ├── signatures.json                 # AI bots, legal paths, CMP signatures, EAA rules
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── README.md                       # Apify Store sales listing & Make/n8n guides
│   │
│   ├── 2-ai-rag-markdown-extractor/        # Universal Web-to-Markdown, RAG Chunker & llms.txt
│   │   ├── .actor/
│   │   │   ├── actor.json
│   │   │   ├── input_schema.json
│   │   │   └── dataset_schema.json
│   │   ├── src/
│   │   │   └── main.py
│   │   ├── cleaning_rules.json             # Noise classes, popup selectors, chunking config
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── README.md                       # Sales listing for AI builders & vector DB pipelines
│   │
│   └── 3-ecommerce-json-intelligence/      # Proxy-Free E-Commerce Catalog, Prices & Stock
│       ├── .actor/
│       │   ├── actor.json
│       │   ├── input_schema.json
│       │   └── dataset_schema.json
│       ├── src/
│       │   └── main.py
│       ├── ecommerce_patterns.json         # Shopify, WooCommerce & Schema.org JSON-LD patterns
│       ├── Dockerfile
│       ├── requirements.txt
│       └── README.md                       # Sales listing for price tracking & competitor drops
│
├── brain_updater/
│   ├── auto_update_pack.py                 # Weekly maintenance script (version bump & signature enrich)
│   ├── test_all_actors.py                  # Syntax, schema & unit test verification engine
│   └── compta_manager.py                   # Micro-BNC French tax & accounting CLI manager
│
├── compta_impots/
│   ├── livre_des_recettes_bnc.csv          # Official French BNC revenue ledger (Apify payouts)
│   └── tableau_de_bord_fiscal.html         # Interactive standalone financial dashboard
│
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🤖 The 3 B2B Actors

### 1. `actors/1-eu-b2b-compliance-auditor/`
- **Target Audience**: B2B Lead Gen Agencies, Web Agencies, SEO/GEO Consultants, Legal Tech.
- **Zero-Proxy Technology**: Queries the official open data API of the French State (`recherche-entreprises.api.gouv.fr`) for SIREN, SIRET, official company name, NAF code, legal representatives, head office address, and calculates the exact mathematical EU VAT number via modulo 97 (`FR + key + SIREN`).
- **Scoring Engine (0 to 100)**:
  - `gdpr_compliance_score`: Legal notices, privacy policy, CMP cookie banner (Axeptio, Didomi, Tarteaucitron, Cookiebot), tracker discovery.
  - `european_accessibility_eaa_score`: Checks `html[lang]`, image `alt` attributes, labeled form inputs, semantic HTML5 structure according to the European Accessibility Act (EAA 2025).
  - `ai_agent_readiness_score`: Validates `/llms.txt`, probes `robots.txt` AI permissions (GPTBot, ClaudeBot, PerplexityBot), checks Schema.org JSON-LD.
- **Agency Deliverable**: Provides a structured `actionable_fixes` array ready to sell to prospects.

### 2. `actors/2-ai-rag-markdown-extractor/`
- **Target Audience**: AI Engineers, LLM App Builders (LangChain, LlamaIndex), Vector DB users (Pinecone, ChromaDB, Supabase, Qdrant).
- **Zero-Proxy Technology**: Direct clean HTML extraction with intelligent DOM pruning (strips navigational chrome, banners, cookie popups, sidebars, and scripts).
- **Pristine Markdown**: Converts HTML tables, code snippets, blockquotes, lists, and resolves relative hyperlinks into absolute URLs.
- **Vector-Ready RAG Chunking**: Splits content into semantic chunks respecting paragraph boundaries, with token estimations and indexing metadata.
- **Standardized `llms.txt`**: Automatically synthesizes a specification-compliant `/llms.txt` draft for the scraped domain.

### 3. `actors/3-ecommerce-json-intelligence/`
- **Target Audience**: E-commerce Brands, Retail Arbitrage, Dropshippers, Price Monitoring automations in Make and n8n.
- **Zero-Proxy Technology**: Detects public structured endpoints (`/products.json`, `/collections/all/products.json`, WooCommerce REST API, and `application/ld+json` Schema.org Product feeds) without needing residential proxies or headless browser overhead.
- **Catalog Statistics**: Computes `min_price`, `max_price`, `avg_price`, `median_price`, `discount_rate` (% of discounted items), and `in_stock_ratio` (% of items available).

---

## ⚡ Zero-Proxy Economics & Apify Free Tier

Apify provides **$5.00 of free platform usage every month**.
Because none of these 3 actors rely on expensive residential proxies or memory-heavy browser engines (Puppeteer/Playwright):
- **Memory Footprint**: 256 MB RAM per Actor.
- **Execution Speed**: 1 to 3 seconds per run.
- **Run Cost**: Less than **$0.0003 per run**.
- **Monthly Capacity**: You can run **over 15,000 tasks per month** completely free on Apify!

---

## 🔄 Weekly Self-Maintenance Engine (`brain_updater/`)

The repository includes an autonomous self-updating mechanism:
1. **GitHub Actions Workflow** (`.github/workflows/weekly_pack_updater.yml`):
   - Triggers every Monday at 04:00 UTC (`cron: '0 4 * * 1'`).
   - Runs `python brain_updater/auto_update_pack.py`.
2. **Maintenance Actions**:
   - Updates `signatures.json` with newly launched AI search crawler bots (e.g. DeepSeekBot, MistralBot).
   - Enriches `cleaning_rules.json` with fresh ad and popup CSS selectors.
   - Bumps the semver patch version (`1.0.0` -> `1.0.1`) across all `.actor/actor.json` files.
   - Refreshes the `Last Automated Maintenance: YYYY-MM-DD` date in the 3 Actor `README.md` files.
   - Executes `brain_updater/test_all_actors.py` (verifying Python syntax, JSON schemas, and mathematical calculations).
3. **Apify Rebuild Hook**:
   - Commits and pushes to `main` with `[skip ci]`.
   - Apify automatically detects the push and rebuilds the 3 Actors, permanently displaying the valuable **"Recently Updated" badge** on Apify Store!

---

## 💶 Module Fiscal Micro-Entreprise BNC (`compta_impots/`)

Conçu spécifiquement pour les créateurs d'Actors domiciliés en France sous le régime **Micro-Entreprise (BNC - Prestation de services intellectuelle / Informatique)** recevant des virements SEPA de la part d'**Apify Technologies s.r.o.** (Prague, République Tchèque, TVA : `CZ04970550`).

### 1. Synthèse des Règles Fiscales & Juridiques
- **Territorialité TVA (Art. 259-1 du CGI)** : La prestation de service B2B étant réalisée pour une société établie dans l'Union Européenne (Apify en République Tchèque), la TVA est obligatoirement **autoliquidée par le preneur** en République Tchèque.
- **Règle de Facturation** : Les factures sont émises **Hors Taxes (TVA 0%)** avec la mention obligatoire :
  > *« Autoliquidation de la TVA - Article 283-1 du Code Général des Impôts et Article 196 de la Directive 2006/112/CE »*
- **Déclaration Européenne de Services (DES)** : Obligation légale de télédéclarer chaque mois sur le portail des douanes (`pro.douane.gouv.fr`) le montant des encaissements Apify sous le numéro `CZ04970550`.
- **Franchise en Base de TVA** : Seuil standard à **36 800 €** (seuil majoré à **39 100 €**).
- **Plafond Micro-BNC** : Chiffre d'affaires annuel HT plafonné à **77 700 €**.
- **Cotisations URSSAF** : Taux global BNC de **21.3%** (21.1% cotisations sociales + 0.2% Contribution Formation Professionnelle). En cas d'ACRE la 1ère année : **10.85%**.

### 2. Cases pour la Déclaration d'Impôt 2042-C-PRO
- **Sans Versement Libératoire (Case 5HQ)** :
  - Déclarer le total brut du Chiffre d'Affaires HT encaissé.
  - L'administration fiscale applique automatiquement un **abattement forfaitaire de 34%**.
  - Le revenu net imposable soumis au barème progressif est donc égal à **66% du CA**.
- **Avec Versement Libératoire (Case 5TE)** :
  - Si vous avez exercé l'option du versement libératoire de l'IR (taux de 2.2% payé à l'URSSAF), reporter le CA brut dans la case **5TE**.

### 3. Commandes de Gestion Comptable
```bash
# Afficher le bilan fiscal instantané en console
python brain_updater/compta_manager.py --summary

# Régénérer le tableau de bord HTML interactif
python brain_updater/compta_manager.py --export-dashboard

# Ouvrir le tableau de bord dans le navigateur
# Double-cliquez sur compta_impots/tableau_de_bord_fiscal.html
```

---

## 🚀 Déploiement sur Apify Store en 3 Étapes

1. **Créer les 3 Actors sur Apify Console** :
   - Allez sur [Apify Console > Actors > Create new](https://console.apify.com/actors/new).
   - Choisissez l'option **Link Git repository**.
2. **Lier le dépôt Git** :
   - Renseignez l'URL de votre dépôt GitHub.
   - Définissez le sous-dossier correspondant (ex : `actors/1-eu-b2b-compliance-auditor`).
3. **Publication sur l'Apify Store** :
   - Dans l'onglet **Publication**, activez la visibilité **Public**.
   - Choisissez votre modèle de monétisation (Pay per result, Flat monthly subscription, ou Rental).

---

*Architected & Maintained by Apify B2B Autopilot Monorepo Engine.*
