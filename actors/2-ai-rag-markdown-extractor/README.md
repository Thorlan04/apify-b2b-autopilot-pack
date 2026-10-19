# 🧠 AI RAG Clean Markdown Extractor & llms.txt Generator

> **The ultimate web-to-Markdown scraper for AI engineers, LangChain, LlamaIndex, Pinecone, and RAG pipelines.**  
> Strips banners, navigation, modals, and cookie tracking. Generates pristine GitHub-flavored Markdown with tables, lists, semantic RAG chunks with token estimates, and creates a standardized `/llms.txt` file ready for Claude, OpenAI, and Perplexity.

---

## 🌟 Why AI Builders Choose This Actor

1. **Pure Signal, Zero Noise**: Discards header chrome, sidebars, cookie banners, tracking scripts, and advertisements to preserve context window tokens.
2. **First-Class Semantic RAG Chunking**: Returns pre-calculated text chunks configured to your exact character/token budget with intelligent boundary preservation (paragraphs, headers) and vector indexing metadata.
3. **Automatic `llms.txt` Generator**: Synthesizes a standardized, ready-to-deploy `/llms.txt` draft compliant with modern LLM indexing specifications.
4. **Proxy-Free Speed & Efficiency**: Consumes minimal CPU and memory. Converts hundreds of documentation pages in seconds.
5. **Table & Code Integrity**: Preserves Markdown tables (`| Col1 | Col2 |`) and syntax-highlighted code blocks without mangling.

---

## ⚙️ Input Schema

```json
{
  "start_urls": [
    "https://docs.python.org/3/tutorial/index.html",
    "https://news.ycombinator.com"
  ],
  "chunk_size": 1600,
  "chunk_overlap": 200,
  "max_pages": 10,
  "generate_llms_txt": true
}
```

### Input Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_urls` | Array of Strings | `["https://docs.python.org/..."]` | Web URLs or sitemap.xml links |
| `chunk_size` | Integer | `1600` | Target characters per RAG chunk (~400 tokens) |
| `chunk_overlap` | Integer | `200` | Character overlap between consecutive chunks |
| `max_pages` | Integer | `10` | Maximum pages to parse |
| `generate_llms_txt` | Boolean | `true` | Generate ready-to-deploy llms.txt file |

---

## 📦 Output Dataset Format

```json
{
  "url": "https://docs.python.org/3/tutorial/index.html",
  "title": "The Python Tutorial — Python 3 documentation",
  "markdown_content": "# The Python Tutorial\n\nPython is an easy to learn, powerful programming language...",
  "word_count": 842,
  "token_estimate": 1050,
  "rag_chunks": [
    {
      "chunk_index": 1,
      "total_chunks": 3,
      "heading_context": "The Python Tutorial",
      "char_count": 1540,
      "token_estimate": 385,
      "text": "# The Python Tutorial\n\nPython is an easy to learn...",
      "source_url": "https://docs.python.org/3/tutorial/index.html"
    }
  ],
  "llms_txt_draft": "# Python Documentation\n\n> Comprehensive AI documentation index...",
  "extracted_at": "2026-10-18T10:00:00Z"
}
```

---

## 🛠️ LangChain / LlamaIndex / Python Integration

```python
import os
import requests

APIFY_TOKEN = os.getenv("APIFY_TOKEN")
ACTOR_URL = f"https://api.apify.com/v2/acts/your-username~ai-rag-markdown-extractor/run-sync-get-dataset-items?token={APIFY_TOKEN}"

payload = {
    "start_urls": ["https://fastapi.tiangolo.com/tutorial/"],
    "chunk_size": 1500,
    "chunk_overlap": 150
}

response = requests.post(ACTOR_URL, json=payload)
dataset = response.json()

# Feed directly into your vector store (Pinecone, ChromaDB, Qdrant)
documents = []
for item in dataset:
    for chunk in item["rag_chunks"]:
        documents.append({
            "page_content": chunk["text"],
            "metadata": {
                "source": chunk["source_url"],
                "heading": chunk["heading_context"],
                "tokens": chunk["token_estimate"]
            }
        })

print(f"Loaded {len(documents)} high-quality vector chunks ready for embedding!")
```

---

## ⚡ Make.com & n8n Workflows

Connect this Actor directly before your OpenAI / Anthropic or Supabase Vector store node in n8n or Make:
1. Trigger webhook with website URL.
2. Run Actor `ai-rag-markdown-extractor`.
3. Iterate over `rag_chunks` array and push embeddings to Vector DB.

---

## 💰 Resource & Pricing Footprint
- **Memory**: 256 MB RAM
- **Run Duration**: ~1 second per page
- **Cost**: < $0.0002 per web page
- Run **up to 20,000 pages per month** within the Apify $5 free tier.

---

*Last Automated Maintenance: 2026-10-19*
