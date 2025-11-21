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

def send_chat_request(kpi_data_g1, add_data_g1, kpi_data_g2, add_data_g2, question, session_id=None):
    """Send request to chat endpoint with session management"""
    payload = {
        "kpi_data_g1": kpi_data_g1,
        "add_data_g1": add_data_g1,
        "kpi_data_g2": kpi_data_g2,
        "add_data_g2": add_data_g2,
        "question": question
    }
    
    # Add session_id if available
    if session_id:
        payload["session_id"] = session_id
    
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
    
    # Sidebar for data overview and token usage
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
    
    # Chat interface
    st.header("💬 Financial Chat")
    
    # CRITICAL: Session state backup mechanism
    if "_session_backup" not in st.session_state:
        st.session_state._session_backup = {
            "session_id": None,
            "messages": [],
            "session_info": None
        }
    
    # Initialize session state for chat and session management
    if "messages" not in st.session_state:
        # Check if we have backup data
        if st.session_state._session_backup["messages"]:
            st.session_state.messages = st.session_state._session_backup["messages"]
            print(f"🔄 RESTORED messages from backup: {len(st.session_state.messages)}")
        else:
            st.session_state.messages = []
            print(f"🆕 INITIALIZED: messages")
    
    if "session_id" not in st.session_state:
        # Check if we have backup data
        if st.session_state._session_backup["session_id"]:
            st.session_state.session_id = st.session_state._session_backup["session_id"]
            print(f"🔄 RESTORED session_id from backup: {st.session_state.session_id}")
        else:
            st.session_state.session_id = None
            print(f"🆕 INITIALIZED: session_id")
    
    if "session_info" not in st.session_state:
        # Check if we have backup data
        if st.session_state._session_backup["session_info"]:
            st.session_state.session_info = st.session_state._session_backup["session_info"]
            print(f"🔄 RESTORED session_info from backup")
        else:
            st.session_state.session_info = None
            print(f"🆕 INITIALIZED: session_info")
    
    # CRITICAL: Add session persistence check
    if hasattr(st.session_state, '_is_first_run') and st.session_state._is_first_run:
        print(f"⚠️  STREAMLIT RE-RUN DETECTED - Preserving session state")
    else:
        print(f"🚀 STREAMLIT FIRST RUN - Initializing session state")
        st.session_state._is_first_run = True
    
    # Debug current session state
    print(f"📊 STREAMLIT SESSION STATE:")
    print(f"   session_id: {st.session_state.session_id}")
    print(f"   messages count: {len(st.session_state.messages)}")
    print(f"   session_info: {st.session_state.session_info}")
    print(f"   _is_first_run: {getattr(st.session_state, '_is_first_run', False)}")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask a financial question..."):
        # CRITICAL: Prevent duplicate processing
        if hasattr(st.session_state, '_last_processed_prompt') and st.session_state._last_processed_prompt == prompt:
            print(f"⚠️  DUPLICATE PROMPT DETECTED - SKIPPING: {prompt[:50]}...")
            return
        
        st.session_state._last_processed_prompt = prompt
        
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # CRITICAL: Update backup immediately
        st.session_state._session_backup["messages"] = st.session_state.messages
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("🤔 Analyzing your financial data..."):
                print(f"🚀 SENDING TO API:")
                print(f"   session_id: {st.session_state.session_id}")
                print(f"   user_query: {prompt[:50]}...")
                print(f"   messages_count: {len(st.session_state.messages)}")
                
                # CRITICAL: Preserve session ID before API call
                current_session_id = st.session_state.session_id
                print(f"🔄 PRESERVING SESSION BEFORE API CALL: {current_session_id}")
                
                response = send_chat_request(
                    kpi_data_g1, add_data_g1, kpi_data_g2, add_data_g2, prompt, st.session_state.session_id
                )
                
                # CRITICAL: Check if session was lost during API call
                if current_session_id and not st.session_state.session_id:
                    print(f"🚨 SESSION LOST DETECTED - RESTORING: {current_session_id}")
                    st.session_state.session_id = current_session_id
                
                print(f"📨 API RESPONSE STATUS: {response.status_code if hasattr(response,'status_code') else 'N/A'}")
                if response and hasattr(response,'status_code') and response.status_code == 200:
                    print(f"📨 API RESPONSE DATA:")
                    print(f"   session_id: {response.get('session_id')}")
                    print(f"   is_new_session: {response.get('is_new_session', False)}")
                    print(f"   answer_length: {len(response.get('response', ''))}")
                
                if response:
                    ai_response = response.get('response', 'No response available')
                    st.markdown(ai_response)
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})
                    
                    # Handle session management
                    if 'session_id' in response:
                        # CRITICAL: Only update session ID if it's different and valid
                        old_session_id = st.session_state.session_id
                        new_session_id = response['session_id']
                        
                        if old_session_id != new_session_id:
                            print(f"🔄 SESSION UPDATE: {old_session_id} → {new_session_id}")
                            print(f"   is_new_session: {response.get('is_new_session', False)}")
                            st.session_state.session_id = new_session_id
                        else:
                            print(f"✅ SESSION UNCHANGED: {old_session_id}")
                        
                        # Always preserve existing session unless explicitly new
                        if not response.get('is_new_session', False) and old_session_id:
                            print(f"🔒 PRESERVING EXISTING SESSION: {old_session_id}")
                            st.session_state.session_id = old_session_id
                        
                        # CRITICAL: Update session backup
                        st.session_state._session_backup["session_id"] = st.session_state.session_id
                        st.session_state._session_backup["messages"] = st.session_state.messages
                        st.session_state._session_backup["session_info"] = st.session_state.session_info
                        print(f"💾 SESSION BACKUP UPDATED")
                        
                        # Show session info for new sessions
                        if response.get('is_new_session', False):
                            st.success(f"🆕 New session started: {response['session_id'][:8]}...")
                            st.session_state.session_info = {
                                'session_id': response['session_id'],
                                'is_new': True,
                                'started_at': datetime.now()
                            }
                        
                        # Display session info in sidebar
                        with st.sidebar:
                            st.divider()
                            st.header("🔑 Session Info")
                            st.write(f"Session ID: `{response['session_id'][:8]}...`")
                            st.write(f"Started: {st.session_state.session_info['started_at'].strftime('%H:%M:%S')}")
                            st.write(f"Messages: {len(st.session_state.messages) // 2}")
                            
                            # Add button to reset session
                            if st.button("🔄 Reset Session", type="secondary"):
                                print(f"🔄 RESET SESSION TRIGGERED!")
                                print(f"   Old session_id: {st.session_state.session_id}")
                                print(f"   Messages count: {len(st.session_state.messages)}")
                                
                                st.session_state.session_id = None
                                st.session_state.session_info = None
                                st.session_state.messages = []
                                st.rerun()
                    
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

if __name__ == "__main__":
    main()
