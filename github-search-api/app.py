from flask import Flask, request, jsonify
from flask_cors import CORS
from searcher import SearchEngine
import time

app = Flask(__name__)
CORS(app)

# Arama motorunu başlat
search_engine = SearchEngine()

@app.route('/')
def home():
    return jsonify({
        'name': 'Search API',
        'version': '1.0',
        'status': 'running',
        'endpoints': {
            '/search': 'GET - Arama yapar (q=kelime)',
            '/health': 'GET - Sağlık kontrolü'
        }
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time()
    })

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({
            'error': 'Arama sorgusu gerekli',
            'results': []
        }), 400
    
    page = int(request.args.get('page', 1))
    
    # Arama yap
    results = search_engine.search(query, page)
    
    return jsonify({
        'query': query,
        'page': page,
        'total': len(results),
        'results': results,
        'timestamp': time.time()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=False)
