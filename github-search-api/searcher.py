from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import concurrent.futures

class SearchEngine:
    def __init__(self):
        self.ddgs = DDGS()
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    def search(self, query, page=1):
        """Ana arama fonksiyonu"""
        all_results = []
        
        # Paralel arama yap (daha hızlı)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(self.search_duckduckgo, query),
                executor.submit(self.search_brave, query),
                executor.submit(self.search_qwant, query)
            ]
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    results = future.result(timeout=10)
                    all_results.extend(results)
                except Exception as e:
                    print(f"Arama hatasi: {e}")
        
        # Aynı URL'leri temizle
        unique_results = {}
        for r in all_results:
            url = r['url']
            if url and url not in unique_results:
                unique_results[url] = r
        
        # Sayfalama
        results_per_page = 10
        start = (page - 1) * results_per_page
        end = start + results_per_page
        final_results = list(unique_results.values())
        
        return final_results[start:end]
    
    def search_duckduckgo(self, query):
        """DuckDuckGo ile arama"""
        results = []
        try:
            ddg_results = self.ddgs.text(
                query,
                region='wt-wt',
                safesearch='moderate',
                max_results=15
            )
            
            for r in ddg_results:
                results.append({
                    'title': r.get('title', ''),
                    'url': r.get('href', ''),
                    'snippet': r.get('body', '')[:300],
                    'source': 'DuckDuckGo'
                })
        except Exception as e:
            print(f"DuckDuckGo hatasi: {e}")
        
        return results
    
    def search_brave(self, query):
        """Brave Search ile arama"""
        results = []
        try:
            url = f"https://search.brave.com/search?q={quote(query)}"
            headers = {'User-Agent': self.user_agent}
            response = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for item in soup.select('.snippet')[:10]:
                title_elem = item.select_one('h2 a')
                if title_elem:
                    results.append({
                        'title': title_elem.get_text(),
                        'url': title_elem.get('href', ''),
                        'snippet': item.get_text()[:300],
                        'source': 'Brave'
                    })
        except Exception as e:
            print(f"Brave hatasi: {e}")
        
        return results
    
    def search_qwant(self, query):
        """Qwant API ile arama"""
        results = []
        try:
            url = f"https://api.qwant.com/v3/search/web"
            params = {
                'q': query,
                'count': 10,
                't': 'web',
                'safesearch': 1,
                'locale': 'tr_TR'
            }
            headers = {'User-Agent': self.user_agent}
            
            response = requests.get(url, params=params, headers=headers, timeout=5)
            data = response.json()
            
            for item in data.get('data', {}).get('result', {}).get('items', []):
                results.append({
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'snippet': item.get('desc', '')[:300],
                    'source': 'Qwant'
                })
        except Exception as e:
            print(f"Qwant hatasi: {e}")
        
        return results
