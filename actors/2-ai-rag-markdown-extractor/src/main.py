"""AI RAG Clean Markdown Extractor Actor.

Converts web pages and documentation into pure, noise-free Markdown,
computes semantic RAG chunks with token estimates for vector databases,
and automatically generates standardized llms.txt specifications.
"""

import asyncio
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple
import urllib.parse
import xml.etree.ElementTree as ET

from apify import Actor
from bs4 import BeautifulSoup, NavigableString, Tag
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/128.0.0.0 Safari/537.36 ApifyRAGMarkdown/1.0"
)

RULES_FILE = Path(__file__).resolve().parent.parent / "cleaning_rules.json"


def load_cleaning_rules() -> Dict[str, Any]:
    """Load DOM stripping rules and chunking parameters."""
    if RULES_FILE.exists():
        try:
            with open(RULES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            Actor.log.warning(f"Could not load cleaning_rules.json: {e}")
    return {
        "strip_tags": ["script", "style", "noscript", "iframe", "svg"],
        "noise_selectors": ["header", "footer", "nav", "aside", ".cookie-banner"],
        "chunking": {"default_chunk_chars": 1600, "default_overlap_chars": 200, "chars_per_token": 4.0},
    }


def fetch_web_page(url: str, timeout: int = 15) -> Optional[Tuple[str, str]]:
    """Fetch web page and return final URL and HTML content."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True, verify=False)
        if resp.status_code == 200:
            return resp.url, resp.text
    except Exception as e:
        Actor.log.warning(f"Failed to fetch {url}: {e}")
    return None


def extract_urls_from_sitemap(sitemap_xml: str, max_urls: int = 50) -> List[str]:
    """Parse XML sitemap and extract page URLs."""
    urls = []
    try:
        root = ET.fromstring(sitemap_xml)
        # Handle standard sitemap namespaces
        for elem in root.iter():
            if elem.tag.endswith("loc") and elem.text:
                loc = elem.text.strip()
                if loc.startswith("http") and not loc.endswith(".xml"):
                    urls.append(loc)
                if len(urls) >= max_urls:
                    break
    except Exception as e:
        Actor.log.warning(f"Error parsing sitemap XML: {e}")
    return urls


def clean_html_soup(soup: BeautifulSoup, rules: Dict[str, Any]) -> BeautifulSoup:
    """Strip scripts, styles, navigational chrome, ads, and cookie banners."""
    # 1. Decompose unwanted tags
    for tag_name in rules.get("strip_tags", []):
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # 2. Decompose noise classes, IDs and semantic elements
    for selector in rules.get("noise_selectors", []):
        try:
            for match in soup.select(selector):
                match.decompose()
        except Exception:
            pass

    return soup


def convert_table_to_markdown(table: Tag) -> str:
    """Convert HTML <table> into GitHub-Flavored Markdown table."""
    rows = table.find_all("tr")
    if not rows:
        return ""

    md_rows = []
    header_col_count = 0

    for r_idx, row in enumerate(rows):
        cells = row.find_all(["th", "td"])
        if not cells:
            continue

        clean_cells = [re.sub(r"\s+", " ", cell.get_text(strip=True)).replace("|", "\\|") for cell in cells]
        if r_idx == 0:
            header_col_count = len(clean_cells)
            md_rows.append("| " + " | ".join(clean_cells) + " |")
            md_rows.append("| " + " | ".join(["---"] * header_col_count) + " |")
        else:
            # Pad or truncate row to header column count
            if len(clean_cells) < header_col_count:
                clean_cells += [""] * (header_col_count - len(clean_cells))
            elif len(clean_cells) > header_col_count and header_col_count > 0:
                clean_cells = clean_cells[:header_col_count]
            md_rows.append("| " + " | ".join(clean_cells) + " |")

    return "\n" + "\n".join(md_rows) + "\n\n" if md_rows else ""


def html_to_markdown(soup: BeautifulSoup, base_url: str) -> str:
    """Convert clean HTML body into structured, readable Markdown."""
    # Select best content root
    root = soup.find("main") or soup.find("article") or soup.find("div", class_=re.compile(r"content|post|article", re.I)) or soup.body or soup

    output_lines = []

    def process_node(node: Any, heading_prefix: str = "") -> str:
        if isinstance(node, NavigableString):
            text = str(node)
            return text

        if not isinstance(node, Tag):
            return ""

        tag_name = node.name.lower()

        # Headings
        if tag_name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            level = int(tag_name[1])
            heading_text = node.get_text(strip=True)
            if heading_text:
                return f"\n\n{'#' * level} {heading_text}\n\n"
            return ""

        # Paragraphs & Divs
        if tag_name in ["p", "div", "section"]:
            inner = "".join(process_node(child) for child in node.children).strip()
            return f"\n\n{inner}\n\n" if inner else ""

        # Hyperlinks (resolved to absolute)
        if tag_name == "a":
            href = node.get("href", "")
            text = node.get_text(strip=True)
            if href and text:
                abs_url = urllib.parse.urljoin(base_url, href)
                return f" [{text}]({abs_url}) "
            return text or ""

        # Code & Preformatted
        if tag_name == "pre":
            code_text = node.get_text()
            return f"\n\n```\n{code_text.strip()}\n```\n\n"
        if tag_name == "code":
            return f"`{node.get_text()}`"

        # Blockquote
        if tag_name == "blockquote":
            inner = node.get_text(strip=True)
            lines = [f"> {line.strip()}" for line in inner.split("\n") if line.strip()]
            return "\n\n" + "\n".join(lines) + "\n\n"

        # Tables
        if tag_name == "table":
            return convert_table_to_markdown(node)

        # Lists
        if tag_name in ["ul", "ol"]:
            items = []
            is_ordered = tag_name == "ol"
            idx = 1
            for child in node.children:
                if isinstance(child, Tag) and child.name == "li":
                    item_text = "".join(process_node(c) for c in child.children).strip()
                    if item_text:
                        prefix = f"{idx}. " if is_ordered else "- "
                        items.append(f"{prefix}{item_text}")
                        idx += 1
            return "\n" + "\n".join(items) + "\n\n" if items else ""

        # Strong / Emphasis
        if tag_name in ["strong", "b"]:
            t = node.get_text(strip=True)
            return f"**{t}**" if t else ""
        if tag_name in ["em", "i"]:
            t = node.get_text(strip=True)
            return f"*{t}*" if t else ""

        # Fallback recursion for container tags
        return "".join(process_node(child) for child in node.children)

    raw_markdown = process_node(root)

    # Clean whitespace and multiple blank lines
    raw_markdown = re.sub(r"\n{3,}", "\n\n", raw_markdown)
    raw_markdown = re.sub(r"[ \t]+", " ", raw_markdown)
    return raw_markdown.strip()


def estimate_tokens(text: str) -> int:
    """Heuristic estimate of tokens for LLMs (chars / 4 and word count composite)."""
    if not text:
        return 0
    words = len(text.split())
    chars = len(text)
    # Average of character ratio and 1.3 tokens per word
    return max(1, int((chars / 4.0 + words * 1.3) / 2))


def generate_rag_chunks(
    markdown_text: str,
    source_url: str,
    chunk_size: int = 1600,
    chunk_overlap: int = 200,
) -> List[Dict[str, Any]]:
    """Segment Markdown text into contextual semantic chunks for vector storage."""
    paragraphs = [p.strip() for p in markdown_text.split("\n\n") if p.strip()]
    chunks = []
    current_chunk = []
    current_length = 0
    current_heading = "General"

    for p in paragraphs:
        # Detect active heading context
        if p.startswith("#"):
            current_heading = p.lstrip("#").strip()

        p_len = len(p)
        if current_length + p_len > chunk_size and current_chunk:
            chunk_body = "\n\n".join(current_chunk)
            chunks.append({
                "text": chunk_body,
                "heading_context": current_heading,
                "char_count": len(chunk_body),
                "token_estimate": estimate_tokens(chunk_body),
            })

            # Overlap handling: retain the last paragraph if small enough
            if chunk_overlap > 0 and len(current_chunk[-1]) <= chunk_overlap:
                current_chunk = [current_chunk[-1], p]
                current_length = len(current_chunk[0]) + p_len
            else:
                current_chunk = [p]
                current_length = p_len
        else:
            current_chunk.append(p)
            current_length += p_len + 2

    if current_chunk:
        chunk_body = "\n\n".join(current_chunk)
        chunks.append({
            "text": chunk_body,
            "heading_context": current_heading,
            "char_count": len(chunk_body),
            "token_estimate": estimate_tokens(chunk_body),
        })

    # Enrich chunks with index metadata
    total_chunks = len(chunks)
    for idx, c in enumerate(chunks):
        c["chunk_index"] = idx + 1
        c["total_chunks"] = total_chunks
        c["source_url"] = source_url

    return chunks


def build_llms_txt_draft(
    domain: str,
    title: str,
    summary: str,
    page_records: List[Dict[str, Any]],
) -> str:
    """Synthesize standardized /llms.txt file specification draft."""
    clean_domain = re.sub(r"^https?://", "", domain).split("/")[0]

    lines = [
        f"# {title or clean_domain}",
        "",
        f"> {summary or f'Comprehensive AI documentation and resource index for {clean_domain}.'}",
        "",
        "## Key Documentation & API Endpoints",
        "",
    ]

    for rec in page_records[:15]:
        p_title = rec.get("title") or "Documentation Page"
        p_url = rec.get("url") or f"https://{clean_domain}"
        lines.append(f"- [{p_title}]({p_url}): Purified documentation section ({rec.get('token_estimate', 0)} tokens)")

    lines.extend([
        "",
        "## LLM Usage & Context Rules",
        "- Format responses using concise Markdown with code blocks where applicable.",
        "- Reference official URLs provided in the index above when citing features.",
        "- Prioritize up-to-date syntax and secure integration patterns.",
    ])

    return "\n".join(lines)


async def main() -> None:
    """Apify Actor lifecycle entrypoint."""
    async with Actor:
        actor_input = await Actor.get_input() or {}
        start_urls = actor_input.get("start_urls", [
            "https://docs.python.org/3/tutorial/index.html",
            "https://news.ycombinator.com",
        ])
        chunk_size = actor_input.get("chunk_size", 1600)
        chunk_overlap = actor_input.get("chunk_overlap", 200)
        max_pages = actor_input.get("max_pages", 10)
        gen_llms_txt = actor_input.get("generate_llms_txt", True)

        if isinstance(start_urls, str):
            start_urls = [u.strip() for u in start_urls.split(",") if u.strip()]

        Actor.log.info(f"Starting AI RAG Markdown Extractor with {len(start_urls)} source(s)...")
        rules = load_cleaning_rules()

        # Expand sitemaps if any
        resolved_urls = []
        for url in start_urls:
            if url.endswith(".xml") or "sitemap" in url.lower():
                Actor.log.info(f"Fetching sitemap XML from: {url}")
                res = fetch_web_page(url)
                if res:
                    s_urls = extract_urls_from_sitemap(res[1], max_urls=max_pages)
                    resolved_urls.extend(s_urls)
            else:
                resolved_urls.append(url)

        target_urls = resolved_urls[:max_pages]
        Actor.log.info(f"Processing {len(target_urls)} page(s) to Markdown...")

        extracted_records = []
        for url in target_urls:
            Actor.log.info(f"Extracting & cleaning: {url}")
            fetch_result = fetch_web_page(url)
            if not fetch_result:
                continue

            final_url, html_raw = fetch_result
            soup = BeautifulSoup(html_raw, "html.parser")

            # Extract Title
            title_tag = soup.find("title")
            title = title_tag.get_text(strip=True) if title_tag else url

            # Clean and convert
            clean_soup = clean_html_soup(soup, rules)
            markdown_content = html_to_markdown(clean_soup, base_url=final_url)

            # RAG Chunks
            chunks = generate_rag_chunks(
                markdown_text=markdown_content,
                source_url=final_url,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )

            word_count = len(markdown_content.split())
            token_estimate = estimate_tokens(markdown_content)

            record = {
                "url": final_url,
                "title": title,
                "markdown_content": markdown_content,
                "word_count": word_count,
                "token_estimate": token_estimate,
                "rag_chunks": chunks,
                "extracted_at": datetime.now(timezone.utc).isoformat(),
            }
            extracted_records.append(record)

        # Generate llms.txt draft if enabled
        domain_sample = target_urls[0] if target_urls else "example.com"
        llms_txt_draft = ""
        if gen_llms_txt and extracted_records:
            llms_txt_draft = build_llms_txt_draft(
                domain=domain_sample,
                title=extracted_records[0].get("title", ""),
                summary=f"Curated AI index generated for {domain_sample}",
                page_records=extracted_records,
            )

        # Push to Apify Dataset
        for r in extracted_records:
            r["llms_txt_draft"] = llms_txt_draft
            await Actor.push_data(r)

        Actor.log.info(f"Completed! Pushed {len(extracted_records)} clean Markdown dataset item(s).")


if __name__ == "__main__":
    asyncio.run(main())
