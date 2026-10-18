"""EU B2B Compliance Auditor Actor.

Extracts verified legal company data (SIREN, SIRET, Intra-EU VAT, NAF, executives)
and computes 3 actionable compliance scores:
- GDPR Compliance Score
- European Accessibility Act (EAA 2025) Score
- AI Agent Readiness Score (llms.txt, robots.txt, schema.org)
"""

import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional
import urllib.parse

from apify import Actor
from bs4 import BeautifulSoup
import requests
import urllib3

# Suppress insecure SSL warnings for heuristic fallbacks
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/128.0.0.0 Safari/537.36 ApifyB2BAuditor/1.0"
)

SIGNATURES_FILE = Path(__file__).resolve().parent.parent / "signatures.json"


def load_signatures() -> Dict[str, Any]:
    """Load signature definitions for bots, CMPs, trackers, and rules."""
    if SIGNATURES_FILE.exists():
        try:
            with open(SIGNATURES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            Actor.log.warning(f"Could not load signatures.json: {e}")
    return {
        "ai_crawlers": [{"name": "GPTBot"}, {"name": "ClaudeBot"}, {"name": "PerplexityBot"}],
        "legal_paths": ["/mentions-legales", "/privacy", "/politique-de-confidentialite"],
        "cookie_consent_signatures": ["axeptio", "didomi", "tarteaucitron", "cookiebot"],
        "trackers": [],
    }


def compute_french_vat(siren: str) -> str:
    """Compute mathematical French Intra-community VAT number from 9-digit SIREN.

    Formula: Key = (12 + 3 * (SIREN % 97)) % 97
    Result: FR + Key (2 digits) + SIREN
    """
    clean_siren = re.sub(r"\D", "", siren)
    if len(clean_siren) != 9:
        return ""
    try:
        siren_num = int(clean_siren)
        key = (12 + 3 * (siren_num % 97)) % 97
        return f"FR{key:02d}{clean_siren}"
    except Exception:
        return ""


def clean_target_query(target: str) -> str:
    """Normalize input domain or business name into search term."""
    cleaned = target.strip()
    # Strip URL schemes if user passed full URL
    cleaned = re.sub(r"^https?://", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.split("/")[0]  # retain domain root if URL was given
    return cleaned


def query_api_gouv_entreprise(query: str, timeout: int = 10) -> Dict[str, Any]:
    """Query French official open-data API (recherche-entreprises.api.gouv.fr)

    Free, no API key required, reliable governmental database.
    """
    clean_q = clean_target_query(query)
    # Strip common TLDs for the French registry search if querying by domain
    search_term = re.sub(r"\.(fr|com|io|net|org|eu|co)$", "", clean_q, flags=re.IGNORECASE)

    url = f"https://recherche-entreprises.api.gouv.fr/search?q={urllib.parse.quote(search_term)}&limite=1"
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}

    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            if results:
                item = results[0]
                siren = item.get("siren", "")
                siege = item.get("siege", {})
                siret = siege.get("siret", item.get("siret", ""))
                nom_complet = item.get("nom_complet", "")
                naf_code = item.get("activite_principale", "")
                effectif = item.get("tranche_effectif_salarie", "Non précisé")

                # Representatives / Dirigeants
                dirigeants_raw = item.get("dirigeants", [])
                dirigeants = []
                for d in dirigeants_raw:
                    nom = d.get("nom", "") or ""
                    prenom = d.get("prenoms", "") or ""
                    qualite = d.get("qualite", "") or ""
                    full_name = f"{prenom} {nom}".strip() or d.get("denomination", "")
                    if full_name:
                        dirigeants.append(f"{full_name} ({qualite})" if qualite else full_name)

                # Address composition
                adresse_parts = [
                    siege.get("numero_voie"),
                    siege.get("type_voie"),
                    siege.get("libelle_voie"),
                    siege.get("code_postal"),
                    siege.get("libelle_commune"),
                ]
                adresse = " ".join([p for p in adresse_parts if p]).strip()

                return {
                    "found": True,
                    "siren": siren,
                    "siret": siret,
                    "company_name": nom_complet,
                    "vat_number": compute_french_vat(siren),
                    "naf_code": naf_code,
                    "employee_bracket": effectif,
                    "address": adresse or siege.get("adresse_complete", ""),
                    "legal_representatives": dirigeants,
                }
    except Exception as e:
        Actor.log.warning(f"Error querying recherche-entreprises API for '{query}': {e}")

    return {
        "found": False,
        "siren": "",
        "siret": "",
        "company_name": clean_q,
        "vat_number": "",
        "naf_code": "",
        "employee_bracket": "Unknown",
        "address": "",
        "legal_representatives": [],
    }


def fetch_url(url: str, timeout: int = 15) -> Optional[requests.Response]:
    """Fetch URL with browser headers and SSL fallback."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True, verify=True)
        return resp
    except requests.exceptions.SSLError:
        try:
            resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True, verify=False)
            return resp
        except Exception:
            return None
    except Exception:
        return None


def audit_website_compliance(
    target: str,
    signatures: Dict[str, Any],
    deep_scan: bool = True,
    timeout: int = 15,
) -> Dict[str, Any]:
    """Perform in-depth audit of GDPR, European Accessibility Act (EAA), and AI Agent Readiness."""
    domain = clean_target_query(target)
    base_url = f"https://{domain}"

    resp = fetch_url(base_url, timeout=timeout)
    if not resp or resp.status_code >= 400:
        # Fallback to http if https failed
        base_url = f"http://{domain}"
        resp = fetch_url(base_url, timeout=timeout)

    html_content = resp.text if resp else ""
    soup = BeautifulSoup(html_content, "html.parser") if html_content else None

    # --- 1. GDPR Audit ---
    gdpr_score = 0
    gdpr_breakdown = {
        "legal_notice_detected": False,
        "privacy_policy_detected": False,
        "cookie_banner_detected": False,
        "trackers_detected": [],
    }
    actionable_fixes = []

    if soup:
        # Check links on homepage for legal notices / privacy
        links = soup.find_all("a", href=True)
        for a in links:
            href = a["href"].lower()
            text = a.get_text(strip=True).lower()
            if any(term in href or term in text for term in ["mentions-legales", "mentions légales", "legal-notice"]):
                gdpr_breakdown["legal_notice_detected"] = True
            if any(term in href or term in text for term in ["confidentialite", "politique de confidentialité", "privacy"]):
                gdpr_breakdown["privacy_policy_detected"] = True

        # Check CMP / Cookie banner signatures
        page_raw = html_content.lower()
        for cmp_sig in signatures.get("cookie_consent_signatures", []):
            if cmp_sig in page_raw:
                gdpr_breakdown["cookie_banner_detected"] = True
                break

        # Check Trackers
        for tracker in signatures.get("trackers", []):
            pattern = tracker.get("pattern", "")
            if re.search(pattern, html_content, re.IGNORECASE):
                gdpr_breakdown["trackers_detected"].append(tracker.get("name"))

    # If deep scan is enabled, probe direct standard legal paths
    if deep_scan and not (gdpr_breakdown["legal_notice_detected"] and gdpr_breakdown["privacy_policy_detected"]):
        for path in ["/mentions-legales", "/politique-de-confidentialite", "/privacy"]:
            test_resp = fetch_url(f"https://{domain}{path}", timeout=5)
            if test_resp and test_resp.status_code == 200:
                if "mention" in path:
                    gdpr_breakdown["legal_notice_detected"] = True
                if "politique" in path or "privacy" in path:
                    gdpr_breakdown["privacy_policy_detected"] = True

    # Compute GDPR score
    if gdpr_breakdown["legal_notice_detected"]:
        gdpr_score += 35
    else:
        actionable_fixes.append(
            "CRITICAL GDPR: Add an accessible 'Mentions Légales' page referencing your SIRET, intra-EU VAT, and host."
        )

    if gdpr_breakdown["privacy_policy_detected"]:
        gdpr_score += 35
    else:
        actionable_fixes.append(
            "CRITICAL GDPR: Add a 'Politique de Confidentialité' detailing GDPR data collection, retention, and user rights."
        )

    if gdpr_breakdown["cookie_banner_detected"]:
        gdpr_score += 30
    else:
        actionable_fixes.append(
            "HIGH GDPR: Implement an official ePrivacy/GDPR cookie banner (Axeptio, Didomi, Tarteaucitron) with prior consent."
        )

    # --- 2. European Accessibility Act (EAA 2025 / WCAG 2.1) Audit ---
    eaa_score = 0
    eaa_breakdown = {
        "html_lang_valid": False,
        "image_alt_coverage_pct": 0,
        "form_controls_labeled": False,
        "semantic_structure_score": 0,
    }

    if soup:
        # Rule 1: <html lang="...">
        html_tag = soup.find("html")
        if html_tag and html_tag.get("lang"):
            eaa_breakdown["html_lang_valid"] = True
            eaa_score += 25
        else:
            actionable_fixes.append("EAA ACCESSIBILITY: Add a valid 'lang' attribute to the <html> tag (e.g. lang=\"fr\").")

        # Rule 2: Image alt attributes
        images = soup.find_all("img")
        if images:
            with_alt = [img for img in images if img.has_attr("alt")]
            coverage = int((len(with_alt) / len(images)) * 100)
            eaa_breakdown["image_alt_coverage_pct"] = coverage
            if coverage >= 80:
                eaa_score += 25
            elif coverage >= 40:
                eaa_score += 15
                actionable_fixes.append(f"EAA ACCESSIBILITY: Improve image alt attribute coverage ({coverage}% detected, goal 100%).")
            else:
                actionable_fixes.append(f"EAA ACCESSIBILITY: {len(images) - len(with_alt)} images are missing an alt description.")
        else:
            eaa_score += 25
            eaa_breakdown["image_alt_coverage_pct"] = 100

        # Rule 3: Form inputs labeled
        forms = soup.find_all("form")
        inputs = soup.find_all(["input", "textarea", "select"])
        if inputs:
            labeled = 0
            for inp in inputs:
                inp_type = inp.get("type", "")
                if inp_type in ["hidden", "submit", "button"]:
                    labeled += 1
                    continue
                inp_id = inp.get("id")
                has_label = False
                if inp_id and soup.find("label", attrs={"for": inp_id}):
                    has_label = True
                elif inp.get("aria-label") or inp.get("aria-labelledby") or inp.get("placeholder"):
                    has_label = True
                if has_label:
                    labeled += 1
            form_coverage = int((labeled / len(inputs)) * 100) if inputs else 100
            if form_coverage >= 70:
                eaa_score += 25
                eaa_breakdown["form_controls_labeled"] = True
            else:
                actionable_fixes.append("EAA ACCESSIBILITY: Ensure all form inputs have associated <label> or aria-label attributes.")
        else:
            eaa_score += 25
            eaa_breakdown["form_controls_labeled"] = True

        # Rule 4: Semantic landmarks (header, nav, main, footer)
        landmarks = ["header", "nav", "main", "footer"]
        found_landmarks = [l for l in landmarks if soup.find(l) or soup.find(role=l)]
        landmark_score = int((len(found_landmarks) / 4) * 25)
        eaa_score += landmark_score
        eaa_breakdown["semantic_structure_score"] = landmark_score
        if landmark_score < 20:
            actionable_fixes.append("EAA ACCESSIBILITY: Use HTML5 landmark elements (<header>, <nav>, <main>, <footer>) for screen readers.")

    # --- 3. AI Agent Readiness Audit (GEO / llms.txt / Schema.org) ---
    ai_score = 0
    ai_breakdown = {
        "llms_txt_present": False,
        "robots_ai_allowed": False,
        "schema_org_json_ld": False,
        "allowed_bots": [],
        "blocked_bots": [],
    }

    # Check /llms.txt
    llms_resp = fetch_url(f"https://{domain}/llms.txt", timeout=6)
    if llms_resp and llms_resp.status_code == 200 and len(llms_resp.text.strip()) > 20:
        ai_breakdown["llms_txt_present"] = True
        ai_score += 35
    else:
        actionable_fixes.append(
            "AI READINESS: Deploy a standardized /llms.txt file to allow Claude, ChatGPT, and Perplexity to index your documentation."
        )

    # Check robots.txt for AI bots
    robots_resp = fetch_url(f"https://{domain}/robots.txt", timeout=6)
    if robots_resp and robots_resp.status_code == 200:
        robots_text = robots_resp.text.lower()
        blocked = []
        allowed = []
        for crawler in signatures.get("ai_crawlers", []):
            name = crawler.get("name", "").lower()
            # If explicit "Disallow: /" right after User-agent: <bot>
            pattern = rf"user-agent:\s*{name}[\s\S]*?disallow:\s*/"
            if re.search(pattern, robots_text):
                blocked.append(crawler.get("name"))
            else:
                allowed.append(crawler.get("name"))

        ai_breakdown["allowed_bots"] = allowed
        ai_breakdown["blocked_bots"] = blocked
        if not blocked:
            ai_score += 35
            ai_breakdown["robots_ai_allowed"] = True
        else:
            ai_score += 15
            actionable_fixes.append(
                f"AI READINESS (GEO): Allow key AI bots in robots.txt (currently blocking: {', '.join(blocked)}) to be cited in ChatGPT/Perplexity search."
            )
    else:
        # No robots.txt means everything is allowed by default
        ai_score += 35
        ai_breakdown["robots_ai_allowed"] = True

    # Check Schema.org / JSON-LD
    if soup:
        scripts = soup.find_all("script", attrs={"type": "application/ld+json"})
        if scripts:
            ai_breakdown["schema_org_json_ld"] = True
            ai_score += 30
        else:
            actionable_fixes.append(
                "AI READINESS: Add Schema.org JSON-LD (Organization, WebSite) for rich snippets and generative engine knowledge graphs."
            )

    return {
        "audited_url": base_url,
        "gdpr_compliance_score": min(100, gdpr_score),
        "european_accessibility_eaa_score": min(100, eaa_score),
        "ai_agent_readiness_score": min(100, ai_score),
        "gdpr_breakdown": gdpr_breakdown,
        "eaa_breakdown": eaa_breakdown,
        "ai_breakdown": ai_breakdown,
        "actionable_fixes": actionable_fixes,
    }


async def main() -> None:
    """Apify Actor lifecycle entrypoint."""
    async with Actor:
        actor_input = await Actor.get_input() or {}
        targets = actor_input.get("targets", ["doctolib.fr", "ovhcloud.com"])
        deep_scan = actor_input.get("deep_scan", True)
        timeout = actor_input.get("timeout_seconds", 15)

        if isinstance(targets, str):
            targets = [t.strip() for t in targets.split(",") if t.strip()]

        Actor.log.info(f"Starting EU B2B Compliance Auditor for {len(targets)} target(s)...")
        signatures = load_signatures()

        results_count = 0
        for target in targets:
            Actor.log.info(f"Auditing legal & compliance for target: {target}")

            # 1. Official French/EU Company Registry (recherche-entreprises.api.gouv.fr)
            company_data = query_api_gouv_entreprise(target, timeout=timeout)

            # 2. Web compliance audit (GDPR, EAA 2025, AI Agent Readiness)
            web_audit = audit_website_compliance(
                target=target,
                signatures=signatures,
                deep_scan=deep_scan,
                timeout=timeout,
            )

            # 3. Consolidation
            merged_record = {
                "target": target,
                "audited_url": web_audit["audited_url"],
                "company_name": company_data["company_name"],
                "siren": company_data["siren"],
                "siret": company_data["siret"],
                "vat_number": company_data["vat_number"],
                "naf_code": company_data["naf_code"],
                "employee_bracket": company_data["employee_bracket"],
                "address": company_data["address"],
                "legal_representatives": company_data["legal_representatives"],
                "gdpr_compliance_score": web_audit["gdpr_compliance_score"],
                "european_accessibility_eaa_score": web_audit["european_accessibility_eaa_score"],
                "ai_agent_readiness_score": web_audit["ai_agent_readiness_score"],
                "audit_details": {
                    "gdpr": web_audit["gdpr_breakdown"],
                    "eaa": web_audit["eaa_breakdown"],
                    "ai_agent": web_audit["ai_breakdown"],
                },
                "actionable_fixes": web_audit["actionable_fixes"],
                "scanned_at": datetime.now(timezone.utc).isoformat(),
            }

            await Actor.push_data(merged_record)
            results_count += 1

        Actor.log.info(f"Completed! Successfully audited and pushed {results_count} record(s).")


if __name__ == "__main__":
    asyncio.run(main())
