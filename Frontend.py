import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from typing import Dict, List, Any

def load_data():
    """Load all necessary data files"""
    data_dir = "data/NLP"
    
    # Load CSV files
    quarterly_summary = pd.read_csv(f"{data_dir}/nvda_quarterly_summary.csv")
    strategic_focuses = pd.read_csv(f"{data_dir}/nvda_strategic_focuses.csv")
    
    # Load transcript files
    transcripts = {}
    transcript_dir = "data/transcripts"
    for file in os.listdir(transcript_dir):
        if file.endswith('.txt'):
            quarter_year = file.split('_')[0:2]
            quarter_key = f"{quarter_year[0]} {quarter_year[1]}"
            with open(f"{transcript_dir}/{file}", 'r', encoding='utf-8') as f:
                transcripts[quarter_key] = f.read()
    
    # Load JSON analysis files
    analysis_data = {}
    for file in os.listdir(data_dir):
        if file.endswith('_analysis.json'):
            quarter_year = file.split('_')[0:2]
            quarter_key = f"{quarter_year[0]} {quarter_year[1]}"
            with open(f"{data_dir}/{file}", 'r', encoding='utf-8') as f:
                analysis_data[quarter_key] = json.load(f)
    
    return quarterly_summary, strategic_focuses, transcripts, analysis_data

