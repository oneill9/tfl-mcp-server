"""Check the published files and discovery links in a built MkDocs site."""

import json
import re
import sys
import unittest
import xml.etree.ElementTree as ElementTree
from html.parser import HTMLParser
from pathlib import Path


class DocumentationPageDriver(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.reference_links = []
        self.feed(path.read_text())

    def handle_starttag(self, tag, attributes):
        attributes = dict(attributes)
        if tag == "link" and attributes.get("rel") == "describedby":
            self.reference_links.append((attributes.get("href"), attributes.get("type")))


class DocumentationSiteDriver:
    def __init__(self, directory):
        self.directory = directory

    def pages(self):
        return list(self.directory.rglob("*.html"))

    def reference(self, name):
        return (self.directory / name).read_bytes()

    def has_rendered_markdown_reference(self):
        return (self.directory / "llms" / "index.html").exists()

    def sitemap_urls(self):
        root = ElementTree.parse(self.directory / "sitemap.xml").getroot()
        namespace = {"sitemap": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        return [location.text for location in root.findall("sitemap:url/sitemap:loc", namespace)]


class IndexNowDeploymentDriver:
    def __init__(self, repository, site):
        self.repository = repository
        self.site = site
        self.workflow = (repository / ".github" / "workflows" / "pages.yml").read_text()

    def key_files(self):
        return list((self.repository / "docs").glob("[0-9a-f]" * 32 + ".txt"))

    def payload(self):
        match = re.search(r"--data-binary\s+'(\{.*?\})'", self.workflow, re.DOTALL)
        return json.loads(match.group(1)) if match else None

    def key_verification_retry_window(self):
        retry = re.search(r"--retry (\d+)", self.workflow)
        delay = re.search(r"--retry-delay (\d+)", self.workflow)
        return int(retry.group(1)) * int(delay.group(1))

    def publishes_current_commit_marker(self):
        return ('printf \'%s\\n\' "$GITHUB_SHA" '
                '> "docs/deployment-${GITHUB_SHA}.txt"') in self.workflow

    def readiness_probe(self):
        match = re.search(
            r'test "\$\(curl.*?"(https://[^"\n]+)"\)"\s*\\\s*\n\s*= "([^"\n]+)"',
            self.workflow,
            re.DOTALL,
        )
        return match.groups() if match else None


class DocumentationDiscoveryTest(unittest.TestCase):
    def test_every_page_links_to_the_same_raw_references_even_from_nested_paths(self):
        site = DocumentationSiteDriver(SITE_DIRECTORY)
        self.assertTrue(site.pages(), "Build the MkDocs site before running this test")
        for path in site.pages():
            with self.subTest(page=str(path.relative_to(SITE_DIRECTORY))):
                page = DocumentationPageDriver(path)
                self.assertEqual(page.reference_links, [
                    ("https://oneill9.github.io/tfl-mcp-server/llms.txt", "text/plain"),
                    ("https://oneill9.github.io/tfl-mcp-server/llms.md", "text/markdown"),
                ])

    def test_build_publishes_both_references_without_rendering_markdown_to_html(self):
        site = DocumentationSiteDriver(SITE_DIRECTORY)
        source_directory = Path(__file__).resolve().parent.parent / "docs"
        for name in ("llms.txt", "llms.md"):
            with self.subTest(reference=name):
                content = site.reference(name)
                self.assertEqual(content, (source_directory / name).read_bytes())
                self.assertTrue(content.startswith(b"# TfL MCP Server\n\n> "))
                self.assertNotIn(b"<html", content.lower())
        self.assertFalse(site.has_rendered_markdown_reference())
        self.assertIn(b"](https://oneill9.github.io/tfl-mcp-server/llms.md)",
                      site.reference("llms.txt"))
        for tool in (b"service_status", b"arrivals", b"journey", b"bike_points", b"crowding", b"fares"):
            self.assertIn(tool, site.reference("llms.md"))

    def test_indexnow_is_notified_after_deployment_for_every_sitemap_url(self):
        repository = Path(__file__).resolve().parent.parent
        site = DocumentationSiteDriver(SITE_DIRECTORY)
        deployment = IndexNowDeploymentDriver(repository, site)
        key_files = deployment.key_files()

        self.assertEqual(len(key_files), 1)
        key_file = key_files[0]
        key = key_file.stem
        self.assertEqual(key_file.read_text().strip(), key)
        self.assertEqual((SITE_DIRECTORY / key_file.name).read_text(), key_file.read_text())
        self.assertIn("\n  indexnow:\n", deployment.workflow)
        self.assertIn("needs: deploy", deployment.workflow)
        self.assertIn("--fail-with-body", deployment.workflow)
        self.assertTrue(deployment.publishes_current_commit_marker())
        self.assertEqual(deployment.readiness_probe(), (
            "https://oneill9.github.io/tfl-mcp-server/deployment-${GITHUB_SHA}.txt",
            "$GITHUB_SHA",
        ))
        self.assertGreaterEqual(deployment.key_verification_retry_window(), 60)
        self.assertEqual(deployment.payload(), {
            "host": "oneill9.github.io",
            "key": key,
            "keyLocation": f"https://oneill9.github.io/tfl-mcp-server/{key}.txt",
            "urlList": site.sitemap_urls(),
        })


if __name__ == "__main__":
    SITE_DIRECTORY = Path(sys.argv.pop(1)) if len(sys.argv) > 1 else Path("site")
    unittest.main()
