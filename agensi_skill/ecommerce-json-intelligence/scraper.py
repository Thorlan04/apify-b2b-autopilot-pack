"""E-Commerce JSON Intelligence Actor.

100% Proxy-free e-commerce catalog, price, and inventory extractor.
Detects public JSON endpoints (Shopify, WooCommerce, custom REST) and
JSON-LD Schema.org product feeds, extracting structured products and
computing deep pricing & stock availability statistics.
"""

import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import statistics
from typing import Any, Dict, List, Optional, Tuple
import urllib.parse

from apify import Actor
from bs4 import BeautifulSoup
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/128.0.0.0 Safari/537.36 ApifyEcommerceIntel/1.0"
)

PATTERNS_FILE = Path(__file__).resolve().parent.parent / "ecommerce_patterns.json"


def load_patterns() -> Dict[str, Any]:
    """Load endpoint heuristics and Schema.org patterns."""
    if PATTERNS_FILE.exists():
        try:
            with open(PATTERNS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            Actor.log.warning(f"Could not load ecommerce_patterns.json: {e}")
    return {
        "shopify": {"endpoints": ["/products.json?limit=250"]},
        "woocommerce": {"endpoints": ["/wp-json/wc/store/v1/products?per_page=100"]},
        "schema_org": {"product_types": ["Product"]},
    }


def clean_store_domain(raw_store: str) -> str:
    """Normalize input into https://domain.com format."""
    store = raw_store.strip()
    if not store.startswith("http://") and not store.startswith("https://"):
        store = f"https://{store}"
    parsed = urllib.parse.urlparse(store)
    return f"{parsed.scheme}://{parsed.netloc}"


def fetch_json_endpoint(url: str, timeout: int = 15) -> Optional[Any]:
    """Query a potential public JSON endpoint with browser headers."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True, verify=False)
        if resp.status_code == 200:
            content_type = resp.headers.get("content-type", "")
            if "json" in content_type or resp.text.strip().startswith(("{", "[")):
                return resp.json()
    except Exception:
        pass
    return None


def fetch_html(url: str, timeout: int = 15) -> Optional[str]:
    """Fetch raw HTML for JSON-LD parsing."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True, verify=False)
        if resp.status_code == 200:
            return resp.text
    except Exception:
        pass
    return None


def extract_shopify_products(data: Any, base_url: str, max_products: int, extract_variants: bool) -> List[Dict[str, Any]]:
    """Parse products from Shopify /products.json response."""
    raw_products = data.get("products", []) if isinstance(data, dict) else []
    extracted = []

    for item in raw_products[:max_products]:
        variants = item.get("variants", [])
        primary_var = variants[0] if variants else {}

        # Prices
        price_str = primary_var.get("price", "0")
        compare_str = primary_var.get("compare_at_price")
        try:
            price = float(price_str)
        except (ValueError, TypeError):
            price = 0.0

        try:
            compare_price = float(compare_str) if compare_str else None
        except (ValueError, TypeError):
            compare_price = None

        is_discounted = compare_price is not None and compare_price > price
        in_stock = bool(primary_var.get("available", True))

        # Images
        images_raw = item.get("images", [])
        images = [img.get("src") for img in images_raw if img.get("src")]

        # Handle variants
        var_list = []
        if extract_variants and variants:
            for v in variants:
                try:
                    v_price = float(v.get("price", price))
                except (ValueError, TypeError):
                    v_price = price
                try:
                    v_comp = float(v.get("compare_at_price")) if v.get("compare_at_price") else None
                except (ValueError, TypeError):
                    v_comp = None

                var_list.append({
                    "id": v.get("id"),
                    "title": v.get("title"),
                    "sku": v.get("sku"),
                    "price": v_price,
                    "compare_at_price": v_comp,
                    "available": bool(v.get("available", True)),
                })

        handle = item.get("handle", "")
        product_url = f"{base_url}/products/{handle}" if handle else base_url

        extracted.append({
            "id": str(item.get("id")),
            "title": item.get("title"),
            "handle": handle,
            "url": product_url,
            "vendor": item.get("vendor", ""),
            "product_type": item.get("product_type", ""),
            "created_at": item.get("created_at"),
            "price": price,
            "compare_at_price": compare_price,
            "is_discounted": is_discounted,
            "in_stock": in_stock,
            "sku": primary_var.get("sku", ""),
            "images": images,
            "variants_count": len(variants),
            "variants": var_list,
        })

    return extracted


def extract_woocommerce_products(data: Any, base_url: str, max_products: int) -> List[Dict[str, Any]]:
    """Parse products from WooCommerce REST API response."""
    items = data if isinstance(data, list) else data.get("products", [])
    extracted = []

    for item in items[:max_products]:
        # Price extraction (WooCommerce Store API prices are in minor units / cents)
        prices_obj = item.get("prices", {})
        price_val = 0.0
        regular_val = None

        if prices_obj:
            try:
                raw_price = int(prices_obj.get("price", 0))
                dec = int(prices_obj.get("currency_minor_unit", 2))
                price_val = raw_price / (10 ** dec)
                if prices_obj.get("regular_price"):
                    regular_val = int(prices_obj.get("regular_price")) / (10 ** dec)
            except Exception:
                price_val = float(item.get("price", 0) or 0)
        else:
            try:
                price_val = float(item.get("price", 0) or 0)
                if item.get("regular_price"):
                    regular_val = float(item.get("regular_price"))
            except Exception:
                price_val = 0.0

        is_discounted = regular_val is not None and regular_val > price_val
        in_stock = bool(item.get("is_in_stock", True) if "is_in_stock" in item else item.get("in_stock", True))

        # Images
        images_raw = item.get("images", [])
        images = [img.get("src") for img in images_raw if isinstance(img, dict) and img.get("src")]

        extracted.append({
            "id": str(item.get("id")),
            "title": item.get("name") or item.get("title"),
            "handle": item.get("slug", ""),
            "url": item.get("permalink") or f"{base_url}/product/{item.get('slug', '')}",
            "vendor": "",
            "product_type": item.get("type", "simple"),
            "price": price_val,
            "compare_at_price": regular_val,
            "is_discounted": is_discounted,
            "in_stock": in_stock,
            "sku": item.get("sku", ""),
            "images": images,
            "variants_count": len(item.get("variations", [])),
            "variants": [],
        })

    return extracted


def extract_schema_org_products(html_content: str, base_url: str, max_products: int) -> List[Dict[str, Any]]:
    """Parse products from JSON-LD Schema.org markup."""
    soup = BeautifulSoup(html_content, "html.parser")
    scripts = soup.find_all("script", attrs={"type": "application/ld+json"})
    extracted = []

    for s in scripts:
        try:
            content = json.loads(s.get_text())
        except Exception:
            continue

        items_to_check = []
        if isinstance(content, list):
            items_to_check.extend(content)
        elif isinstance(content, dict):
            if "@graph" in content:
                items_to_check.extend(content["@graph"])
            else:
                items_to_check.append(content)

        for item in items_to_check:
            if not isinstance(item, dict):
                continue
            item_type = item.get("@type", "")
            if item_type in ["Product", "IndividualProduct", "ProductModel"]:
                offers = item.get("offers", {})
                if isinstance(offers, list) and offers:
                    offers = offers[0]

                price_val = 0.0
                currency = "USD"
                availability = True
                if isinstance(offers, dict):
                    try:
                        price_val = float(offers.get("price", 0) or 0)
                    except Exception:
                        price_val = 0.0
                    currency = offers.get("priceCurrency", currency)
                    avail_str = offers.get("availability", "")
                    if "OutOfStock" in avail_str:
                        availability = False

                images = item.get("image", [])
                if isinstance(images, str):
                    images = [images]

                item_url = item.get("url") or base_url

                extracted.append({
                    "id": str(item.get("sku") or item.get("gtin13") or item.get("name")),
                    "title": item.get("name"),
                    "handle": "",
                    "url": urllib.parse.urljoin(base_url, item_url),
                    "vendor": item.get("brand", {}).get("name", "") if isinstance(item.get("brand"), dict) else str(item.get("brand", "")),
                    "product_type": item.get("category", ""),
                    "price": price_val,
                    "compare_at_price": None,
                    "is_discounted": False,
                    "in_stock": availability,
                    "sku": item.get("sku", ""),
                    "images": images,
                    "variants_count": 1,
                    "variants": [],
                })

                if len(extracted) >= max_products:
                    return extracted

    return extracted


def compute_catalog_stats(products: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate statistical metrics for catalog pricing, discounts, and inventory."""
    if not products:
        return {
            "min_price": 0.0,
            "max_price": 0.0,
            "avg_price": 0.0,
            "median_price": 0.0,
            "discount_rate": 0.0,
            "in_stock_ratio": 0.0,
            "discounted_products_count": 0,
            "in_stock_count": 0,
        }

    prices = [p["price"] for p in products if p.get("price") is not None and p["price"] > 0]
    discounted = [p for p in products if p.get("is_discounted")]
    in_stock = [p for p in products if p.get("in_stock")]

    min_p = round(min(prices), 2) if prices else 0.0
    max_p = round(max(prices), 2) if prices else 0.0
    avg_p = round(statistics.mean(prices), 2) if prices else 0.0
    med_p = round(statistics.median(prices), 2) if prices else 0.0

    discount_rate = round((len(discounted) / len(products)) * 100, 1)
    in_stock_ratio = round((len(in_stock) / len(products)) * 100, 1)

    return {
        "min_price": min_p,
        "max_price": max_p,
        "avg_price": avg_p,
        "median_price": med_p,
        "discount_rate": discount_rate,
        "in_stock_ratio": in_stock_ratio,
        "discounted_products_count": len(discounted),
        "in_stock_count": len(in_stock),
    }


async def main() -> None:
    """Apify Actor lifecycle entrypoint."""
    async with Actor:
        actor_input = await Actor.get_input() or {}
        stores = actor_input.get("stores", ["allbirds.com", "gymshark.com"])
        max_products = actor_input.get("max_products_per_store", 100)
        extract_variants = actor_input.get("extract_variants", True)
        timeout = actor_input.get("timeout_seconds", 15)

        if isinstance(stores, str):
            stores = [s.strip() for s in stores.split(",") if s.strip()]

        Actor.log.info(f"Starting E-Commerce JSON Intelligence for {len(stores)} store(s)...")
        patterns = load_patterns()

        for store in stores:
            base_url = clean_store_domain(store)
            Actor.log.info(f"Probing e-commerce catalog for: {base_url}")

            products: List[Dict[str, Any]] = []
            platform = "Custom / Unknown"
            currency = "USD"

            # 1. Probe Shopify Public Endpoints
            for endpoint in patterns.get("shopify", {}).get("endpoints", []):
                probe_url = f"{base_url}{endpoint}"
                data = fetch_json_endpoint(probe_url, timeout=timeout)
                if data and isinstance(data, dict) and "products" in data:
                    platform = "Shopify"
                    products = extract_shopify_products(
                        data=data,
                        base_url=base_url,
                        max_products=max_products,
                        extract_variants=extract_variants,
                    )
                    break

            # 2. Probe WooCommerce REST Endpoints if not found
            if not products:
                for endpoint in patterns.get("woocommerce", {}).get("endpoints", []):
                    probe_url = f"{base_url}{endpoint}"
                    data = fetch_json_endpoint(probe_url, timeout=timeout)
                    if data and (isinstance(data, list) or "products" in data):
                        platform = "WooCommerce"
                        products = extract_woocommerce_products(
                            data=data,
                            base_url=base_url,
                            max_products=max_products,
                        )
                        break

            # 3. Fallback: Parse JSON-LD Schema.org Product markup
            if not products:
                html_raw = fetch_html(base_url, timeout=timeout)
                if html_raw:
                    products = extract_schema_org_products(
                        html_content=html_raw,
                        base_url=base_url,
                        max_products=max_products,
                    )
                    if products:
                        platform = "Schema.org / JSON-LD"

            # Compute catalog intelligence statistics
            stats = compute_catalog_stats(products)

            record = {
                "store_domain": base_url,
                "platform_detected": platform,
                "currency": currency,
                "total_products_extracted": len(products),
                "catalog_stats": stats,
                "products": products,
                "extracted_at": datetime.now(timezone.utc).isoformat(),
            }

            await Actor.push_data(record)
            Actor.log.info(
                f"Successfully processed {base_url} ({platform}): {len(products)} products, "
                f"avg price: {stats['avg_price']}, in-stock: {stats['in_stock_ratio']}%"
            )

        Actor.log.info("E-Commerce Intelligence run completed.")


if __name__ == "__main__":
    asyncio.run(main())
