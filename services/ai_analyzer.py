from transformers import pipeline

class AIAnalyzer:
    def __init__(self, model_name="t5-small"):
        """
        Initialize summarization pipeline with a lightweight local model.
        - 't5-small' (fast, ~250MB, runs on CPU)
        - 'facebook/bart-large-cnn' (better summaries, heavier)
        """
        self.summarizer = pipeline("summarization", model=model_name)

    def summarize(self, text: str, max_len: int = 150, min_len: int = 40) -> str:
        """Summarize text using local T5/BART model."""
        if not text:
            return "No text available for summarization."

        # Limit length for T5 (it accepts max ~512 tokens)
        chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]

        summaries = []
        for chunk in chunks[:3]:  # only process first 3 chunks to save time
            result = self.summarizer(
                chunk,
                max_length=max_len,
                min_length=min_len,
                do_sample=False
            )
            summaries.append(result[0]['summary_text'])

        return " ".join(summaries)
