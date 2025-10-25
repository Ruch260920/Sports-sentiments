from textblob import TextBlob
import re

class SentimentAnalyzer:
    """Sentiment analysis service using TextBlob"""
    
    def __init__(self):
        self.analyzer = TextBlob
    
    def analyze_sentiment(self, text):
        """
        Analyze sentiment of given text
        
        Args:
            text (str): Text to analyze
            
        Returns:
            dict: Contains sentiment_score and sentiment_label
        """
        if not text or not isinstance(text, str):
            return {
                'sentiment_score': 0.0,
                'sentiment_label': 'neutral'
            }
        
        # Clean the text
        cleaned_text = self._clean_text(text)
        
        # Analyze sentiment
        blob = self.analyzer(cleaned_text)
        sentiment_score = blob.sentiment.polarity
        
        # Determine label
        if sentiment_score > 0.1:
            sentiment_label = 'positive'
        elif sentiment_score < -0.1:
            sentiment_label = 'negative'
        else:
            sentiment_label = 'neutral'
        
        return {
            'sentiment_score': round(sentiment_score, 3),
            'sentiment_label': sentiment_label
        }
    
    def _clean_text(self, text):
        """Clean text for sentiment analysis"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\!\?]', '', text)
        
        return text.strip()
    
    def analyze_article(self, title, summary=None, content=None):
        """
        Analyze sentiment of an article combining title, summary, and content
        
        Args:
            title (str): Article title
            summary (str, optional): Article summary
            content (str, optional): Article content
            
        Returns:
            dict: Contains sentiment_score and sentiment_label
        """
        # Combine all text fields
        text_parts = [title]
        if summary:
            text_parts.append(summary)
        if content:
            # Use first 1000 characters of content to avoid too long text
            text_parts.append(content[:1000])
        
        combined_text = ' '.join(text_parts)
        
        return self.analyze_sentiment(combined_text) 