import streamlit as st
import sqlite3
import pandas as pd
import os
from pathlib import Path

# --- 1. THEME & SETUP ---
st.set_page_config(page_title="AI Triage & Annotation Lab", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8fafc !important; }
    h1, h2, h3, p, span, label { color: #1e293b !important; font-family: 'Inter', sans-serif; }
    [data-testid="column"] {
        background-color: #ffffff !important;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .stButton>button {
        background-color: #2563eb !important;
        color: white !important;
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINE (Session State Driven) ---
DB_PATH = Path("/Users/aldacal/ProYECTS/ai-tickets-triage/db/app.db")

def load_initial_data():
    if not DB_PATH.exists():
        st.error("Database file not found!")
        return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM ai_predictions", conn)
    conn.close()
    return df

# Initialize Session State so we work in memory
if 'working_df' not in st.session_state:
    st.session_state.working_df = load_initial_data()

# Refresh the view from session state
df = st.session_state.working_df

# --- 3. UI LAYOUT ---
st.title("🛡️ AI Support Triage & Annotation")
st.caption("Human-in-the-Loop Review System")

if df.empty:
    st.warning("No data to display.")
else:
    # Top Metrics
    m1, m2, m3 = st.columns(3)
    total = len(df)
    reviewed = len(df[df['reviewed_status'] == 'human_reviewed'])
    m1.metric("Queue Size", total)
    m2.metric("Annotations Complete", reviewed)
    m3.metric("Progress", f"{(reviewed/total)*100:.1f}%")

    st.divider()

    col_nav, col_list, col_main = st.columns([1, 2.2, 3])

    # PANE 1: PRIORITY FILTERS
    with col_nav:
        st.write("### 📁 Folders")
        priorities = ["Urgent", "High", "Medium", "Low"]
        p_labels = [f"{p} ({len(df[df['priority'].str.lower() == p.lower()])})" for p in priorities]
        sel_p_label = st.radio("Priority Filter", p_labels, key="nav_p")
        sel_p = sel_p_label.split(" ")[0].lower()

    # PANE 2: TICKET FEED
    with col_list:
        st.write(f"### 📋 {sel_p.upper()} Queue")
        sub_df = df[df['priority'].str.lower() == sel_p].copy()
        
        if sub_df.empty:
            st.info("No tickets in this tier.")
            sel_id = None
        else:
            sub_df['display'] = sub_df['ticket_id'].astype(str) + ": " + sub_df['subject'].str.slice(0, 40)
            sel_choice = st.radio("Select Ticket", sub_df['display'].tolist(), key="nav_t")
            sel_id = int(sel_choice.split(":")[0])

    # PANE 3: ANNOTATION WORKSPACE
    with col_main:
        if sel_id:
            # Get data from our in-memory session state
            idx = df[df['ticket_id'] == sel_id].index[0]
            ticket = df.iloc[idx]
            
            st.write(f"## Ticket #{ticket['ticket_id']}")
            st.markdown(f"**Subject:** {ticket['subject']}")
            
            st.text_area("Customer Message", ticket['description'], height=150, disabled=True)
            
            with st.expander("🤖 AI Reasoning & Confidence", expanded=False):
                st.write(ticket['reasoning'])
                st.progress(int(ticket['confidence'])/100, f"Confidence: {ticket['confidence']}%")

            st.divider()
            
            # THE ANNOTATION FORM
            st.write("### ✍️ Human Annotation")
            new_p = st.selectbox("Corrected Priority", ["low", "medium", "high", "urgent"], 
                                 index=["low", "medium", "high", "urgent"].index(ticket['priority'].lower()))
            
            new_team = st.selectbox("Route to Team", ["Support", "SRE", "Billing", "Dev", "Security Operations"],
                                   index=0) # You can add logic here to match existing team

            if st.button("UPDATE MEMORY & MOVE"):
                # Update the Session State (Memory)
                st.session_state.working_df.at[idx, 'priority'] = new_p.lower()
                st.session_state.working_df.at[idx, 'assigned_team'] = new_team
                st.session_state.working_df.at[idx, 'reviewed_status'] = 'human_reviewed'
                
                st.toast(f"Ticket {sel_id} updated in memory!", icon="📝")
                st.rerun()
        else:
            st.write("Please select a ticket.")

    # --- 4. THE EXPORT WIZARD ---
    st.sidebar.divider()
    st.sidebar.write("### 💾 Data Export")
    st.sidebar.write("Save your annotations to a CSV for training.")
    
    csv = st.session_state.working_df.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button(
        label="📥 Download Reviewed Dataset",
        data=csv,
        file_name="reviewed_tickets.csv",
        mime="text/csv",
    )