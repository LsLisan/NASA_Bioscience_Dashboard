import os
import json
import requests
import PyPDF2
import pdfplumber
from urllib.parse import urlparse
import time
from datetime import datetime

class PDFProcessor:
    def __init__(self):
        self.pdf_dir = "data/pdfs"
        self.cache_dir = "data/cache"
        
        # Create directories if they don't exist
        os.makedirs(self.pdf_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def process_publication(self, publication, pub_id):
        """Main method to process a publication"""
        try:
            # Check if already processed
            cache_file = os.path.join(self.cache_dir, f"pub_{pub_id}_analysis.json")
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    return json.load(f)
            
            # Download PDF
            pdf_path = self.download_pdf(publication['Link'], pub_id)
            if not pdf_path:
                return {"error": "Failed to download PDF"}
            
            # Extract text
            text = self.extract_text(pdf_path)
            if not text:
                return {"error": "Failed to extract text from PDF"}
            
            # Basic analysis (for now)
            analysis = {
                "title": publication['Title'],
                "pdf_path": pdf_path,
                "text_length": len(text),
                "word_count": len(text.split()),
                "extracted_at": datetime.now().isoformat(),
                "preview": text[:500] + "..." if len(text) > 500 else text,
                "status": "processed"
            }
            
            # Save to cache
            with open(cache_file, 'w') as f:
                json.dump(analysis, f, indent=2)
            
            return analysis
            
        except Exception as e:
            return {"error": f"Processing failed: {str(e)}"}
    
    def download_pdf(self, url, pub_id):
        """Download PDF from URL"""
        try:
            # Generate filename
            pdf_filename = f"pub_{pub_id}.pdf"
            pdf_path = os.path.join(self.pdf_dir, pdf_filename)
            
            # Skip if already downloaded
            if os.path.exists(pdf_path):
                return pdf_path
            
            print(f"Downloading PDF from: {url}")
            
            # Set headers to mimic a browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Download with timeout
            response = requests.get(url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()
            
            # Check if response is PDF
            content_type = response.headers.get('content-type', '')
            if 'pdf' not in content_type.lower():
                # Try to find PDF link in HTML
                if 'html' in content_type.lower():
                    pdf_url = self.find_pdf_in_html(response.text, url)
                    if pdf_url:
                        return self.download_pdf(pdf_url, pub_id)
                raise Exception(f"Not a PDF file: {content_type}")
            
            # Save PDF
            with open(pdf_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"Downloaded PDF: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            print(f"Download error: {e}")
            return None
    
    def find_pdf_in_html(self, html_content, base_url):
        """Try to find PDF link in HTML page"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for common PDF link patterns
            pdf_links = soup.find_all('a', href=lambda x: x and '.pdf' in x.lower())
            
            if pdf_links:
                href = pdf_links[0]['href']
                # Handle relative URLs
                if href.startswith('/'):
                    parsed_url = urlparse(base_url)
                    return f"{parsed_url.scheme}://{parsed_url.netloc}{href}"
                elif href.startswith('http'):
                    return href
                else:
                    return f"{base_url.rstrip('/')}/{href}"
            
            return None
        except:
            return None
    
    def extract_text(self, pdf_path):
        """Extract text from PDF file"""
        text = ""
        
        try:
            # Try pdfplumber first (better for complex layouts)
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"pdfplumber failed: {e}, trying PyPDF2...")
            
            # Fallback to PyPDF2
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            except Exception as e:
                print(f"PyPDF2 also failed: {e}")
                return None
        
        # Clean up text
        text = self.clean_text(text)
        return text if text.strip() else None
    
    def clean_text(self, text):
        """Clean extracted text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line and len(line) > 2:  # Skip very short lines
                cleaned_lines.append(line)
        
        # Join lines and normalize spacing
        cleaned_text = ' '.join(cleaned_lines)
        cleaned_text = ' '.join(cleaned_text.split())  # Normalize whitespace
        
        return cleaned_text
    
    def get_pdf_info(self, pdf_path):
        """Get basic info about the PDF"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                info = {
                    'num_pages': len(pdf_reader.pages),
                    'file_size': os.path.getsize(pdf_path),
                    'metadata': pdf_reader.metadata if hasattr(pdf_reader, 'metadata') else {}
                }
                return info
        except:
            return {'num_pages': 0, 'file_size': 0, 'metadata': {}}