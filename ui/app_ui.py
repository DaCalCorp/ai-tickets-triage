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
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #30363d;
        min-height: 85vh;
    }

    /* Text Colors */
    h1, h2, h3, p, span, label { color: #c9d1d9 !important; }
    
    /* Sidebar Radio Styling */
    div[data-testid="stRadio"] > label { font-weight: bold; color: #58a6ff !important; }
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
    # --- 3. THE THREE-PANEL ARCHITECTURE ---
    # Col 1: Priority Picker | Col 2: Ticket List | Col 3: Details & Actions
    col_priority, col_list, col_detail = st.columns([0.8, 1.5, 2.2])

    # --- PANE 1: PRIORITY SELECTOR ---
    with col_priority:
        st.markdown("### 🏷️ Priority")
        all_priorities = ["Urgent", "High", "Medium", "Low"]
        selected_p = st.radio("Select Level", all_priorities, label_visibility="collapsed")
        
        st.divider()
        st.metric("Total Count", len(df[df['priority'].str.lower() == selected_p.lower()]))

    # --- PANE 2: TICKET LIST (Filtered by Pane 1) ---
    with col_list:
        st.markdown(f"### 📋 {selected_p} Tickets")
        list_df = df[df['priority'].str.lower() == selected_p.lower()]
        
        if list_df.empty:
            st.info("No tickets in this category.")
            selected_id = None
        else:
            # Create a clean display string for the list
            list_df['display_name'] = list_df['ticket_id'].astype(str) + ": " + list_df['subject'].str.slice(0, 30) + "..."
            
            # Select individual ticket
            selected_display = st.radio("Choose Ticket", list_df['display_name'].tolist(), label_visibility="collapsed")
            selected_id = int(selected_display.split(":")[0])

    # --- PANE 3: THE FOCUS & ACTION AREA ---
    with col_detail:
        if selected_id:
            ticket = df[df['ticket_id'] == selected_id].iloc[0]
            
            st.markdown(f"### 📄 Ticket #{ticket['ticket_id']}")
            st.subheader(ticket['subject'])
            
            st.markdown(f"**Description:**")
            st.info(ticket['description'])
            
            with st.status("🤖 AI Analysis Detail", expanded=True):
                st.write(f"**Reasoning:** {ticket['reasoning']}")
                st.write(f"**Sentiment:** {ticket['sentiment']}")
                st.progress(int(ticket['confidence'])/100, text=f"Confidence: {ticket['confidence']}%")
            
            st.divider()
            
            # Vetting Controls
            c1, c2, c3 = st.columns(3)
            
            priority_options = ["low", "medium", "high", "urgent"]
            team_options = ["Support", "SRE", "Billing", "Dev", "Security Operations"]
            
            new_p = c1.selectbox("Priority", priority_options, index=priority_options.index(ticket['priority'].lower()))
            
            curr_t = str(ticket['assigned_team']).strip()
            t_idx = team_options.index(curr_t) if curr_t in team_options else 0
            new_t = c2.selectbox("Team", team_options, index=t_idx)
            
            if c3.button("✅ Confirm", use_container_width=True):
                conn = sqlite3.connect(DB_PATH)
                conn.execute("UPDATE ai_predictions SET priority=?, assigned_team=?, reviewed_status='human_reviewed' WHERE ticket_id=?", 
                             (new_p, new_t, ticket['ticket_id']))
                conn.commit()
                conn.close()
                st.success("Triage Updated!")
                st.rerun()
        else:
            st.write("Select a ticket to view details.")