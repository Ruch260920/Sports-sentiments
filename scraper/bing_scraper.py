import requests
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class BingScraper:
    """Bing search scraper for finding news articles"""
    
    def __init__(self):
        self.api_key = os.getenv('BING_API_KEY')
        self.endpoint = "https://api.bing.microsoft.com/v7.0/news/search"
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({
                'Ocp-Apim-Subscription-Key': self.api_key
            })
    
    def search_news(self, query: str, count: int = 50, 
                   freshness: str = "Day") -> List[Dict]:
        """
        Search for news articles using Bing News API
        
        Args:
            query (str): Search query
            count (int): Number of results to return
            freshness (str): Time filter (Day, Week, Month)
            
        Returns:
            List[Dict]: List of article dictionaries
        """
        if not self.api_key:
            print("Bing API key not found. Using fallback search method.")
            return self._fallback_search(query, count)
        
        try:
            params = {
                'q': query,
                'count': count,
                'freshness': freshness,
                'mkt': 'en-US',
                'safeSearch': 'Moderate'
            }
            
            response = self.session.get(self.endpoint, params=params)
            response.raise_for_status()
            
            data = response.json()
            articles = []
            
            if 'value' in data:
                for item in data['value']:
                    article = self._parse_bing_article(item)
                    if article:
                        articles.append(article)
            
            return articles
            
        except Exception as e:
            print(f"Error searching Bing News: {e}")
            return self._fallback_search(query, count)
    
    def _parse_bing_article(self, item: Dict) -> Optional[Dict]:
        """Parse article data from Bing API response"""
        try:
            # Extract basic info
            title = item.get('name', '')
            description = item.get('description', '')
            url = item.get('url', '')
            
            if not title or not url:
                return None
            
            # Extract date
            published_date = None
            if 'datePublished' in item:
                try:
                    published_date = datetime.fromisoformat(
                        item['datePublished'].replace('Z', '+00:00')
                    )
                except:
                    pass
            
            # Extract source info
            source_name = "Unknown"
            if 'provider' in item and len(item['provider']) > 0:
                source_name = item['provider'][0].get('name', 'Unknown')
            
            return {
                'title': title,
                'summary': description,
                'url': url,
                'published_date': published_date,
                'source_name': source_name,
                'domain': self._extract_domain(url)
            }
            
        except Exception as e:
            print(f"Error parsing Bing article: {e}")
            return None
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return ""
    
    def _fallback_search(self, query: str, count: int) -> List[Dict]:
        """Fallback search method when API is not available"""
        # This would implement a basic web scraping fallback
        # For now, return empty list
        print("Fallback search not implemented. Please provide Bing API key.")
        return []
    
    def search_entity_news(self, entity_name: str, days_back: int = 7) -> List[Dict]:
        """
        Search for news about a specific entity
        
        Args:
            entity_name (str): Name of the entity to search for
            days_back (int): Number of days back to search
            
        Returns:
            List[Dict]: List of relevant articles
        """
        articles = []
        
        # Generate search queries
        queries = self._generate_entity_queries(entity_name)
        
        for query in queries:
            try:
                query_articles = self.search_news(query, count=20)
                articles.extend(query_articles)
                
                # Remove duplicates based on URL
                seen_urls = set()
                unique_articles = []
                for article in articles:
                    if article['url'] not in seen_urls:
                        seen_urls.add(article['url'])
                        unique_articles.append(article)
                
                articles = unique_articles
                
            except Exception as e:
                print(f"Error searching for query '{query}': {e}")
                continue
        
        # Filter by date if specified
        if days_back > 0:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            articles = [
                article for article in articles 
                if not article.get('published_date') or 
                article['published_date'] >= cutoff_date
            ]
        
        return articles
    
    def _generate_entity_queries(self, entity_name: str) -> List[str]:
        """Generate search queries for an entity"""
        queries = [
            f'"{entity_name}"',
            f'"{entity_name}" news',
            f'"{entity_name}" latest'
        ]
        
        # Add specific queries for Sean McVay
        if 'sean mcvay' in entity_name.lower():
            queries.extend([
                '"Sean McVay" coach',
                '"Sean McVay" Rams',
                '"Sean McVay" NFL',
                'McVay coach',
                'McVay Rams'
            ])
        
        return queries 