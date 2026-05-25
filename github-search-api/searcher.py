from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup
import concurrent.futures
from typing import List, Dict

class SearchEngine:
    def __init__(self):
        self.ddgs = DDGS()
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    def search(self, query: str, page: int = 1) -> List[Dict]:
        """Ana arama fonksiyonu - tüm kütüphaneler burada"""
        results = []
        
        # 1. DuckDuckGo ile ara (kütüphane kullanarak)
        try:
            ddg_results = self.search_duckduckgo(query, page)
            results.extend(ddg_results)
        except Exception as e:
            print(f"DuckDuckGo hatası: {e}")
        
        # 2. Brave Search API (opsiyonel)
        try:
            brave_results = self.search_brave(query, page)
            results.extend(brave_results)
        except:
            pass
        
        # 3. Yedek olarak Google (scraping)
        if len(results) < 5:
            try:
                google_results = self.search_google_fallback(query)
                results.extend(google_results)
            except:
                pass
        
        # Sonuçları birleştir ve sırala
        return self.merge_and_rank(results, query)
    
    def search_duckduckgo(self, query: str, page: int) -> List[Dict]:
        """DuckDuckGo kütüphanesi ile arama"""
        results = []
        
        # DuckDuckGo'da ara
        ddg_results = self.ddgs.text(
            query,
            region='tr-tr',
            safesearch='moderate',
            max_results=30
        )
        
        # Sayfalama
        start = (page - 1) * 10
        for i, item in enumerate(ddg_results):
            if i >= start and i < start + 10:
                results.append({
                    'title': item.get('title', ''),
                    'url': item.get('href', ''),
                    'snippet': item.get('body', '')[:300],
                    'source': 'DuckDuckGo',
                    'rank_score': 1.0
                })
        
        return results
    
    def search_brave(self, query: str, page: int) -> List[Dict]:
        """Brave Search API (ücretsiz)"""
        # Brave'in ücretsiz API'sini kullan
        url = f"https://api.search.brave.com/res/v1/web/search"
        headers = {
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip',
            'X-Subscription-Token': 'YOUR_BRAVE_API_KEY'  # Ücretsiz alabilirsin
        }
        params = {
            'q': query,
            'count': 10,
            'offset': (page - 1) * 10
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=5)
            data = response.json()
            
            results = []
            for item in data.get('web', {}).get('results', []):
                results.append({
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'snippet': item.get('description', '')[:300],
                    'source': 'Brave',
                    'rank_score': 0.8
                })
            return results
        except:
            return []
    
    def search_google_fallback(self, query: str) -> List[Dict]:
        """Google scraping (yedek) - BeautifulSoup kullanarak"""
        results = []
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        headers = {'User-Agent': self.user_agent}
        
        try:
            response = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for item in soup.select('div.g')[:5]:
                title_elem = item.select_one('h3')
                link_elem = item.select_one('a')
                snippet_elem = item.select_one('div.VwiC3b')
                
                if title_elem and link_elem:
                    results.append({
                        'title': title_elem.get_text(),
                        'url': link_elem.get('href', ''),
                        'snippet': snippet_elem.get_text()[:300] if snippet_elem else '',
                        'source': 'Google',
                        'rank_score': 0.9
                    })
        except:
            pass
        
        return results
    
    def merge_and_rank(self, results: List[Dict], query: str) -> List[Dict]:
        """Aynı URL'leri birleştir ve sırala"""
        url_map = {}
        
        for result in results:
            url = result['url']
            if url not in url_map:
                url_map[url] = result
                url_map[url]['score'] = result.get('rank_score', 0)
                url_map[url]['sources'] = [result['source']]
            else:
                url_map[url]['score'] += result.get('rank_score', 0)
                url_map[url]['sources'].append(result['source'])
        
        # Sorgu kelimelerine göre ek puan
        query_words = set(query.lower().split())
        for url, item in url_map.items():
            snippet_lower = item['snippet'].lower()
            title_lower = item['title'].lower()
            
            matches = sum(1 for word in query_words 
                         if word in snippet_lower or word in title_lower)
            item['score'] += matches * 0.5
        
        # Sırala
        sorted_results = sorted(url_map.values(), 
                               key=lambda x: x['score'], 
                               reverse=True)
        
        return sorted_results[:20]
    
    def get_suggestions(self, query: str) -> List[str]:
        """Otomatik tamamlama önerileri"""
        suggestions = []
        
        try:
            # DuckDuckGo'dan öneri al
            url = f"https://duckduckgo.com/ac/?q={query}&type=list"
            response = requests.get(url)
            data = response.json()
            suggestions = [item['phrase'] for item in data[:5]]
        except:
            # Basit öneriler
            suggestions = [
                f"{query} nedir",
                f"{query} nasıl yapılır",
                f"{query} fiyatları",
                f"{query} özellikleri"
            ]
        
        return suggestions