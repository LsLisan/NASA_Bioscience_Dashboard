import os
import json
import requests
from pathlib import Path
from PyPDF2 import PdfReader
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from services.ai_analyzer import AIAnalyzer


class PDFProcessor:
    def __init__(self, pdf_dir="data/pdfs", cache_dir="data/cache"):
        self.pdf_dir = Path(pdf_dir)
        self.cache_dir = Path(cache_dir)
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.analyzer = AIAnalyzer()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/117.0 Safari/537.36"
        }

    def get_pdf_url(self, article_url: str) -> str:
        """
        Construct or scrape the correct PDF URL from an article page.
        Handles direct /pdf links, relative paths, and full URLs.
        """
        # First, try the simple `/pdf` endpoint
        candidate = article_url.rstrip("/") + "/pdf"
        resp = requests.get(candidate, headers=self.headers, timeout=15)

        if "pdf" in resp.headers.get("Content-Type", "").lower():
            return candidate

        # Otherwise scrape the article page
        resp = requests.get(article_url, headers=self.headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        link = soup.select_one('a[href*="pdf"]')

        if not link:
            raise ValueError(f"No PDF link found in article page: {article_url}")

        raw_href = link["href"]

        # urljoin fixes both relative and absolute hrefs
        pdf_url = urljoin(article_url, raw_href)

        return pdf_url

    def download_pdf(self, pub, pub_id):
        """Download PDF from publication link."""
        article_url = pub["Link"]
        pdf_url = self.get_pdf_url(article_url)
        pdf_path = self.pdf_dir / f"pub_{pub_id}.pdf"

        if pdf_path.exists():
            return pdf_path

        response = requests.get(pdf_url, headers=self.headers, timeout=30)
        response.raise_for_status()

        with open(pdf_path, "wb") as f:
            f.write(response.content)

        return pdf_path

    def extract_text(self, pdf_path):
        """Extract text from PDF."""
        text = ""
        with open(pdf_path, "rb") as f:
            reader = PdfReader(f)
            for page in reader.pages:
                try:
                    text += page.extract_text() or ""
                except Exception:
                    continue
        return text.strip()

    def process_publication(self, pub, pub_id):
        """
        Download, extract, analyze, and cache publication.
        Returns dict with summary + preview.
        """
        cache_file = self.cache_dir / f"pub_{pub_id}_analysis.json"
        if cache_file.exists():
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)

        pdf_path = self.download_pdf(pub, pub_id)
        text = self.extract_text(pdf_path)

        summary = self.analyzer.summarize(text)

        result = {
            "pub_id": pub_id,
            "title": pub["Title"],
            "link": pub["Link"],
            "summary": summary,
            "text_preview": text[:2000]  # limit preview
        }

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        return result
