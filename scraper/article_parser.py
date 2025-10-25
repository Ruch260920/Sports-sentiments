import re
from typing import List, Dict, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from services.utilities import clean_text, extract_domain, parse_date

class ArticleParser:
    """Parser for extracting article data from HTML content"""
    
    def __init__(self):
        self.title_selectors = [
            'h1', 'h2', '.headline', '.title', '.article-title',
            '[class*="title"]', '[class*="headline"]'
        ]
        
        self.summary_selectors = [
            '.summary', '.excerpt', '.description', '.article-summary',
            '[class*="summary"]', '[class*="excerpt"]'
        ]
        
        self.date_selectors = [
            '.date', '.published-date', '.article-date', '.timestamp',
            '[class*="date"]', '[datetime]'
        ]
    
    def parse_source_page(self, html_content: str, source_name: str, 
                         query: str) -> List[Dict]:
        """
        Parse articles from a source page HTML
        
        Args:
            html_content (str): HTML content of the page
            source_name (str): Name of the source
            query (str): Search query used
            
        Returns:
            List[Dict]: List of article dictionaries
        """
        articles = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find article links
        article_links = self._find_article_links(soup, query)
        
        for link in article_links[:20]:  # Limit to first 20 articles
            try:
                article_data = self._parse_article_from_link(link, source_name)
                if article_data:
                    articles.append(article_data)
            except Exception as e:
                print(f"Error parsing article link: {e}")
                continue
        
        return articles
    
    def _find_article_links(self, soup: BeautifulSoup, query: str) -> List:
        """Find article links in the HTML"""
        links = []
        
        # Common patterns for article links
        link_patterns = [
            'a[href*="/article"]',
            'a[href*="/news"]',
            'a[href*="/story"]',
            'a[href*="/sports"]',
            '.article a',
            '.news-item a',
            '.story-link'
        ]
        
        for pattern in link_patterns:
            found_links = soup.select(pattern)
            links.extend(found_links)
        
        # Filter links that might be relevant to the query
        relevant_links = []
        query_terms = query.lower().replace('"', '').split()
        
        for link in links:
            href = link.get('href', '')
            text = link.get_text().lower()
            
            # Check if link text or URL contains query terms
            if any(term in href.lower() or term in text for term in query_terms):
                relevant_links.append(link)
        
        return relevant_links
    
    def _parse_article_from_link(self, link, source_name: str) -> Optional[Dict]:
        """Parse article data from a link element"""
        href = link.get('href', '')
        if not href:
            return None
        
        # Make URL absolute if it's relative
        if href.startswith('/'):
            href = f"https://{source_name.lower().replace(' ', '')}.com{href}"
        
        # Extract basic info from the link
        title = clean_text(link.get_text())
        if not title:
            return None
        
        # Try to find summary in nearby elements
        summary = self._extract_summary_from_context(link)
        
        # Try to find date in nearby elements
        published_date = self._extract_date_from_context(link)
        
        return {
            'title': title,
            'summary': summary,
            'url': href,
            'published_date': published_date,
            'source_name': source_name,
            'domain': extract_domain(href)
        }
    
    def _extract_summary_from_context(self, element) -> Optional[str]:
        """Extract summary from the context around the element"""
        # Look for summary in parent or sibling elements
        parent = element.parent
        if parent:
            # Check for summary in parent
            for selector in self.summary_selectors:
                summary_elem = parent.select_one(selector)
                if summary_elem:
                    return clean_text(summary_elem.get_text())
            
            # Check for summary in siblings
            for sibling in parent.find_all(['p', 'div'], limit=3):
                text = clean_text(sibling.get_text())
                if len(text) > 50 and len(text) < 300:  # Reasonable summary length
                    return text
        
        return None
    
    def _extract_date_from_context(self, element) -> Optional[datetime]:
        """Extract date from the context around the element"""
        # Look for date in parent or sibling elements
        parent = element.parent
        if parent:
            # Check for date in parent
            for selector in self.date_selectors:
                date_elem = parent.select_one(selector)
                if date_elem:
                    date_text = date_elem.get_text()
                    parsed_date = parse_date(date_text)
                    if parsed_date:
                        return parsed_date
            
            # Check for date in siblings
            for sibling in parent.find_all(['span', 'time'], limit=3):
                date_text = sibling.get_text()
                parsed_date = parse_date(date_text)
                if parsed_date:
                    return parsed_date
        
        return None
    
    def parse_article_html(self, html_content: str, url: str) -> Optional[Dict]:
        """
        Parse article data from HTML content
        
        Args:
            html_content (str): HTML content of the article
            url (str): URL of the article
            
        Returns:
            Optional[Dict]: Article data or None if parsing fails
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract title
            title = self._extract_title(soup)
            if not title:
                return None
            
            # Extract summary
            summary = self._extract_summary(soup)
            
            # Extract content
            content = self._extract_content(soup)
            
            # Extract published date
            published_date = self._extract_published_date(soup)
            
            return {
                'title': title,
                'summary': summary,
                'content': content,
                'url': url,
                'published_date': published_date,
                'source_name': extract_domain(url),
                'domain': extract_domain(url)
            }
            
        except Exception as e:
            print(f"Error parsing article HTML: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article title"""
        # Try different selectors for title
        for selector in self.title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = clean_text(title_elem.get_text())
                if title and len(title) > 10:
                    return title
        
        # Fallback to first h1
        h1 = soup.find('h1')
        if h1:
            title = clean_text(h1.get_text())
            if title and len(title) > 10:
                return title
        
        return None
    
    def _extract_summary(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article summary"""
        for selector in self.summary_selectors:
            summary_elem = soup.select_one(selector)
            if summary_elem:
                summary = clean_text(summary_elem.get_text())
                if summary and len(summary) > 20:
                    return summary
        
        return None
    
    def _extract_content(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article content"""
        # Try to find main content area
        content_selectors = [
            '.article-content', '.content', '.post-content',
            '.entry-content', '.article-body', '.story-body'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                content = clean_text(content_elem.get_text())
                if content and len(content) > 100:
                    return content
        
        # Fallback to all paragraphs
        paragraphs = soup.find_all('p')
        if paragraphs:
            content = ' '.join([clean_text(p.get_text()) for p in paragraphs])
            if content and len(content) > 100:
                return content
        
        return None
    
    def _extract_published_date(self, soup: BeautifulSoup) -> Optional[datetime]:
        """Extract published date"""
        for selector in self.date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                date_text = date_elem.get_text()
                parsed_date = parse_date(date_text)
                if parsed_date:
                    return parsed_date
        
        return None 