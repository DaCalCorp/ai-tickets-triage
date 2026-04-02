import streamlit as st
import sqlite3
import pandas as pd
import os

# --- 1. SETUP & THEME ---
st.set_page_config(page_title="Audit Command Center", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0d1117; }
    
    /* Panel Styling */
    [data-testid="column"] {
        background-color: #161b22;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #30363d;
        min-height: 85vh;
    }

    /* Text Colors */
    h1, h2, h3, p, span, label { color: #c9d1d9 !important; }
    
    /* Metrics Branding */
    [data-testid="stMetricValue"] { color: #58a6ff !important; font-size: 1.8rem !important; }
    
    /* Sidebar Radio Styling */
    div[data-testid="stRadio"] > label { font-weight: bold; color: #58a6ff !important; margin-bottom: 10px; }
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

if df.empty:
    st.warning("No data found. Run classifier.py.")
else:
    # --- 3. THE THREE-PANEL ARCHITECTURE (Adjusted Ratios) ---
    # Col 1: 0.7 (Narrow Navigation)
    # Col 2: 1.8 (Wider List)
    # Col 3: 2.5 (Action Focus)
    col_priority, col_list, col_detail = st.columns([0.7, 1.8, 2.5])

    # --- PANE 1: PRIORITY SELECTOR (With Live Counts) ---
    with col_priority:
        st.markdown("### 🏷️ Folders")
        
        # Calculate counts for each priority
        def get_count(p):
            return len(df[df['priority'].str.lower() == p.lower()])
        
        priorities = ["Urgent", "High", "Medium", "Low"]
        # Create labels like "Urgent (5)"
        priority_labels = [f"{p} ({get_count(p)})" for p in priorities]
        
        selected_p_label = st.radio("Select Level", priority_labels, label_visibility="collapsed")
        # Extract just the word "Urgent" from "Urgent (5)"
        selected_p = selected_p_label.split(" ")[0].lower()

    # --- PANE 2: TICKET LIST (Wider for Readability) ---
    with col_list:
        st.markdown(f"### 📋 {selected_p.upper()} List")
        list_df = df[df['priority'].str.lower() == selected_p]
        
        if list_df.empty:
            st.info("No tickets here.")
            selected_id = None
        else:
            # We show more of the subject now that the pane is wider
            list_df['display_name'] = list_df['ticket_id'].astype(str) + " | " + list_df['subject'].str.slice(0, 50)
            
            selected_display = st.radio("Choose Ticket", list_df['display_name'].tolist(), label_visibility="collapsed")
            selected_id = int(selected_display.split(" | ")[0])

    # --- PANE 3: THE FOCUS & ACTION AREA ---
    with col_detail:
        if selected_id:
            ticket = df[df['ticket_id'] == selected_id].iloc[0]
            
            st.markdown(f"### 📄 Ticket #{ticket['ticket_id']}")
            st.subheader(ticket['subject'])
            
            st.markdown("**Customer Message:**")
            st.info(ticket['description'])
            
            st.markdown("#### 🤖 AI Triage Reasoning")
            st.code(ticket['reasoning'], language=None)
            
            st.divider()
            
            # Action Controls
            c1, c2, c3 = st.columns(3)
            
            p_options = ["low", "medium", "high", "urgent"]
            t_options = ["Support", "SRE", "Billing", "Dev", "Security Operations"]
            
            new_p = c1.selectbox("Final Priority", p_options, index=p_options.index(ticket['priority'].lower()))
            
            curr_t = str(ticket['assigned_team']).strip()
            t_idx = t_options.index(curr_t) if curr_t in t_options else 0
            new_t = c2.selectbox("Final Team", t_options, index=t_idx)
            
            if c3.button("✅ Confirm", use_container_width=True):
                conn = sqlite3.connect(DB_PATH)
                conn.execute("UPDATE ai_predictions SET priority=?, assigned_team=?, reviewed_status='human_reviewed' WHERE ticket_id=?", 
                             (new_p, new_t, ticket['ticket_id']))
                conn.commit()
                conn.close()
                st.success("Triage Verified!")
                st.rerun()
        else:
            st.write("Select a folder and ticket to begin.")