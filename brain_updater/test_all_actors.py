"""Comprehensive health test suite for the Apify B2B Autopilot Pack.

Validates:
1. Python syntax & compilation across all actors.
2. JSON schema validity and required Apify properties.
3. Core algorithmic units:
   - French SIREN to intra-EU VAT modulo 97 computation.
   - HTML to clean Markdown conversion and RAG chunking.
   - E-commerce catalog price statistics calculation.
"""

import compileall
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_module_from_path(module_name: str, file_path: Path) -> Any:
    """Dynamically load module from absolute path without module cache collisions."""
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestActorJsonSchemas(unittest.TestCase):
    """Validate all JSON configuration and schema files across the monorepo."""

    def test_json_files_are_valid(self):
        json_files = list(REPO_ROOT.glob("actors/**/*.json"))
        self.assertGreater(len(json_files), 5, "Should find multiple JSON files in actors directory")

        for jf in json_files:
            with open(jf, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    self.assertIsInstance(data, (dict, list), f"File {jf} should parse to dict or list")
                except Exception as e:
                    self.fail(f"Invalid JSON in {jf}: {e}")

    def test_actor_json_specifications(self):
        actor_jsons = list(REPO_ROOT.glob("actors/**/.actor/actor.json"))
        self.assertEqual(len(actor_jsons), 3, "Expected exactly 3 actor.json files")

        for aj in actor_jsons:
            with open(aj, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.assertEqual(data.get("actorSpecification"), 1)
                self.assertTrue(bool(data.get("name")), f"Missing name in {aj}")
                self.assertTrue(bool(data.get("version")), f"Missing version in {aj}")
                self.assertEqual(data.get("dockerfile"), "./Dockerfile")
                self.assertEqual(data.get("input"), "./input_schema.json")

    def test_input_schemas(self):
        input_schemas = list(REPO_ROOT.glob("actors/**/.actor/input_schema.json"))
        self.assertEqual(len(input_schemas), 3, "Expected exactly 3 input_schema.json files")

        for is_path in input_schemas:
            with open(is_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.assertEqual(data.get("type"), "object")
                self.assertEqual(data.get("schemaVersion"), 1)
                self.assertIn("properties", data)
                self.assertIn("required", data)


class TestActorAlgorithms(unittest.TestCase):
    """Test core algorithmic and business logic of the 3 actors."""

    def test_vat_calculation(self):
        actor1_path = REPO_ROOT / "actors" / "1-eu-b2b-compliance-auditor" / "src" / "main.py"
        actor1 = load_module_from_path("actor1_main_module", actor1_path)

        # Doctolib SIREN: 794598813
        # 794598813 % 97 = 33
        # (12 + 3 * 33) % 97 = (12 + 99) % 97 = 111 % 97 = 14
        # VAT: FR14794598813
        vat = actor1.compute_french_vat("794598813")
        self.assertEqual(vat, "FR14794598813")

        # Test invalid inputs
        self.assertEqual(actor1.compute_french_vat("123"), "")
        self.assertEqual(actor1.compute_french_vat("ABC"), "")

    def test_markdown_and_rag_chunking(self):
        actor2_path = REPO_ROOT / "actors" / "2-ai-rag-markdown-extractor" / "src" / "main.py"
        actor2 = load_module_from_path("actor2_main_module", actor2_path)
        from bs4 import BeautifulSoup

        raw_html = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <header><h1>Header to Ignore</h1></header>
                <main>
                    <h1>Official Documentation</h1>
                    <p>This is the first paragraph describing <strong>high-performance</strong> AI features.</p>
                    <p>Check out <a href="/docs/guide">the guide</a> for more info.</p>
                    <table>
                        <tr><th>Param</th><th>Default</th></tr>
                        <tr><td>timeout</td><td>15</td></tr>
                    </table>
                </main>
                <footer><p>Footer to ignore</p></footer>
            </body>
        </html>
        """
        soup = BeautifulSoup(raw_html, "html.parser")
        rules = actor2.load_cleaning_rules()
        clean_soup = actor2.clean_html_soup(soup, rules)
        md = actor2.html_to_markdown(clean_soup, base_url="https://example.com")

        self.assertIn("# Official Documentation", md)
        self.assertIn("**high-performance**", md)
        self.assertIn("[the guide](https://example.com/docs/guide)", md)
        self.assertIn("| Param | Default |", md)
        self.assertNotIn("Header to Ignore", md)
        self.assertNotIn("Footer to ignore", md)

        chunks = actor2.generate_rag_chunks(md, source_url="https://example.com", chunk_size=200, chunk_overlap=50)
        self.assertGreater(len(chunks), 0)
        self.assertEqual(chunks[0]["source_url"], "https://example.com")
        self.assertIn("token_estimate", chunks[0])

    def test_ecommerce_price_stats(self):
        actor3_path = REPO_ROOT / "actors" / "3-ecommerce-json-intelligence" / "src" / "main.py"
        actor3 = load_module_from_path("actor3_main_module", actor3_path)

        sample_products = [
            {"price": 100.0, "is_discounted": False, "in_stock": True},
            {"price": 50.0, "is_discounted": True, "in_stock": True},
            {"price": 150.0, "is_discounted": True, "in_stock": False},
        ]

        stats = actor3.compute_catalog_stats(sample_products)
        self.assertEqual(stats["min_price"], 50.0)
        self.assertEqual(stats["max_price"], 150.0)
        self.assertEqual(stats["avg_price"], 100.0)
        self.assertEqual(stats["median_price"], 100.0)
        self.assertEqual(stats["discounted_products_count"], 2)
        self.assertEqual(stats["discount_rate"], 66.7)
        self.assertEqual(stats["in_stock_ratio"], 66.7)


def run_all_tests() -> bool:
    """Run Python compilation and unittest suite."""
    print("=== [1/2] Compiling all Python sources ===")
    compile_success = compileall.compile_dir(REPO_ROOT, force=True, quiet=1)
    if not compile_success:
        print("[-] Compilation error found in Python files!")
        return False
    print("[+] All Python files compiled successfully without syntax errors.")

    print("\n=== [2/2] Running Unit & Integration Tests ===")
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
