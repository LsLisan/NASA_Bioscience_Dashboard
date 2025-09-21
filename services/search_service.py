import pandas as pd
import re
from math import ceil

class SearchService:
    def __init__(self):
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being'
        }
    
    def preprocess_query(self, query):
        """Clean and preprocess search query"""
        # Convert to lowercase and remove special characters
        query = re.sub(r'[^\w\s]', ' ', query.lower())
        # Split into words and remove stop words
        words = [word.strip() for word in query.split() 
                if word.strip() and word not in self.stop_words and len(word) > 2]
        return words
    
    def search(self, df, query, page=1, per_page=10):
        """Search publications based on query"""
        if df is None or df.empty:
            return {"publications": [], "total": 0, "total_pages": 0}
        
        # Preprocess query
        search_terms = self.preprocess_query(query)
        
        if not search_terms:
            return {"publications": [], "total": 0, "total_pages": 0}
        
        # Create search pattern
        pattern = '|'.join(search_terms)
        
        # Search in title (case insensitive)
        mask = df['Title'].str.contains(pattern, case=False, na=False, regex=True)
        
        # Filter results
        filtered_df = df[mask].copy()
        
        # Add relevance score (simple word count matching)
        filtered_df['relevance'] = filtered_df['Title'].apply(
            lambda x: self.calculate_relevance(x, search_terms)
        )
        
        # Sort by relevance
        filtered_df = filtered_df.sort_values('relevance', ascending=False)
        
        # Calculate pagination
        total = len(filtered_df)
        total_pages = ceil(total / per_page)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        # Get page results
        page_results = filtered_df.iloc[start_idx:end_idx]
        
        # Convert to list of dictionaries with index
        publications = []
        for idx, row in page_results.iterrows():
            pub_dict = row.to_dict()
            pub_dict['index'] = idx  # Original dataframe index for ID
            publications.append(pub_dict)
        
        return {
            "publications": publications,
            "total": total,
            "total_pages": total_pages,
            "current_page": page
        }
    
    def calculate_relevance(self, title, search_terms):
        """Calculate relevance score based on term frequency"""
        title_lower = title.lower()
        score = 0
        
        for term in search_terms:
            # Count occurrences of each search term
            count = title_lower.count(term.lower())
            # Weight longer terms higher
            weight = len(term) / 3
            score += count * weight
        
        return score
    
    def get_suggestions(self, df, partial_query, limit=5):
        """Get search suggestions based on partial query"""
        if df is None or df.empty or not partial_query:
            return []
        
        # Extract unique words from titles
        all_titles = ' '.join(df['Title'].dropna().values)
        words = re.findall(r'\w+', all_titles.lower())
        
        # Find words that start with the partial query
        suggestions = [word for word in set(words) 
                      if word.startswith(partial_query.lower()) 
                      and len(word) > len(partial_query)]
        
        # Sort by frequency and return top suggestions
        word_counts = {word: words.count(word) for word in suggestions}
        sorted_suggestions = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [word for word, count in sorted_suggestions[:limit]]