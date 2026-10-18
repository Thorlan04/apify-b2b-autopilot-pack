---
name: ai-rag-markdown-extractor
description: Universal web to pristine Markdown converter and semantic RAG chunker for AI agents (Cursor, Claude Code, Copilot, LangChain, LlamaIndex). Strips ads, navigation, banners, and cookie popups. Converts HTML tables, code blocks, and absolute hyperlinks. Segments text into semantic RAG chunks with token estimates and generates compliant /llms.txt specification drafts.
version: 1.0.0
author: Cedric Jover
tags:
  - rag
  - markdown
  - web-scraper
  - llmstxt
  - embeddings
  - vector-search
---

# AI RAG Clean Markdown Extractor & llms.txt Generator Skill

An autonomous AI agent skill for converting noisy web pages, sitemaps, and online documentation into purified, LLM-ready Markdown and semantic RAG chunks.

## When to Use This Skill
Activate this skill whenever the user or agent needs to:
- Convert web documentation, articles, or complex URLs into pristine GitHub-Flavored Markdown.
- Eliminate HTML clutter (sidebars, menus, cookie banners, tracking scripts, popups).
- Extract data tables and convert them cleanly into Markdown tables (`| Col1 | Col2 |`).
- Prepare text chunks for Vector Databases (Pinecone, ChromaDB, Qdrant, Supabase Vector) with token estimates and paragraph boundary preservation.
- Generate a standardized `/llms.txt` file for indexing by Claude, OpenAI, and Perplexity.

## Capabilities & Architecture
- **DOM Cleaning**: Decomposes unwanted tags and CSS noise classes.
- **Table & Link Integrity**: Preserves table structures and resolves relative hyperlinks into absolute URLs.
- **RAG Chunking**: Splits text according to target character/token budgets with contextual headings.
- **Zero Proxies**: Runs on direct high-speed HTTP requests without paid proxies.
