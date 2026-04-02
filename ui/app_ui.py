import streamlit as st
import sqlite3
import pandas as pd
import os

# --- 1. SETUP & BRANDING ---
st.set_page_config(page_title="Support Ticket Audit Lab", layout="wide")

# --- 2. HIGH-CONTRAST DARK THEME ---
st.markdown("""
    <style>
    .stApp { background-color: #0f172a !important; }
    h1, h2, h3, p, span, label { color: #f8fafc !important; font-weight: 500 !important; }
    
    /* Kanban Column Styling */
    [data-testid="column"] {
        background-color: #1e293b;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #334155;
        min-height: 80vh;
    }
    
    /* Card/Expander Styling */
    .stExpander {
        background-color: #0f172a !important;
        border: 1px solid #3b82f6 !important;
        margin-bottom: 10px !important;
    }
    
    div[data-baseweb="select"] > div { background-color: #0f172a !important; color: #ffffff !important; }
    [data-testid="stMetricValue"] { color: #38bdf8 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATABASE CONNECTION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "db", "app.db")

def get_data():
    if not os.path.exists(DB_PATH): return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM ai_predictions", conn)
    conn.close()
    return df

st.title("🛡️ Support Ticket Audit Lab")
df = get_data()

if df.empty:
    st.error("❌ No data found. Run 'python3 classifier.py' first.")
else:
    # Top Stats
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Tickets", len(df))
    m2.metric("Pending Audit", len(df[df['reviewed_status'] == 'pending']))
    m3.metric("Verified", len(df[df['reviewed_status'] == 'human_reviewed']))

    st.divider()

    # --- 4. KANBAN COLUMNS ---
    # We define the order we want
    priorities = ["urgent", "high", "medium", "low"]
    cols = st.columns(4)
    
    priority_options = ["low", "medium", "high", "urgent"]
    team_options = ["Support", "SRE", "Billing", "Dev", "Security Operations"]

    for i, p_level in enumerate(priorities):
        with cols[i]:
            st.markdown(f"### {p_level.upper()}")
            # Filter data for this specific column
            subset = df[df['priority'].str.lower() == p_level]
            
            if subset.empty:
                st.caption("No tickets in this tier.")
            
            for _, row in subset.iterrows():
                # Card Header
                with st.expander(f"ID: {row['ticket_id']} | {row['subject'][:30]}..."):
                    st.markdown(f"**Description:** {row['description']}")
                    st.divider()
                    
                    # Small Vetting Actions inside the Card
                    new_p = st.selectbox("Priority", priority_options, 
                                        index=priority_options.index(