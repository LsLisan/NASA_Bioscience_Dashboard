from pathlib import Path
from services.pdf_processor import PDFProcessor
from services.ai_analyzer import AIAnalyzer

class UploadPDFService:
    def __init__(self, upload_dir="data/uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        self.pdf_processor = PDFProcessor()
        self.ai_analyzer = AIAnalyzer()

    def handle_upload(self, pdf_file) -> dict:
        """
        Save uploaded PDF, extract text, summarize with AI.
        Returns dict: {summary, text_preview}.
        """
        if not pdf_file or pdf_file.filename == "":
            raise ValueError("No file uploaded")

        # Save PDF
        save_path = self.upload_dir / pdf_file.filename
        pdf_file.save(str(save_path))

        # Extract text
        text = self.pdf_processor.extract_text(save_path)

        # Summarize with AI
        summary = self.ai_analyzer.summarize(text)

        return {
            "summary": summary,
            "text_preview": text[:2000]  # first 2000 characters as preview
        }
