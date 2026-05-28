import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd
from streamlit_chat import message
import os
import time

# Page config
st.set_page_config(
    page_title="AI Refund Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar configuration
st.sidebar.title("🤖 AI Refund Agent")
page = st.sidebar.radio("Select Page", ["Customer Support", "Admin Dashboard"])

# Backend API configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")

def get_api_url():
    """Get API URL from environment or sidebar input"""
    return st.sidebar.text_input(
        "API Server URL",
        value=API_URL,
        help="Enter the backend API URL"
    )

def health_check(api_url):
    """Check if backend is running"""
    try:
        response = requests.get(f"{api_url}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def get_agent_info(api_url):
    """Get current agent configuration (LLM or Rule-based)"""
    try:
        response = requests.get(f"{api_url}/api/agent-info", timeout=2)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def display_agent_status(api_url):
    """Display agent status and mode selector in sidebar"""
    agent_info = get_agent_info(api_url)
    
    if agent_info:
        st.sidebar.divider()
        st.sidebar.subheader("🤖 Agent Status")
        
        # Initialize session state for selected mode
        if "selected_mode" not in st.session_state:
            st.session_state.selected_mode = agent_info.get("current_mode", "rule-based")
        
        # Get available modes
        available_modes = agent_info.get("available_modes", ["rule-based"])
        
        # Mode selector
        selected_mode = st.sidebar.selectbox(
            "Select Processing Mode:",
            options=available_modes,
            index=available_modes.index(st.session_state.selected_mode) if st.session_state.selected_mode in available_modes else 0,
            help="Choose between rule-based (deterministic) or LLM (intelligent) mode"
        )
        
        # Update session state
        st.session_state.selected_mode = selected_mode
        
        # Display current status
        if selected_mode == "llm":
            st.sidebar.success(f"✅ **LLM Mode Selected**")
            st.sidebar.info(f"Model: `{agent_info.get('llm_model', 'gpt-3.5-turbo')}`")
            if agent_info.get("has_openai_key"):
                st.sidebar.success("🔑 OpenAI API Key: Connected")
            else:
                st.sidebar.warning("⚠️ OpenAI API Key: Not configured")
        else:
            st.sidebar.info(f"📋 **Rule-Based Mode Selected**")
            st.sidebar.caption("Using deterministic policy rules (no LLM costs)")
        
        # Show switch status if different from default
        if selected_mode != agent_info.get("current_mode"):
            st.sidebar.info(f"📤 Will use {selected_mode} mode for this request")
        
        return selected_mode
    
    return "rule-based"

if page == "Customer Support":
    st.title("🛍️ Customer Refund Support")
    
    api_url = get_api_url()
    
    # Check API connection
    if not health_check(api_url):
        st.error(f"⚠️ Cannot connect to backend API at {api_url}")
        st.info("Make sure the FastAPI server is running on the specified address")
        st.stop()
    
    st.success("✓ Connected to AI Agent API")
    
    # Display agent status
    display_agent_status(api_url)
    
    # Two-column layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Refund Request Form")
        
        # Input fields
        customer_id = st.text_input(
            "Customer ID",
            placeholder="e.g., CUST001",
            help="Your unique customer ID"
        )
        
        order_id = st.text_input(
            "Order ID",
            placeholder="e.g., ORD-2024-001",
            help="The order ID you want to refund"
        )
        
        reason = st.text_area(
            "Reason for Refund",
            placeholder="Please explain why you need a refund...",
            height=100,
            help="Be specific about the reason (e.g., defective, wrong item, changed mind)"
        )
        
        requested_amount = st.number_input(
            "Requested Refund Amount (Optional)",
            min_value=0.0,
            step=0.01,
            help="Leave as 0 for full refund of order amount"
        )
        
        # Submit button
        if st.button("🔍 Submit Refund Request", use_container_width=True, type="primary"):
            if not all([customer_id, order_id, reason]):
                st.error("❌ Please fill in all required fields")
            else:
                with st.spinner("Processing your request..."):
                    try:
                        payload = {
                            "customer_id": customer_id,
                            "order_id": order_id,
                            "reason": reason,
                            "requested_amount": requested_amount if requested_amount > 0 else None,
                            "mode": st.session_state.get("selected_mode", "rule-based")
                        }
                        
                        response = requests.post(
                            f"{api_url}/api/refund/process",
                            json=payload,
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.session_state.last_result = result
                        else:
                            st.error(f"❌ Error: {response.text}")
                    
                    except Exception as e:
                        st.error(f"❌ Connection error: {str(e)}")
    
    with col2:
        st.subheader("Quick Info")
        st.info("""
        **Sample Customer IDs:**
        - CUST001 (John Smith)
        - CUST003 (Michael Brown)
        - CUST015 (Matthew Lewis - VIP)
        
        **Sample Order IDs:**
        - ORD-2024-001
        - ORD-2024-020
        - ORD-2024-070
        """)
    
    # Display result
    if "last_result" in st.session_state:
        result = st.session_state.last_result
        
        st.divider()
        st.subheader("📋 Decision Result")
        
        # Decision badge
        if result["decision"] == "approved":
            st.success(f"✅ APPROVED - ${result['amount']:.2f}")
        elif result["decision"] == "denied":
            st.error(f"❌ DENIED")
        else:
            st.warning(f"⚠️ ESCALATED - Requires Human Review")
        
        # Result details
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Decision:** {result['decision'].upper()}")
            st.write(f"**Amount:** ${result['amount']:.2f}")
            st.write(f"**Requires Review:** {'Yes' if result['requires_human_review'] else 'No'}")
        
        with col2:
            st.write(f"**Policy Violations:** {len(result['policy_violations'])}")
            if result['policy_violations']:
                for violation in result['policy_violations']:
                    st.write(f"- {violation}")
        
        # Reason and next steps
        st.info(f"**Reason:** {result['reason']}")
        st.success(f"**Next Steps:** {result['next_steps']}")
        
        # Reasoning log
        with st.expander("📊 Agent Reasoning Log"):
            for log_entry in result['reasoning_log']:
                st.code(log_entry, language="text")

elif page == "Admin Dashboard":
    st.title("📊 Admin Dashboard")
    
    api_url = get_api_url()
    
    # Check API connection
    if not health_check(api_url):
        st.error(f"⚠️ Cannot connect to backend API at {api_url}")
        st.stop()
    
    st.success("✓ Connected to AI Agent API")
    
    # Display agent status
    display_agent_status(api_url)
    
    # Refresh button
    if st.button("🔄 Refresh Dashboard", use_container_width=True):
        st.rerun()
    
    try:
        # Fetch dashboard data
        dashboard_response = requests.get(
            f"{api_url}/api/admin/dashboard",
            timeout=10
        )
        
        if dashboard_response.status_code == 200:
            dashboard = dashboard_response.json()
            summary = dashboard["summary"]
            
            # Summary metrics
            st.subheader("📈 Summary Metrics")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Total Requests", summary["total_requests"])
            
            with col2:
                st.metric("Approved", summary["approved"], 
                         delta=f"{dashboard.get('approval_rate', 0):.1f}%")
            
            with col3:
                st.metric("Denied", summary["denied"])
            
            with col4:
                st.metric("Escalated", summary["escalated"])
            
            with col5:
                st.metric("Approval Rate", f"{dashboard.get('approval_rate', 0):.1f}%")
            
            st.divider()
            
            # Financial summary
            st.subheader("💰 Financial Summary")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    "Total Approved Amount",
                    f"${summary['total_approved_amount']:.2f}"
                )
            
            with col2:
                st.metric(
                    "Total Escalated Amount",
                    f"${summary['total_escalated_amount']:.2f}"
                )
            
            st.divider()
            
            # Recent requests
            st.subheader("📝 Recent Refund Requests")
            
            if dashboard["recent_requests"]:
                # Create a dataframe for display
                requests_data = []
                for entry in dashboard["recent_requests"]:
                    if entry["type"] == "refund_request":
                        req = entry["request"]
                        resp = entry["response"]
                        requests_data.append({
                            "Customer ID": req["customer_id"],
                            "Order ID": req["order_id"],
                            "Decision": resp["decision"].upper(),
                            "Amount": f"${resp['amount']:.2f}",
                            "Requires Review": "Yes" if resp["requires_human_review"] else "No"
                        })
                
                if requests_data:
                    df = pd.DataFrame(requests_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No refund requests processed yet")
            
            st.divider()
            
            # Detailed logs
            st.subheader("🔍 Detailed Processing Logs")
            
            log_response = requests.get(
                f"{api_url}/api/admin/conversation-log?limit=10",
                timeout=10
            )
            
            if log_response.status_code == 200:
                logs = log_response.json()
                
                for i, entry in enumerate(reversed(logs.get("entries", [])), 1):
                    if entry["type"] == "refund_request":
                        with st.expander(f"Request #{i}: {entry['request']['customer_id']} - {entry['request']['order_id']}"):
                            resp = entry["response"]
                            
                            col1, col2 = st.columns([1, 1])
                            
                            with col1:
                                st.write(f"**Decision:** {resp['decision'].upper()}")
                                st.write(f"**Amount:** ${resp['amount']:.2f}")
                                st.write(f"**Violations:** {len(resp['policy_violations'])}")
                            
                            with col2:
                                st.write(f"**Requires Review:** {'Yes' if resp['requires_human_review'] else 'No'}")
                                st.write(f"**Reason:** {resp['reason']}")
                            
                            # Reasoning steps
                            st.write("**Agent Reasoning:**")
                            for step in resp['reasoning_log'][:5]:  # Show first 5 steps
                                st.text(step)
                            
                            if len(resp['reasoning_log']) > 5:
                                with st.expander(f"Show all {len(resp['reasoning_log'])} reasoning steps"):
                                    for step in resp['reasoning_log']:
                                        st.text(step)
        
        else:
            st.error("Failed to fetch dashboard data")
    
    except Exception as e:
        st.error(f"Error fetching dashboard: {str(e)}")

# Footer
st.divider()
st.caption("🤖 AI Refund Agent v1.0 | Powered by FastAPI + Streamlit")
