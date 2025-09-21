from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
import json
from services.search_service import SearchService
from services.pdf_processor import PDFProcessor

app = Flask(__name__, 
           template_folder='templates',
           static_folder='static')

# Initialize services
search_service = SearchService()
pdf_processor = PDFProcessor()

# Load publications data
publications_df = None

def load_data():
    """Load publications from CSV file"""
    global publications_df
    import traceback
    try:
        data_path = os.path.join('data', 'SB_publication_PMC.csv')
        publications_df = pd.read_csv(data_path)
        print(f"Loaded {len(publications_df)} publications")
        return True
    except Exception as e:
        print(f"Error loading data: {e}")
        traceback.print_exc()
        return False

@app.route('/')
def index():
    """Home page with search interface"""
    return render_template('index.html')

@app.route('/search')
def search():
    """Search publications"""
    query = request.args.get('q', '').strip()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    if not query:
        return render_template('search_results.html', 
                             results=[], 
                             query="", 
                             total=0, 
                             page=1, 
                             total_pages=0)
    
    # Search publications
    results = search_service.search(publications_df, query, page, per_page)
    
    return render_template('search_results.html',
                         results=results['publications'],
                         query=query,
                         total=results['total'],
                         page=page,
                         total_pages=results['total_pages'])

@app.route('/publication/<int:pub_id>')
def publication_detail(pub_id):
    """Publication detail page"""
    if publications_df is None or pub_id >= len(publications_df):
        return "Publication not found", 404
    
    # Get publication data
    pub = publications_df.iloc[pub_id]
    
    # Check if we have cached analysis
    cache_file = f"data/cache/pub_{pub_id}_analysis.json"
    analysis_data = None
    
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            analysis_data = json.load(f)
    
    return render_template('publication.html',
                         publication=pub,
                         pub_id=pub_id,
                         analysis=analysis_data)

@app.route('/api/analyze/<int:pub_id>')
def analyze_publication(pub_id):
    """API endpoint to analyze a publication"""
    if publications_df is None or pub_id >= len(publications_df):
        return jsonify({"error": "Publication not found"}), 404
    
    pub = publications_df.iloc[pub_id]
    
    try:
        # Process PDF and extract text
        result = pdf_processor.process_publication(pub, pub_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/search')
def api_search():
    """API endpoint for search"""
    query = request.args.get('q', '').strip()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    if not query:
        return jsonify({"publications": [], "total": 0, "total_pages": 0})
    
    results = search_service.search(publications_df, query, page, per_page)
    return jsonify(results)

if __name__ == '__main__':
    # Load data on startup
    if load_data():
        app.run(debug=True, port=5000)
    else:
        print("Failed to load data. Please check your CSV file.")