from flask import Flask, request, jsonify
from flask_cors import CORS
from searcher import SearchEngine
from cachetools import TTLCache
import time

app = Flask(__name__)
CORS(app)  # Herkese açık API

# Önbellek (5 dakika)
cache = TTLCache(maxsize=100, ttl=300)
search_engine = SearchEngine()

@app.route('/')
def home():
    return jsonify({
        'name': 'GitHub Search API',
        'version': '1.0',
        'status': 'online',
        'endpoints': {
            '/search': 'GET - Arama yapar',
            '/health': 'GET - Sağlık kontrolü'
        }
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': time.time()})

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    page = int(request.args.get('page', 1))
    
    if not query:
        return jsonify({'error': 'Sorgu gerekli'}), 400
    
    # Önbellek kontrolü
    cache_key = f"{query}:{page}"
    if cache_key in cache:
        return jsonify({
            'query': query,
            'page': page,
            'results': cache[cache_key],
            'cached': True,
            'source': 'GitHub API'
        })
    
    # Gerçek arama
    results = search_engine.search(query, page)
    
    # Önbelleğe al
    cache[cache_key] = results
    
    return jsonify({
        'query': query,
        'page': page,
        'results': results,
        'cached': False,
        'source': 'GitHub API',
        'total': len(results)
    })

@app.route('/suggest')
def suggest():
    """Otomatik tamamlama önerileri"""
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify({'suggestions': []})
    
    suggestions = search_engine.get_suggestions(query)
    return jsonify({'suggestions': suggestions})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)