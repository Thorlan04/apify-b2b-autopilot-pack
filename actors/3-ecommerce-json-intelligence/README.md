# 🛍️ E-Commerce JSON Intelligence (Shopify, WooCommerce & Schema.org Scraper)

> **The 100% proxy-free e-commerce product, inventory, and pricing intelligence Actor.**  
> Effortlessly extract thousands of products, variants, SKUs, inventory availability, and pricing metrics from online storefronts via public JSON APIs (`/products.json`, WooCommerce REST) and `application/ld+json` Schema.org product feeds.

---

## 🚀 Key Advantages

1. **Zero Proxy Costs**: Why pay for residential proxies and heavy headless browsers when modern e-commerce platforms expose high-speed public JSON feeds? This Actor accesses clean, structured JSON directly!
2. **Deep Pricing & Discount Intelligence**: Automatically calculates:
   - `min_price`, `max_price`, `avg_price`, and `median_price`
   - `discount_rate`: Percentage of items on sale with marked-down pricing
   - `in_stock_ratio`: Real-time inventory availability percentage
3. **Multi-Platform Support**: Auto-detects Shopify, WooCommerce, and modern headless storefronts featuring Schema.org JSON-LD markup.
4. **Comprehensive Variant Breakdown**: Extracts individual variant titles, prices, SKUs, and stock states.
5. **Automation-Ready**: Perfect for Make.com, n8n, Zapier, Airtable, and Google Sheets price monitoring alerts.

---

## ⚙️ Input Configuration

```json
{
  "stores": [
    "allbirds.com",
    "gymshark.com"
  ],
  "max_products_per_store": 100,
  "extract_variants": true,
  "timeout_seconds": 15
}
```

### Input Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `stores` | Array of Strings | `["allbirds.com", "gymshark.com"]` | Domains or URLs of e-commerce stores |
| `max_products_per_store` | Integer | `100` | Maximum products to collect per store |
| `extract_variants` | Boolean | `true` | Include granular variant pricing, SKUs, and stock |
| `timeout_seconds` | Integer | `15` | Request timeout per endpoint probe |

---

## 📊 Sample Output Dataset

```json
{
  "store_domain": "https://allbirds.com",
  "platform_detected": "Shopify",
  "currency": "USD",
  "total_products_extracted": 100,
  "catalog_stats": {
    "min_price": 28.0,
    "max_price": 160.0,
    "avg_price": 94.5,
    "median_price": 98.0,
    "discount_rate": 18.0,
    "in_stock_ratio": 92.0,
    "discounted_products_count": 18,
    "in_stock_count": 92
  },
  "products": [
    {
      "id": "7182938472",
      "title": "Men's Tree Runners",
      "handle": "mens-tree-runners",
      "url": "https://allbirds.com/products/mens-tree-runners",
      "vendor": "Allbirds",
      "product_type": "Shoes",
      "price": 98.0,
      "compare_at_price": 110.0,
      "is_discounted": true,
      "in_stock": true,
      "sku": "TR-M-01",
      "images": [
        "https://cdn.shopify.com/s/files/1/sample.jpg"
      ],
      "variants_count": 8,
      "variants": [
        {
          "id": 412839218,
          "title": "Size 10 / Mist Grey",
          "sku": "TR-M-01-10",
          "price": 98.0,
          "compare_at_price": 110.0,
          "available": true
        }
      ]
    }
  ],
  "extracted_at": "2026-10-18T10:00:00Z"
}
```

---

## ⚡ Integration Workflows

### 1. Daily Price & Competitor Drop Alert in Make / n8n
1. Schedule daily trigger at 08:00 AM.
2. Run Actor `ecommerce-json-intelligence` with competitor URLs.
3. Filter products where `is_discounted == true` or `catalog_stats.discount_rate > 20`.
4. Send an alert directly to your Slack, Discord, or Microsoft Teams channel with the discounted items and direct links!

### 2. Google Sheets / Airtable Auto-Sync
Use Apify's native Google Sheets integration to append catalog metrics (`avg_price`, `in_stock_ratio`, `total_products_extracted`) daily into a historical price tracking chart.

### 3. Direct cURL
```bash
curl -X POST "https://api.apify.com/v2/acts/your-username~ecommerce-json-intelligence/run-sync-get-dataset-items?token=YOUR_APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"stores": ["gymshark.com"], "max_products_per_store": 50}'
```

---

## 💰 Resource & Pricing Economics
- **Memory Consumption**: 256 MB RAM
- **Average Duration**: ~1.5 seconds per store
- **Cost**: < $0.00025 per audit
- Extracts hundreds of store catalogs every month without spending a single cent on Apify's $5 free tier.

---

*Last Automated Maintenance: 2026-10-19*