def create_sentiment_chart(quarterly_summary):
    """Create sentiment visualization"""
    quarters = quarterly_summary['quarter'] + ' ' + quarterly_summary['year'].astype(str)
    
    # Convert sentiment scores to numeric values
    sentiment_mapping = {
        'very positive': 5,
        'positive': 4,
        'neutral': 3,
        'negative': 2,
        'very negative': 1
    }
    
    mgmt_scores = [sentiment_mapping.get(score, 3) for score in quarterly_summary['mgmt_sentiment_score']]
    qa_scores = [sentiment_mapping.get(score, 3) for score in quarterly_summary['qa_sentiment_score']]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=quarters,
        y=mgmt_scores,
        mode='lines+markers',
        name='Management Sentiment',
        line=dict(color='#00cc96', width=3),
        marker=dict(size=8)
    ))
    
    fig.add_trace(go.Scatter(
        x=quarters,
        y=qa_scores,
        mode='lines+markers',
        name='Q&A Sentiment',
        line=dict(color='#636efa', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title='Sentiment Trends Across Quarters',
        xaxis_title='Quarter',
        yaxis_title='Sentiment Score',
        yaxis=dict(range=[1, 5], tickvals=[1, 2, 3, 4, 5], 
                  ticktext=['Very Negative', 'Negative', 'Neutral', 'Positive', 'Very Positive']),
        height=400
    )
    
    return fig

def create_strategic_focus_chart(strategic_focuses):
    """Create strategic focuses visualization"""
    quarters = strategic_focuses['quarter'] + ' ' + strategic_focuses['year'].astype(str)
    
    fig = px.sunburst(
        strategic_focuses,
        path=['quarter', 'theme'],
        values='mentions',
        title='Strategic Focuses by Quarter',
        height=500
    )
    
    return fig

def create_confidence_chart(quarterly_summary):
    """Create confidence level visualization"""
    quarters = quarterly_summary['quarter'] + ' ' + quarterly_summary['year'].astype(str)
    
    fig = px.bar(
        x=quarters,
        y=quarterly_summary['mgmt_sentiment_confidence'],
        title='Management Sentiment Confidence by Quarter',
        labels={'x': 'Quarter', 'y': 'Confidence Level'},
        color=quarterly_summary['mgmt_sentiment_confidence'],
        color_continuous_scale='viridis'
    )
    
    fig.update_layout(height=400)
    return fig

def main():
    st.set_page_config(
        page_title="NVIDIA Earnings Analysis Dashboard",
        layout="wide"
    )
    
    st.title("NVIDIA Earnings Call Analysis Dashboard")
    st.markdown("---")
    
    # Load data
    try:
        quarterly_summary, strategic_focuses, transcripts, analysis_data = load_data()
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a section:",
        ["Overview", "Transcripts", "Sentiment Analysis", "Strategic Focuses", "Tone Trends"]
    )
    
    if page == "Overview":
        st.header("Dashboard Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Quarters", len(quarterly_summary))
        
        with col2:
            avg_confidence = quarterly_summary['mgmt_sentiment_confidence'].mean()
            st.metric("Avg Confidence", f"{avg_confidence:.2f}")
        
        with col3:
            total_focuses = len(strategic_focuses)
            st.metric("Strategic Focuses", total_focuses)
        
        with col4:
            latest_sentiment = quarterly_summary.iloc[-1]['mgmt_sentiment_score']
            st.metric("Latest Sentiment", latest_sentiment.title())
        
        st.markdown("### Quick Insights")
        st.info("This dashboard analyzes NVIDIA's earnings call transcripts across Q1-Q4 2025, providing insights into sentiment trends, strategic focuses, and management tone.")
        
    elif page == "Transcripts":
        st.header("Earnings Call Transcripts")
        
        quarter_options = list(transcripts.keys())
        selected_quarter = st.selectbox("Select Quarter:", quarter_options)
        
        if selected_quarter and selected_quarter in transcripts:
            st.subheader(f"{selected_quarter} Transcript")
            
            transcript_text = transcripts[selected_quarter]
            
            # Show word count and key stats
            word_count = len(transcript_text.split())
            st.info(f"Word count: {word_count:,}")
            
            # Display the transcript text
            st.text_area("Full Transcript", transcript_text, height=500)
    
    elif page == "Sentiment Analysis":
        st.header("Sentiment Analysis")
        
        # Main sentiment chart
        st.subheader("Sentiment Trends Over Time")
        sentiment_fig = create_sentiment_chart(quarterly_summary)
        st.plotly_chart(sentiment_fig, use_container_width=True)
        
        # Confidence levels
        st.subheader("Confidence Levels")
        confidence_fig = create_confidence_chart(quarterly_summary)
        st.plotly_chart(confidence_fig, use_container_width=True)
        
        # Detailed sentiment breakdown
        st.subheader("Detailed Sentiment Breakdown")
        for _, row in quarterly_summary.iterrows():
            quarter_label = f"{row['quarter']} {row['year']}"
            
            with st.expander(f"{quarter_label} - {row['mgmt_sentiment_score'].title()}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Management Sentiment:**")
                    st.write(f"Score: {row['mgmt_sentiment_score'].title()}")
                    st.write(f"Confidence: {row['mgmt_sentiment_confidence']:.2f}")
                    st.write(f"Reasoning: {row['mgmt_reasoning']}")
                
                with col2:
                    st.write("**Q&A Sentiment:**")
                    st.write(f"Score: {row['qa_sentiment_score'].title()}")
                    st.write(f"Confidence: {row['qa_sentiment_confidence']:.2f}")
                    st.write(f"Reasoning: {row['qa_reasoning']}")
    
    elif page == "Strategic Focuses":
        st.header("Strategic Focuses")
        
        st.subheader("Strategic Focus Distribution")
        strategic_fig = create_strategic_focus_chart(strategic_focuses)
        st.plotly_chart(strategic_fig, use_container_width=True)
        
        # Strategic focus table
        st.subheader("Detailed Strategic Focuses")
        
        # Filter by quarter
        quarter_filter = st.selectbox(
            "Filter by Quarter:",
            ["All"] + list(strategic_focuses['quarter'].unique())
        )
        
        if quarter_filter != "All":
            filtered_focuses = strategic_focuses[strategic_focuses['quarter'] == quarter_filter]
        else:
            filtered_focuses = strategic_focuses
        
        st.dataframe(filtered_focuses, use_container_width=True)
        
        # Top themes analysis
        st.subheader("Top Strategic Themes")
        theme_mentions = strategic_focuses.groupby('theme')['mentions'].sum().sort_values(ascending=False)
        
        fig_themes = px.bar(
            x=theme_mentions.values,
            y=theme_mentions.index,
            orientation='h',
            title='Total Mentions by Strategic Theme',
            labels={'x': 'Total Mentions', 'y': 'Theme'}
        )
        st.plotly_chart(fig_themes, use_container_width=True)
    
    elif page == "Tone Trends":
        st.header("Tone Change Trends")
        
        quarters = quarterly_summary['quarter'] + ' ' + quarterly_summary['year'].astype(str)
        
        # Tone Score Trends
        st.subheader("Management Tone Scores Over Time")
        tone_fig = px.line(
            x=quarters,
            y=quarterly_summary['tone_score'],
            title='Tone Score Trends (0-100 Scale)',
            markers=True,
            line_shape='linear'
        )
        tone_fig.update_layout(
            yaxis=dict(range=[0, 100]),
            height=400
        )
        st.plotly_chart(tone_fig, use_container_width=True)
        
        
        # Detailed Tone Summary
        st.subheader("Quarterly Tone Details")
        
        for _, row in quarterly_summary.iterrows():
            quarter_label = f"{row['quarter']} {row['year']}"
            
            with st.expander(f"{quarter_label} - {row['tone'].title()} (Score: {row['tone_score']})"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Tone Type", row['tone'].title())
                
                with col2:
                    st.metric("Tone Score", f"{row['tone_score']}/100")
                
                with col3:
                    st.metric("Confidence Level", row['confidence_level'].title())
            

if __name__ == "__main__":
    main()