---
name: ecommerce-json-intelligence
description: Proxy-free e-commerce catalog, price, and stock intelligence scraper for AI agents. Extracts products, variants, SKUs, inventory availability, and pricing metrics from Shopify (/products.json), WooCommerce REST APIs, and Schema.org JSON-LD product feeds. Calculates catalog statistics (min, max, avg price, discount rate, and in-stock ratio).
version: 1.0.0
author: Cedric Jover
tags:
  - ecommerce
  - shopify
  - woocommerce
  - pricing-intelligence
  - stock-monitor
  - retail-analytics
---

# E-Commerce JSON Intelligence Skill

An autonomous AI agent skill for extracting full product catalogs, live inventory availability, and pricing intelligence from modern online storefronts without paid proxies.

## When to Use This Skill
Activate this skill whenever the user or agent needs to:
- Scrape product catalogs, variants, and prices from Shopify or WooCommerce stores.
- Monitor competitor pricing, discounts, and markdown rates.
- Track inventory levels and in-stock / out-of-stock ratios.
- Extract structured product feeds from Schema.org `Product` JSON-LD markup.
- Calculate catalog metrics (`min_price`, `max_price`, `avg_price`, `median_price`, `discount_rate`).

## Capabilities & Architecture
- **Zero Paid Proxies**: Directly probes public JSON endpoints (`/products.json?limit=250`, `/wp-json/wc/store/v1/products`) and JSON-LD markup.
- **Variant Breakdown**: Extracts granular pricing, individual SKUs, variant titles, and availability.
- **Statistical Aggregation**: Instantly computes pricing distributions and inventory health.
