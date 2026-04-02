import streamlit as st
import sqlite3
import pandas as pd
import os

# --- 1. SETUP & BRANDING ---
st.set_page_config(page_title="Support Ticket Audit Lab", layout="wide")

# --- 2. HIGH-CONTRAST DARK THEME (The CSS) ---
st.markdown("""
    <style>
    /* Main Background: Deep Slate */
    .stApp {
        background-color: #0f172a !important; 
    }
    
    /* Force all base text to Bright White */
    h1, h2, h3, p, span, label, .stMarkdown {
        color: #f8fafc !important;
        font-weight: 500 !important;
    }

    /* Dropdown / Selectbox Container */
    div[data-baseweb="select"] > div {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 2px solid #3b82f6 !important; /* Blue border for visibility */
    }

    /* Dropdown Text inside the box */
    div[data-testid="stSelectbox"] p {
        color: #ffffff !important;
        font-size: 1.1rem !important;
    }
    
    /* The Popover Menu (when you click the dropdown) */
    div[data-baseweb="popover"] ul {
        background-color: #1e293b !important;
    }
    
    div[data-baseweb="popover"] li {
        color: #ffffff !important;
        background-color: #1e293b !important;
        border-bottom: 1px solid #334155;
    }

    /* Hover effect for dropdown options */
    div[data-baseweb="popover"] li:hover {
        background-color: #3b82f6 !important;
    }

    /* Metrics and Expanders */
    [data-testid="stMetricValue"] {
        color: #38bdf8 !important;
    }
    .stExpander {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }

    /* Buttons: Bright Blue */
    .stButton>button {
        background-color: #2563eb !important;
        color: white !important;
        border-radius: 8px;
        border: none;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATABASE CONNECTION (Absolute Path) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "db", "app.db")

def get_data():
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query("SELECT * FROM ai_predictions", conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df

# --- 4. DASHBOARD LOGIC ---
st.title("🛡️ Support Ticket Audit Lab")
st.markdown("### Human-in-the-Loop Vetting & Quality Assurance")

df = get_data()

if df.empty:
    st.error(f"❌ Database not found or empty at: {DB_PATH}")
    st.info("Please run 'python3 classifier.py' first to populate the database.")
else:
    # Metrics Header
    m1, m2, m3 = st.columns(3)
    m1.metric("Total in Queue", len(df))
    m2.metric("Pending Audit", len(df[df['reviewed_status'] == 'pending']))
    m3.metric("Human Verified", len(df[df['reviewed_status'] == 'human_reviewed']))

    st.divider()

    st.subheader("🔍 Active Vetting Queue")
    
    # Valid options for dropdowns
    priority_options = ["low", "medium", "high", "urgent"]
    team_options = ["Support", "SRE", "Billing", "Dev", "Security Operations"]

    for index, row in df.iterrows():
        # Normalization to prevent 'High' vs 'high' crashes
        current_p = str(row['priority']).lower().strip()
        if current_p not in priority_options:
            current_p = "medium"

        current_t = str(row['assigned_team']).strip()
        if current_t not in team_options:
            current_t = "Support"

        # The interactive card
        label = f"[{current_p.upper()}] - {row['subject']}"
        with st.expander(label):
            col_text, col_action = st.columns([2, 1])
            
            with col_text:
                st.markdown(f"**Customer Message:**\n{row['description']}")
                with st.status("🔍 View AI Analysis Details"):
                    st.write(f"**AI Reasoning:** {row['reasoning']}")
                    st.write(f"**Sentiment:** {row['sentiment']}")
                    st.write(f"**AI Confidence:** {row['confidence']}%")

            with col_action:
                st.markdown("#### Vetting Actions")
                
                # Correct Priority Dropdown
                new_priority = st.selectbox(
                    "Adjust Priority", 
                    priority_options, 
                    index=priority_options.index(current_p), 
                    key=f"p_{index}"
                )
                
                # Correct Team Dropdown
                new_team = st.selectbox(
                    "Assign Team", 
                    team_options, 
                    index=team_options.index(current_t), 
                    key=f"t_{index}"
                )
                
                if st.button("Verify & Lock", key=f"btn_{index}"):
                    conn = sqlite3.connect(DB_PATH)
                    conn.execute("""
                        UPDATE ai_predictions 
                        SET priority = ?, assigned_team = ?, reviewed_status = 'human_reviewed' 
                        WHERE ticket_id = ?
                    """, (new_priority, new_team, row['ticket_id']))
                    conn.commit()
                    conn.close()
                    st.success("Triage Verified!")
                    st.rerun()