import streamlit as st
import sqlite3
import pandas as pd
import os

# --- 1. SETUP & THEME ---
st.set_page_config(page_title="Audit Command Center", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0d1117; }
    
    /* Panel Containers */
    .ticket-item {
        padding: 10px;
        border-bottom: 1px solid #30363d;
        cursor: pointer;
        transition: 0.2s;
    }
    .ticket-item:hover { background-color: #161b22; }
    
    .active-ticket {
        background-color: #1f2937 !important;
        border-left: 4px solid #3b82f6;
    }

    /* Text Colors */
    h1, h2, h3, p, span, label { color: #c9d1d9 !important; }
    .subject-small { font-size: 14px; font-weight: 600; display: block; }
    .id-small { font-size: 10px; color: #8b949e; }
    
    /* Priority Dots */
    .dot { height: 8px; width: 8px; border-radius: 50%; display: inline-block; margin-right: 5px; }
    .urgent-dot { background-color: #f85149; }
    .high-dot { background-color: #f0883e; }
    .medium-dot { background-color: #d2a8ff; }
    .low-dot { background-color: #8b949e; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA CONNECTION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "db", "app.db")

def get_data():
    if not os.path.exists(DB_PATH): return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM ai_predictions ORDER BY ticket_id DESC", conn)
    conn.close()
    return df

df = get_data()

# --- 3. THE THREE-PANEL LAYOUT ---
if df.empty:
    st.warning("No data found. Run classifier.py.")
else:
    # Sidebar-style Left Panel (Navigation)
    col_nav, col_content, col_actions = st.columns([1, 2, 1])

    with col_nav:
        st.markdown("### 📥 Queue")
        search = st.text_input("", placeholder="Search...", label_visibility="collapsed")
        
        # Filtering navigation list
        nav_df = df[df['subject'].str.contains(search, case=False)] if search else df
        
        # Selection Logic (Simulating a click)
        ticket_list = nav_df['subject'].tolist()
        selected_subject = st.radio("Select a ticket", ticket_list, label_visibility="collapsed")
        
        # Get the full data for the selected ticket
        selected_ticket = df[df['subject'] == selected_subject].iloc[0]

    with col_content:
        st.markdown(f"### 📄 Ticket #{selected_ticket['ticket_id']}")
        st.markdown(f"## {selected_ticket['subject']}")
        
        st.info(f"**Description:**\n\n{selected_ticket['description']}")
        
        with st.container():
            st.markdown("#### 🤖 AI Insights")
            st.write(f"**Sentiment:** {selected_ticket['sentiment']}")
            st.write(f"**Reasoning:** {selected_ticket['reasoning']}")
            st.progress(int(selected_ticket['confidence'])/100, text=f"Confidence: {selected_ticket['confidence']}%")

    with col_actions:
        st.markdown("### 🛠️ Actions")
        st.write("Review and verify the triage.")
        
        priority_options = ["low", "medium", "high", "urgent"]
        team_options = ["Support", "SRE", "Billing", "Dev", "Security Operations"]
        
        # Normalization
        curr_p = str(selected_ticket['priority']).lower().strip()
        p_idx = priority_options.index(curr_p) if curr_p in priority_options else 0
        
        new_p = st.selectbox("Confirm Priority", priority_options, index=p_idx)
        
        curr_t = str(selected_ticket['assigned_team']).strip()
        t_idx = team_options.index(curr_t) if curr_t in team_options else 0
        
        new_t = st.selectbox("Confirm Assignee", team_options, index=t_idx)
        
        st.divider()
        
        if st.button("✅ Verify & Next", use_container_width=True):
            conn = sqlite3.connect(DB_PATH)
            conn.execute("UPDATE ai_predictions SET priority=?, assigned_team=?, reviewed_status='human_reviewed' WHERE ticket_id=?", 
                         (new_p, new_t, selected_ticket['ticket_id']))
            conn.commit()
            conn.close()
            st.success("Triage Locked!")
            st.rerun()

    # Footer metrics
    st.sidebar.divider()
    st.sidebar.metric("Pending Review", len(df[df['reviewed_status'] == 'pending']))