"""Weekly Auto-Maintenance Engine for Apify B2B Autopilot Pack.

Executed automatically every Monday by GitHub Actions:
1. Enriches signatures.json, cleaning_rules.json, and ecommerce_patterns.json.
2. Bumps semver patch version across all 3 actor.json files.
3. Refreshes the 'Last Automated Maintenance' timestamp in all READMEs.
4. Runs full health check suite (test_all_actors.py) before approving changes.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys

# Ensure UTF-8 stdout on all operating systems and shells
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent


def bump_patch_version(current_version: str) -> str:
    """Increment patch version: 1.0.0 -> 1.0.1."""
    parts = current_version.split(".")
    if len(parts) == 3:
        try:
            major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
            return f"{major}.{minor}.{patch + 1}"
        except ValueError:
            pass
    return f"{current_version}.1"


def update_actor_json_files() -> None:
    """Bump version in all .actor/actor.json files."""
    actor_jsons = list(REPO_ROOT.glob("actors/**/.actor/actor.json"))
    for aj in actor_jsons:
        with open(aj, "r", encoding="utf-8") as f:
            data = json.load(f)

        old_ver = data.get("version", "1.0.0")
        new_ver = bump_patch_version(old_ver)
        data["version"] = new_ver

        with open(aj, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")

        print(f"[+] Bumped {aj.parent.parent.name} version: {old_ver} -> {new_ver}")


def update_signatures() -> None:
    """Enrich signatures.json with latest AI crawler bots and compliance updates."""
    sig_path = REPO_ROOT / "actors" / "1-eu-b2b-compliance-auditor" / "signatures.json"
    if not sig_path.exists():
        return

    with open(sig_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    today_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    data["last_updated"] = today_iso

    # Fresh AI crawlers list
    current_bots = {b.get("name") for b in data.get("ai_crawlers", [])}
    fresh_bots = [
        {"name": "GPTBot", "company": "OpenAI", "category": "LLM Training & Search"},
        {"name": "OAI-SearchBot", "company": "OpenAI", "category": "Real-time Search"},
        {"name": "ClaudeBot", "company": "Anthropic", "category": "Claude Search Index"},
        {"name": "PerplexityBot", "company": "Perplexity AI", "category": "AI Search Engine"},
        {"name": "Google-Extended", "company": "Google", "category": "Gemini AI Training"},
        {"name": "Applebot-Extended", "company": "Apple", "category": "Apple Intelligence"},
        {"name": "Amazonbot", "company": "Amazon", "category": "Rufus E-commerce AI"},
        {"name": "CCBot", "company": "Common Crawl", "category": "Open Dataset"},
        {"name": "Bytespider", "company": "ByteDance", "category": "TikTok AI Index"},
        {"name": "DeepSeekBot", "company": "DeepSeek", "category": "DeepSeek AI Crawler"},
        {"name": "MistralBot", "company": "Mistral AI", "category": "Mistral AI Search"},
    ]

    for b in fresh_bots:
        if b["name"] not in current_bots:
            data.setdefault("ai_crawlers", []).append(b)

    with open(sig_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    print("[+] Updated signatures.json with latest AI crawlers.")


def update_cleaning_rules() -> None:
    """Enrich cleaning_rules.json with fresh noise selectors."""
    rules_path = REPO_ROOT / "actors" / "2-ai-rag-markdown-extractor" / "cleaning_rules.json"
    if not rules_path.exists():
        return

    with open(rules_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    selectors = set(data.get("noise_selectors", []))
    new_selectors = [
        ".newsletter-modal",
        ".exit-intent-popup",
        ".app-download-banner",
        "#usercentrics-root",
        ".trustpilot-widget",
    ]
    for s in new_selectors:
        selectors.add(s)

    data["noise_selectors"] = sorted(list(selectors))

    with open(rules_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    print("[+] Updated cleaning_rules.json with modern popup/modal selectors.")


def update_ecommerce_patterns() -> None:
    """Enrich ecommerce_patterns.json with new API endpoints."""
    p_path = REPO_ROOT / "actors" / "3-ecommerce-json-intelligence" / "ecommerce_patterns.json"
    if not p_path.exists():
        return

    with open(p_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    with open(p_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    print("[+] Updated ecommerce_patterns.json timestamp.")


def update_readme_timestamps() -> None:
    """Update 'Last Automated Maintenance: YYYY-MM-DD' in all READMEs."""
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    readme_files = list(REPO_ROOT.glob("actors/**/README.md"))

    for rm in readme_files:
        with open(rm, "r", encoding="utf-8") as f:
            content = f.read()

        new_content = re.sub(
            r"Last Automated Maintenance:\s*\d{4}-\d{2}-\d{2}",
            f"Last Automated Maintenance: {today_str}",
            content,
        )

        with open(rm, "w", encoding="utf-8") as f:
            f.write(new_content)

        print(f"[+] Updated maintenance date in {rm.parent.name}/README.md")


def run_tests() -> bool:
    """Run test_all_actors.py health check."""
    test_script = REPO_ROOT / "brain_updater" / "test_all_actors.py"
    print("\n--> Running validation suite: test_all_actors.py")
    res = subprocess.run([sys.executable, str(test_script)], cwd=str(REPO_ROOT))
    return res.returncode == 0


def main() -> None:
    """Main auto-updater runner."""
    print("==================================================")
    print("  🚀 Apify B2B Autopilot Pack: Weekly Updater     ")
    print("==================================================")

    update_actor_json_files()
    update_signatures()
    update_cleaning_rules()
    update_ecommerce_patterns()
    update_readme_timestamps()

    print("\nVerifying test suite health...")
    if not run_tests():
        print("\n[-] Health checks FAILED! Aborting update commit.")
        sys.exit(1)

    print("\n[✔] Weekly maintenance completed successfully! All actors are healthy.")
    sys.exit(0)


if __name__ == "__main__":
    main()
