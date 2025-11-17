import streamlit as st
import json
import requests
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

def load_data():
    """Load the financial data from data.json"""
    try:
        with open('data.json', 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        st.error("❌ data.json file not found")
        return None
    except json.JSONDecodeError as e:
        st.error(f"❌ Error parsing JSON: {e}")
        return None

def send_chat_request(kpi_data_g1, add_data_g1, kpi_data_g2, add_data_g2, question):
    """Send request to chat endpoint"""
    payload = {
        "kpi_data_g1": kpi_data_g1,
        "add_data_g1": add_data_g1,
        "kpi_data_g2": kpi_data_g2,
        "add_data_g2": add_data_g2,
        "question": question
    }
    
    try:
        response = requests.post(
            'https://dashboard-ai-production.up.railway.app/chat',
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"❌ Error: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("❌ Could not connect to the server. Make sure the Flask API is running on port 8083")
        return None

def create_income_chart(kpi_data_g1):
    """Create income visualization chart"""
    if not kpi_data_g1:
        return None
    
    # Convert to DataFrame for easier plotting
    df = pd.DataFrame(kpi_data_g1)
    
    if 'Income' not in df.columns or 'Month_Year' not in df.columns:
        return None
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['Month_Year'],
        y=df['Income'],
        mode='lines+markers',
        name='Income',
        line=dict(color='green', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title='Income Over Time',
        xaxis_title='Month',
        yaxis_title='Income ($)',
        template='plotly_white',
        height=400
    )
    
    return fig

def create_kpi_dashboard(kpi_data_g2):
    """Create KPI dashboard"""
    if not kpi_data_g2:
        return None
    
    df = pd.DataFrame(kpi_data_g2)
    
    # Create subplots for different KPIs
    fig = go.Figure()
    
    kpi_metrics = ['Gross Profit', 'EBITDA', 'Net Income']
    colors = ['blue', 'orange', 'red']
    
    for i, metric in enumerate(kpi_metrics):
        if metric in df.columns:
            fig.add_trace(go.Scatter(
                x=df.get('Month_Year', df.index),
                y=df[metric],
                mode='lines+markers',
                name=metric,
                line=dict(color=colors[i], width=3),
                marker=dict(size=8)
            ))
    
    fig.update_layout(
        title='Key Performance Indicators',
        xaxis_title='Month',
        yaxis_title='Value ($)',
        template='plotly_white',
        height=400,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )
    
    return fig

def main():
    st.set_page_config(
        page_title="Financial AI Assistant",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🏦 Financial AI Assistant")
    st.markdown("### Ask questions about your financial data")
    
    # Load data
    data = load_data()
    if not data:
        return
    
    # Extract data sections
    kpi_data_g1 = data.get('kpi_data_g1', [])
    add_data_g1 = data.get('add_data_g1', [])
    kpi_data_g2 = data.get('kpi_data_g2', [])
    add_data_g2 = data.get('add_data_g2', [])
    
    # Sidebar for data overview
    with st.sidebar:
        st.header("📊 Data Overview")
        st.metric("KPI Data G1", f"{len(kpi_data_g1)} records")
        st.metric("Additional Data G1", f"{len(add_data_g1)} records")
        st.metric("KPI Data G2", f"{len(kpi_data_g2)} records")
        st.metric("Additional Data G2", f"{len(add_data_g2)} records")
        
        st.divider()
        
        # Token usage tracking
        if 'token_stats' not in st.session_state:
            st.session_state.token_stats = {
                'total_prompt_tokens': 0,
                'total_completion_tokens': 0,
                'total_tokens': 0,
                'query_count': 0,
                'cached_tokens': 0,
                'cache_hit_rate': 0,
                'total_cost': 0.0,
                'cache_miss_cost': 0.0,
                'cache_hit_cost': 0.0
            }
        
        # Pricing constants (per 1M tokens)
        CACHE_MISS_COST_PER_1M = 0.27  # $0.27 per 1M tokens
        CACHE_HIT_COST_PER_1M = 0.07   # $0.07 per 1M tokens
        
        st.header("🔢 Token Usage & Cost")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Queries", st.session_state.token_stats['query_count'])
            st.metric("Total Tokens", f"{st.session_state.token_stats['total_tokens']:,}")
            st.metric("Total Cost", f"${st.session_state.token_stats['total_cost']:.4f}")
        with col2:
            st.metric("Cached Tokens", f"{st.session_state.token_stats['cached_tokens']:,}")
            st.metric("Cache Hit Rate", f"{st.session_state.token_stats['cache_hit_rate']:.1f}%")
            st.metric("Cache Miss Cost", f"${st.session_state.token_stats['cache_miss_cost']:.4f}")
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["💬 Chat", "📈 Visualizations", "📋 Sample Questions"])
    
    with tab1:
        st.header("💬 Financial Chat")
        
        # Chat interface
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask a financial question..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Get AI response
            with st.chat_message("assistant"):
                with st.spinner("🤔 Analyzing your financial data..."):
                    response = send_chat_request(
                        kpi_data_g1, add_data_g1, kpi_data_g2, add_data_g2, prompt
                    )
                    
                    if response:
                        ai_response = response.get('response', 'No response available')
                        st.markdown(ai_response)
                        st.session_state.messages.append({"role": "assistant", "content": ai_response})
                        
                        # Update token stats
                        if 'tokens' in response:
                            tokens = response['tokens']
                            st.session_state.token_stats['query_count'] += 1
                            st.session_state.token_stats['total_prompt_tokens'] += tokens.get('prompt', 0)
                            st.session_state.token_stats['total_completion_tokens'] += tokens.get('completion', 0)
                            st.session_state.token_stats['total_tokens'] += tokens.get('total', 0)
                            st.session_state.token_stats['cached_tokens'] += tokens.get('cached_tokens', 0)
                            
                            # Calculate cache hit rate
                            if st.session_state.token_stats['total_prompt_tokens'] > 0:
                                st.session_state.token_stats['cache_hit_rate'] = (
                                    st.session_state.token_stats['cached_tokens'] / 
                                    st.session_state.token_stats['total_prompt_tokens'] * 100
                                )
                            
                            # Calculate costs
                            prompt_tokens = tokens.get('prompt', 0)
                            cached_tokens = tokens.get('cached_tokens', 0)
                            cache_miss_tokens = prompt_tokens - cached_tokens
                            
                            # Calculate costs for this query
                            cache_hit_cost = (cached_tokens / 1_000_000) * CACHE_HIT_COST_PER_1M
                            cache_miss_cost = (cache_miss_tokens / 1_000_000) * CACHE_MISS_COST_PER_1M
                            total_cost = cache_hit_cost + cache_miss_cost
                            
                            # Update cumulative costs
                            st.session_state.token_stats['cache_hit_cost'] += cache_hit_cost
                            st.session_state.token_stats['cache_miss_cost'] += cache_miss_cost
                            st.session_state.token_stats['total_cost'] += total_cost
                            
                            # Show token usage for this query
                            with st.expander("🔢 Token Usage Details"):
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("Prompt Tokens", f"{tokens.get('prompt', 0):,}")
                                with col2:
                                    st.metric("Completion Tokens", f"{tokens.get('completion', 0):,}")
                                with col3:
                                    st.metric("Total Tokens", f"{tokens.get('total', 0):,}")
                                with col4:
                                    cached = tokens.get('cached_tokens', 0)
                                    st.metric("Cached Tokens", f"{cached:,}")
                                
                                # Cost breakdown
                                st.divider()
                                st.write("💰 **Cost Breakdown for this query:**")
                                cost_col1, cost_col2, cost_col3 = st.columns(3)
                                with cost_col1:
                                    st.metric("Cache Hit Cost", f"${cache_hit_cost:.6f}")
                                with cost_col2:
                                    st.metric("Cache Miss Cost", f"${cache_miss_cost:.6f}")
                                with cost_col3:
                                    st.metric("Total Query Cost", f"${total_cost:.6f}")
                                
                                # Savings information
                                if cached_tokens > 0:
                                    savings = (cached_tokens / 1_000_000) * (CACHE_MISS_COST_PER_1M - CACHE_HIT_COST_PER_1M)
                                    st.success(f"💡 You saved ${savings:.6f} with cached tokens!")
                                    st.info(f"Cache hit rate for this query: {(cached_tokens / prompt_tokens * 100):.1f}%")
                    else:
                        st.error("Failed to get response from the AI assistant")
    
    with tab2:
        st.header("📈 Financial Visualizations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            income_chart = create_income_chart(kpi_data_g1)
            if income_chart:
                st.plotly_chart(income_chart, use_container_width=True)
            else:
                st.info("Income data not available for visualization")
        
        with col2:
            kpi_chart = create_kpi_dashboard(kpi_data_g2)
            if kpi_chart:
                st.plotly_chart(kpi_chart, use_container_width=True)
            else:
                st.info("KPI data not available for visualization")
        
        # Data preview
        with st.expander("📋 View Raw Data"):
            if kpi_data_g1:
                st.subheader("KPI Data G1")
                st.dataframe(pd.DataFrame(kpi_data_g1))
            
            if kpi_data_g2:
                st.subheader("KPI Data G2")
                st.dataframe(pd.DataFrame(kpi_data_g2))
    
    with tab3:
        st.header("💡 Sample Questions")
        
        sample_questions = [
            "What is the trend in income over the past year?",
            "Which month had the highest income?",
            "What is the average gross profit?",
            "How has EBITDA changed over time?",
            "What was the net income in July 2024?",
            "Compare income between Q1 and Q2 2024",
            "What is the overall financial performance trend?",
            "Which metrics show the most volatility?"
        ]
        
        for i, question in enumerate(sample_questions):
            if st.button(f"Q{i+1}: {question}", key=f"sample_q_{i}"):
                # Add to chat and trigger response
                st.session_state.messages.append({"role": "user", "content": question})
                st.rerun()

if __name__ == "__main__":
    main()