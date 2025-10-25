import re
from typing import Dict, List

class RelevanceScorer:
    """Relevance scoring service for articles"""
    
    def __init__(self):
        # Keywords that indicate high relevance to Sean McVay
        self.mcvay_keywords = [
            'sean mcvay', 'mcvay', 'rams coach', 'los angeles rams',
            'nfl coach', 'rams head coach', 'mcvay rams'
        ]
        
        # Keywords that indicate relevance to coaching/football
        self.football_keywords = [
            'coach', 'coaching', 'football', 'nfl', 'rams', 'team',
            'game', 'playoff', 'super bowl', 'quarterback', 'offense',
            'defense', 'strategy', 'playbook', 'win', 'loss', 'record'
        ]
        
        # Keywords that indicate relevance to Sean McVay's personal life
        self.personal_keywords = [
            'wife', 'family', 'personal', 'life', 'marriage', 'relationship',
            'offseason', 'vacation', 'personal life', 'private'
        ]
    
    def calculate_relevance_score(self, title: str, summary: str = None, content: str = None, entity_name: str = "Sean McVay") -> float:
        """
        Calculate relevance score for an article
        
        Args:
            title (str): Article title
            summary (str, optional): Article summary
            content (str, optional): Article content
            entity_name (str): Name of the entity being tracked
            
        Returns:
            float: Relevance score between 0.0 and 1.0
        """
        if not title:
            return 0.0
        
        # Combine all text for analysis
        text_parts = [title.lower()]
        if summary:
            text_parts.append(summary.lower())
        if content:
            text_parts.append(content[:2000].lower())  # Limit content length
        
        combined_text = ' '.join(text_parts)
        
        # Calculate different relevance factors
        entity_mentions = self._count_entity_mentions(combined_text, entity_name)
        keyword_score = self._calculate_keyword_score(combined_text)
        title_relevance = self._calculate_title_relevance(title.lower(), entity_name)
        
        # Weight the factors
        final_score = (
            entity_mentions * 0.4 +
            keyword_score * 0.3 +
            title_relevance * 0.3
        )
        
        # Ensure score is between 0 and 1
        return min(max(final_score, 0.0), 1.0)
    
    def _count_entity_mentions(self, text: str, entity_name: str) -> float:
        """Count mentions of the entity in the text"""
        entity_variations = [
            entity_name.lower(),
            entity_name.lower().replace(' ', ''),
            entity_name.lower().replace(' ', '-'),
        ]
        
        # Add common variations for Sean McVay
        if 'sean mcvay' in entity_name.lower():
            entity_variations.extend(['mcvay', 'sean', 'coach mcvay'])
        
        total_mentions = 0
        for variation in entity_variations:
            total_mentions += text.count(variation)
        
        # Normalize to 0-1 scale (more mentions = higher score, but cap at 1.0)
        return min(total_mentions / 5.0, 1.0)
    
    def _calculate_keyword_score(self, text: str) -> float:
        """Calculate score based on relevant keywords"""
        score = 0.0
        
        # Check for McVay-specific keywords
        for keyword in self.mcvay_keywords:
            if keyword in text:
                score += 0.3
        
        # Check for football-related keywords
        for keyword in self.football_keywords:
            if keyword in text:
                score += 0.1
        
        # Check for personal life keywords
        for keyword in self.personal_keywords:
            if keyword in text:
                score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_title_relevance(self, title: str, entity_name: str) -> float:
        """Calculate relevance based on title"""
        # Higher score if entity name is in title
        if entity_name.lower() in title:
            return 1.0
        
        # Check for partial matches
        entity_words = entity_name.lower().split()
        title_words = title.split()
        
        # Count how many entity words appear in title
        matches = sum(1 for word in entity_words if word in title_words)
        
        if len(entity_words) > 0:
            return matches / len(entity_words)
        
        return 0.0
    
    def is_relevant(self, title: str, summary: str = None, content: str = None, 
                   entity_name: str = "Sean McVay", threshold: float = 0.3) -> bool:
        """
        Determine if an article is relevant enough to store
        
        Args:
            title (str): Article title
            summary (str, optional): Article summary
            content (str, optional): Article content
            entity_name (str): Name of the entity being tracked
            threshold (float): Minimum relevance score to consider relevant
            
        Returns:
            bool: True if article is relevant, False otherwise
        """
        score = self.calculate_relevance_score(title, summary, content, entity_name)
        return score >= threshold 