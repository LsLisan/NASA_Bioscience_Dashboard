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

        # Initialize AI summarizer
        self.ai_analyzer = AIAnalyzer(model_name="t5-small")

    # -------------------------------
    # PubMed Central (PMC) BioC API
    # -------------------------------
    def fetch_from_bioc_api(self, pub_id: str) -> dict:
        url = f"https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_json/{pub_id}/unicode"
        resp = requests.get(url, timeout=30)

        if resp.status_code != 200:
            raise RuntimeError(f"BioC API request failed for {pub_id}: {resp.status_code}")

        data = resp.json()
        passages = []
        for doc in data.get("documents", []):
            for passage in doc.get("passages", []):
                text = passage.get("text")
                if text:
                    passages.append(text)

        return {
            "text": "\n".join(passages).strip(),
            "meta": data
        }

    # -------------------------------
    # PDF download + extract fallback
    # -------------------------------
    def download_pdf(self, pub, pub_id):
        base_url = pub["Link"].strip()
        if not base_url.startswith("http"):
            raise ValueError(f"Invalid publication link: {base_url}")

        pdf_url = base_url.rstrip("/") + "/pdf/"
        pdf_path = self.pdf_dir / f"pub_{pub_id}.pdf"

        if pdf_path.exists():
            return pdf_path

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            ),
            "Accept": "text/html,application/pdf",
            "Referer": "https://pmc.ncbi.nlm.nih.gov/"
        }

        response = requests.get(pdf_url, headers=headers, timeout=30, allow_redirects=True)

        if "application/pdf" in response.headers.get("Content-Type", ""):
            with open(pdf_path, "wb") as f:
                f.write(response.content)
            return pdf_path

        soup = BeautifulSoup(response.text, "html.parser")
        pdf_link = None
        for a in soup.find_all("a", href=True):
            if a["href"].endswith(".pdf"):
                pdf_link = a["href"]
                break

        if not pdf_link:
            raise RuntimeError(f"No PDF link found at {pdf_url}")

        pdf_link = urljoin(pdf_url, pdf_link)
        pdf_resp = requests.get(pdf_link, headers=headers, timeout=30, allow_redirects=True)
        pdf_resp.raise_for_status()

        with open(pdf_path, "wb") as f:
            f.write(pdf_resp.content)

        return pdf_path

    def extract_text(self, pdf_path: Path) -> str:
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        reader = PdfReader(str(pdf_path))
        text = []
        for page in reader.pages:
            text.append(page.extract_text() or "")
        return "\n".join(text).strip()

    # -------------------------------
    # Main handler
    # -------------------------------
    def process_publication(self, pub, pub_id):
        cache_file = self.cache_dir / f"pub_{pub_id}_analysis.json"
        if cache_file.exists():
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)

        text = ""
        used_api = False

        if "pmc.ncbi.nlm.nih.gov" in pub["Link"].lower() or str(pub_id).startswith("PMC"):
            try:
                bioc_data = self.fetch_from_bioc_api(pub_id)
                text = bioc_data["text"]
                used_api = True
            except Exception as e:
                print(f"[WARN] BioC API failed: {e}. Falling back to PDF.")

        if not text:
            pdf_path = self.download_pdf(pub, pub_id)
            text = self.extract_text(pdf_path)

        # 🔥 Use AIAnalyzer for summary
        summary = self.ai_analyzer.summarize(text)

        result = {
            "pub_id": pub_id,
            "title": pub["Title"],
            "link": pub["Link"],
            "source": "BioC API" if used_api else "PDF",
            "summary": summary,
            "text_preview": text[:2000]  # first 2000 chars
        }

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        return result
