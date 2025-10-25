from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Entity(Base):
    """Entity table to store people/companies we're tracking"""
    __tablename__ = "entities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Twitter-specific fields
    twitter_username = Column(String(100), nullable=True, unique=True, index=True)
    twitter_user_id = Column(String(100), nullable=True, index=True)
    is_twitter_tracked = Column(Boolean, default=False)
    
    # Relationships
    articles = relationship("Article", back_populates="entity")
    tweets = relationship("Tweet", back_populates="entity")

class Source(Base):
    """Source table to store news sources"""
    __tablename__ = "sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    domain = Column(String(255), nullable=True)
    url = Column(String(500), nullable=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    articles = relationship("Article", back_populates="source")

class Article(Base):
    """Article table to store scraped articles"""
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=True)
    url = Column(String(1000), unique=True, nullable=False)
    content = Column(Text, nullable=True)
    published_date = Column(DateTime(timezone=True), nullable=True)
    scraped_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Foreign Keys
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)
    
    # Analysis fields
    relevance_score = Column(Float, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    sentiment_label = Column(String(50), nullable=True)
    
    # Relationships
    entity = relationship("Entity", back_populates="articles")
    source = relationship("Source", back_populates="articles")

class Tweet(Base):
    """Tweet table to store tweets from twitterapi.io webhooks"""
    __tablename__ = "tweets"
    
    id = Column(Integer, primary_key=True, index=True)
    tweet_id = Column(String(100), unique=True, index=True, nullable=False)  # Twitter's tweet ID
    text = Column(Text, nullable=False)
    author_username = Column(String(100), nullable=False, index=True)
    author_user_id = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    received_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Twitter metadata
    retweet_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    reply_count = Column(Integer, default=0)
    quote_count = Column(Integer, default=0)
    is_retweet = Column(Boolean, default=False)
    is_quote = Column(Boolean, default=False)
    is_reply = Column(Boolean, default=False)
    
    # Raw Twitter data for additional processing
    raw_data = Column(JSON, nullable=True)
    
    # Foreign Keys
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=True)  # Nullable for tweets not yet classified
    
    # Analysis fields
    relevance_score = Column(Float, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    sentiment_label = Column(String(50), nullable=True)
    
    # Relationships
    entity = relationship("Entity", back_populates="tweets")

class TwitterWebhook(Base):
    """Table to track webhook subscriptions and their status"""
    __tablename__ = "twitter_webhooks"
    
    id = Column(Integer, primary_key=True, index=True)
    webhook_id = Column(String(100), unique=True, nullable=False)  # twitterapi.io webhook ID
    webhook_url = Column(String(500), nullable=False)
    target_username = Column(String(100), nullable=False, index=True)
    target_user_id = Column(String(100), nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), nullable=True)
    failure_count = Column(Integer, default=0)
    
    # Webhook configuration
    events = Column(JSON, nullable=True)  # Array of events to listen for
    webhook_metadata = Column(JSON, nullable=True)  # Additional webhook metadata 