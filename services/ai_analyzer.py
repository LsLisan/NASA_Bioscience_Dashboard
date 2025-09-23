from transformers import pipeline
import nltk
nltk.download('punkt')
from nltk.tokenize import sent_tokenize

class AIAnalyzer:
    def __init__(self, model_name="sshleifer/distilbart-cnn-12-6"):
        """
        Optimized summarizer for scientific papers:
        - Lightweight (~300MB)
        - Focus on Methodology, Methods, Results, and Discussion
        - Handles long documents in chunks
        """
        print("Initializing summarizer model...")
        self.summarizer = pipeline("summarization", model=model_name)

    def _chunk_text(self, text, max_chunk_size=1000):
        """
        Split text into chunks of roughly max_chunk_size characters
        while maintaining sentence integrity.
        """
        sentences = sent_tokenize(text)
        chunks = []
        chunk = []
        chunk_len = 0

        for sentence in sentences:
            chunk_len += len(sentence)
            chunk.append(sentence)
            if chunk_len >= max_chunk_size:
                chunks.append(" ".join(chunk))
                chunk = []
                chunk_len = 0

        if chunk:
            chunks.append(" ".join(chunk))
        return chunks

    def summarize(self, text: str, max_len: int = 250, min_len: int = 80) -> str:
        if not text:
            return "No text available for summarization."

        chunks = self._chunk_text(text, max_chunk_size=1200)
        summaries = []

        # Emphasized instruction: focus on methodology, methods, results, discussion
        instructions = (
            "Summarize this paper focusing primarily on:\n"
            "- Methodology and experimental approach\n"
            "- Specific methods and techniques used\n"
            "- Key results and findings\n"
            "- Discussion and implications\n"
            "Keep the summary precise, structured, and detailed."
        )

        # Process all chunks but limit to avoid OOM issues
        for chunk in chunks[:7]:  # Adjust number of chunks for memory
            try:
                result = self.summarizer(
                    instructions + "\n" + chunk,
                    max_length=max_len,
                    min_length=min_len,
                    do_sample=False
                )
                summaries.append(result[0]['summary_text'])
            except Exception as e:
                print(f"[WARN] Chunk summarization failed: {e}")
                continue

        combined_summary = " ".join(summaries)

        # Knowledge gaps / future directions
        knowledge_gap_prompt = (
            "Based on this summary, identify:\n"
            "- Potential research gaps\n"
            "- Limitations\n"
            "- Open questions for future research"
        )
        try:
            gap_result = self.summarizer(
                knowledge_gap_prompt + "\n" + combined_summary,
                max_length=200,
                min_length=80,
                do_sample=False
            )
            knowledge_gaps = gap_result[0]['summary_text']
        except Exception as e:
            print(f"[WARN] Knowledge gap generation failed: {e}")
            knowledge_gaps = "Could not generate knowledge gaps due to memory constraints."

        return (
            f"### Methodology, Methods & Results Summary\n{combined_summary}\n\n"
            f"### Knowledge Gaps & Future Directions\n{knowledge_gaps}"
        )
