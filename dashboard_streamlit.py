#!/usr/bin/env python3
"""
Streamlit Dashboard for Sean McVay News Scraping Pipeline

This provides an interactive web interface for monitoring and analyzing
scraped news articles with real-time charts and filtering capabilities.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import time
from sqlalchemy.orm import sessionmaker
from models.database import engine, get_db
from models.models import Entity, Article, Source
from services.sentiment_analyzer import SentimentAnalyzer
from services.relevance_scorer import RelevanceScorer

# Page configuration
st.set_page_config(
    page_title="Sean McVay News Dashboard",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .stAlert {
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_database_data():
    """Load data from database with caching"""
    try:
        db = next(get_db())
        
        # Get basic counts
        total_articles = db.query(Article).count()
        total_sources = db.query(Source).count()
        total_entities = db.query(Entity).count()
        
        # Get recent articles (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        recent_articles = db.query(Article).filter(
            Article.scraped_date >= week_ago
        ).count()
        
        # Get articles with sentiment data
        articles_data = []
        articles = db.query(Article).join(Source).join(Entity).order_by(
            Article.scraped_date.desc()
        ).limit(1000).all()
        
        for article in articles:
            articles_data.append({
                'id': article.id,
                'title': article.title,
                'summary': article.summary,
                'url': article.url,
                'published_date': article.published_date,
                'scraped_date': article.scraped_date,
                'relevance_score': article.relevance_score,
                'sentiment_score': article.sentiment_score,
                'sentiment_label': article.sentiment_label,
                'source_name': article.source.name,
                'entity_name': article.entity.name
            })
        
        # Get sources data
        sources_data = []
        sources = db.query(Source).all()
        for source in sources:
            article_count = db.query(Article).filter(
                Article.source_id == source.id
            ).count()
            sources_data.append({
                'name': source.name,
                'domain': source.domain,
                'article_count': article_count,
                'is_verified': source.is_verified
            })
        
        db.close()
        
        return {
            'total_articles': total_articles,
            'total_sources': total_sources,
            'total_entities': total_entities,
            'recent_articles': recent_articles,
            'articles_df': pd.DataFrame(articles_data),
            'sources_df': pd.DataFrame(sources_data)
        }
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

def create_sentiment_timeline_chart(df):
    """Create sentiment timeline chart"""
    if df.empty:
        return go.Figure()
    
    # Group by date and sentiment
    df['date'] = pd.to_datetime(df['scraped_date']).dt.date
    sentiment_timeline = df.groupby(['date', 'sentiment_label']).size().reset_index(name='count')
    
    # Pivot for plotting
    pivot_df = sentiment_timeline.pivot(index='date', columns='sentiment_label', values='count').fillna(0)
    
    fig = go.Figure()
    
    colors = {'positive': '#28a745', 'negative': '#dc3545', 'neutral': '#6c757d'}
    
    for sentiment in ['positive', 'negative', 'neutral']:
        if sentiment in pivot_df.columns:
            fig.add_trace(go.Scatter(
                x=pivot_df.index,
                y=pivot_df[sentiment],
                mode='lines+markers',
                name=sentiment.title(),
                line=dict(color=colors.get(sentiment, '#000000')),
                marker=dict(size=8)
            ))
    
    fig.update_layout(
        title="Sentiment Timeline",
        xaxis_title="Date",
        yaxis_title="Number of Articles",
        hovermode='x unified',
        height=400
    )
    
    return fig

def create_source_distribution_chart(sources_df):
    """Create source distribution chart"""
    if sources_df.empty:
        return go.Figure()
    
    fig = px.pie(
        sources_df, 
        values='article_count', 
        names='name',
        title="Article Distribution by Source",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_layout(height=400)
    return fig

def create_relevance_distribution_chart(df):
    """Create relevance score distribution chart"""
    if df.empty or 'relevance_score' not in df.columns:
        return go.Figure()
    
    # Filter out None values
    relevance_data = df[df['relevance_score'].notna()]['relevance_score']
    
    if relevance_data.empty:
        return go.Figure()
    
    fig = px.histogram(
        x=relevance_data,
        nbins=20,
        title="Relevance Score Distribution",
        labels={'x': 'Relevance Score', 'y': 'Number of Articles'}
    )
    
    fig.update_layout(height=400)
    return fig

def create_sentiment_pie_chart(df):
    """Create sentiment distribution pie chart"""
    if df.empty or 'sentiment_label' not in df.columns:
        return go.Figure()
    
    sentiment_counts = df['sentiment_label'].value_counts()
    
    fig = px.pie(
        values=sentiment_counts.values,
        names=sentiment_counts.index,
        title="Sentiment Distribution",
        color_discrete_map={
            'positive': '#28a745',
            'negative': '#dc3545', 
            'neutral': '#6c757d'
        }
    )
    
    fig.update_layout(height=400)
    return fig

def main():
    """Main Streamlit app"""
    
    # Header
    st.markdown('<h1 class="main-header">📰 Sean McVay News Dashboard</h1>', unsafe_allow_html=True)
    
    # Load data
    data = load_database_data()
    
    if data is None:
        st.error("Failed to load data from database. Please check your database connection.")
        return
    
    # Sidebar filters
    st.sidebar.header("🔍 Filters")
    
    # Date range filter
    if not data['articles_df'].empty:
        # Convert timezone-aware dates to date objects for the widget
        min_date = data['articles_df']['scraped_date'].min().date()
        max_date = data['articles_df']['scraped_date'].max().date()
        
        date_range = st.sidebar.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
    
    # Sentiment filter
    sentiment_filter = st.sidebar.multiselect(
        "Sentiment",
        options=['positive', 'negative', 'neutral'],
        default=['positive', 'negative', 'neutral']
    )
    
    # Source filter
    if not data['sources_df'].empty:
        source_options = data['sources_df']['name'].tolist()
        source_filter = st.sidebar.multiselect(
            "Source",
            options=source_options,
            default=source_options
        )
    
    # Search filter
    search_query = st.sidebar.text_input("Search Articles", placeholder="Enter keywords...")
    
    # Apply filters
    filtered_df = data['articles_df'].copy()
    
    if not filtered_df.empty:
        # Date filter
        if len(date_range) == 2:
            # Convert date_range to timezone-aware timestamps
            start_date = pd.Timestamp(date_range[0]).tz_localize('UTC')
            end_date = pd.Timestamp(date_range[1]).tz_localize('UTC')
            
            filtered_df = filtered_df[
                (filtered_df['scraped_date'] >= start_date) &
                (filtered_df['scraped_date'] <= end_date)
            ]
        
        # Sentiment filter
        filtered_df = filtered_df[filtered_df['sentiment_label'].isin(sentiment_filter)]
        
        # Source filter
        if 'source_filter' in locals():
            filtered_df = filtered_df[filtered_df['source_name'].isin(source_filter)]
        
        # Search filter
        if search_query:
            mask = (
                filtered_df['title'].str.contains(search_query, case=False, na=False) |
                filtered_df['summary'].str.contains(search_query, case=False, na=False)
            )
            filtered_df = filtered_df[mask]
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📊 Total Articles",
            value=f"{data['total_articles']:,}",
            delta=f"+{data['recent_articles']} recent"
        )
    
    with col2:
        st.metric(
            label="🕒 Recent Articles (7 days)",
            value=f"{data['recent_articles']:,}"
        )
    
    with col3:
        st.metric(
            label="🌐 Sources",
            value=f"{data['total_sources']:,}"
        )
    
    with col4:
        st.metric(
            label="👤 Entities",
            value=f"{data['total_entities']:,}"
        )
    
    # Charts row 1
    col1, col2 = st.columns(2)
    
    with col1:
        sentiment_timeline = create_sentiment_timeline_chart(filtered_df)
        st.plotly_chart(sentiment_timeline, use_container_width=True)
    
    with col2:
        source_distribution = create_source_distribution_chart(data['sources_df'])
        st.plotly_chart(source_distribution, use_container_width=True)
    
    # Charts row 2
    col1, col2 = st.columns(2)
    
    with col1:
        relevance_distribution = create_relevance_distribution_chart(filtered_df)
        st.plotly_chart(relevance_distribution, use_container_width=True)
    
    with col2:
        sentiment_pie = create_sentiment_pie_chart(filtered_df)
        st.plotly_chart(sentiment_pie, use_container_width=True)
    
    # Articles table
    st.header("📋 Recent Articles")
    
    if not filtered_df.empty:
        # Display articles in a nice format
        for _, article in filtered_df.head(20).iterrows():
            with st.expander(f"📰 {article['title'][:100]}..."):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Title:** {article['title']}")
                    if pd.notna(article['summary']):
                        st.write(f"**Summary:** {article['summary']}")
                    st.write(f"**Source:** {article['source_name']}")
                    st.write(f"**Published:** {article['published_date']}")
                    st.write(f"**Scraped:** {article['scraped_date']}")
                
                with col2:
                    # Sentiment badge
                    sentiment_color = {
                        'positive': 'green',
                        'negative': 'red',
                        'neutral': 'gray'
                    }.get(article['sentiment_label'], 'gray')
                    
                    st.markdown(f"""
                    <div style="background-color: {sentiment_color}; color: white; padding: 0.5rem; border-radius: 0.25rem; text-align: center;">
                        {article['sentiment_label'].title()}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Relevance score
                    if pd.notna(article['relevance_score']):
                        relevance_percent = article['relevance_score'] * 100
                        st.metric("Relevance", f"{relevance_percent:.1f}%")
                    
                    # Link to original article
                    st.markdown(f"[🔗 View Original]({article['url']})")
        
        # Show total count
        st.info(f"Showing {len(filtered_df)} articles (filtered from {len(data['articles_df'])} total)")
    else:
        st.warning("No articles found matching the current filters.")
    
    # Auto-refresh
    st.sidebar.header("🔄 Auto-refresh")
    auto_refresh = st.sidebar.checkbox("Enable auto-refresh", value=True)
    
    if auto_refresh:
        st.sidebar.write("Data refreshes every 5 minutes")
        time.sleep(1)  # Small delay to prevent excessive refreshing
        st.experimental_rerun()

if __name__ == "__main__":
    main() 