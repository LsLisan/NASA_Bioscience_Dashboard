from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
import json
import nltk

# -------------------------
# NLTK punkt setup
# -------------------------
NLTK_DATA_DIR = r'D:\nltk_data'  # change to any local folder you prefer
nltk.data.path.append(NLTK_DATA_DIR)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', download_dir=NLTK_DATA_DIR)

from services.search_service import SearchService
from services.pdf_processor import PDFProcessor
from services.uploadpdf import UploadPDFService

app = Flask(
    __name__,
    template_folder='templates',
    static_folder='static'
)

# Initialize services
search_service = SearchService()
pdf_processor = PDFProcessor()
upload_service = UploadPDFService()

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

# -------------------------
# Routes
# -------------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    if not query:
        return render_template(
            'search_results.html', 
            results=[], 
            query="", 
            total=0, 
            page=1, 
            total_pages=0
        )
    
    results = search_service.search(publications_df, query, page, per_page)
    
    return render_template(
        'search_results.html',
        results=results['publications'],
        query=query,
        total=results['total'],
        page=page,
        total_pages=results['total_pages']
    )

@app.route('/publication/<int:pub_id>')
def publication_detail(pub_id):
    if publications_df is None or pub_id >= len(publications_df):
        return "Publication not found", 404
    
    pub = publications_df.iloc[pub_id]
    cache_file = f"data/cache/pub_{pub_id}_analysis.json"
    analysis_data = None
    
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)
    
    return render_template(
        'publication.html',
        publication=pub,
        pub_id=pub_id,
        analysis=analysis_data
    )

@app.route('/api/analyze/<int:pub_id>')
def analyze_publication(pub_id):
    if publications_df is None or pub_id >= len(publications_df):
        return jsonify({"error": "Publication not found"}), 404
    
    pub = publications_df.iloc[pub_id]
    
    try:
        result = pdf_processor.process_publication(pub, pub_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/search')
def api_search():
    query = request.args.get('q', '').strip()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    if not query:
        return jsonify({"publications": [], "total": 0, "total_pages": 0})
    
    results = search_service.search(publications_df, query, page, per_page)
    return jsonify(results)

@app.route('/api/upload_pdf', methods=['POST'])
def upload_pdf():
    """Handle PDF upload and AI analysis"""
    try:
        file_key = 'file' if 'file' in request.files else 'pdf_file' if 'pdf_file' in request.files else None
        if not file_key:
            return jsonify({"error": "No file part in request"}), 400

        pdf_file = request.files[file_key]
        if pdf_file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        result = upload_service.handle_upload(pdf_file)
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route("/about")
def about():
    return render_template("about.html")


# -------------------------
# Main
# -------------------------
if __name__ == '__main__':
    if load_data():
        print("Starting Flask app on http://127.0.0.1:5000")
        app.run(debug=True, port=5000)
    else:
        print("Failed to load data. Please check your CSV file.")
