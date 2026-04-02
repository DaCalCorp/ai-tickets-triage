import streamlit as st
import sqlite3
import pandas as pd
import os

# --- 1. SETUP & LIGHT BRANDING ---
st.set_page_config(page_title="Support Ticket Audit Lab", layout="wide")

# --- 2. CREATIVE UI: ARCTIC GLASS THEME ---
st.markdown("""
    <style>
    /* Light Gradient Background */
    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    }
    
    /* Elegant Card Design */
    .ticket-card {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.5);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }

    /* Metric Styling */
    [data-testid="stMetricValue"] {
        color: #2563eb !important;
        font-weight: 700;
    }

    /* Priority Badges */
    .badge-urgent { background-color: #fee2e2; color: #991b1b; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }
    .badge-high { background-color: #ffedd5; color: #9a3412; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }
    .badge-medium { background-color: #dcfce7; color: #166534; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }
    .badge-low { background-color: #f1f5f9; color: #475569; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }
    
    /* Titles */
    h1, h2, h3 { color: #1e293b !important; font-family: 'Inter', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA CONNECTION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "db", "app.db")

def get_data():
    if not os.path.exists(DB_PATH): return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM ai_predictions", conn)
    conn.close()
    return df

st.title("🛡️ Ticket Audit Lab")
st.markdown("##### *Vetting the Intelligence behind your Support Queue*")

df = get_data()

if df.empty:
    st.warning("No tickets found. Run the classifier to begin.")
else:
    # 4. SMART FILTERING (The "Creative" touch)
    # Instead of columns, let's use a Filter Bar at the top
    col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
    search = col_f1.text_input("🔍 Search Subject or Keywords", "")
    filter_p = col_f2.multiselect("Filter Priority", ["urgent", "high", "medium", "low"], default=["urgent", "high"])
    
    # Filter the Data
    filtered_df = df[df['priority'].str.lower().isin(filter_p)]
    if search:
        filtered_df = filtered_df[filtered_df['subject'].str.contains(search, case=False)]

    st.divider()

    # 5. THE CARD FEED
    for index, row in filtered_df.iterrows():
        p_class = f"badge-{row['priority'].lower()}"
        
        # We use a container to create the "Card" feel
        with st.container():
            st.markdown(f"""
            <div class="ticket-card">
                <span class="{p_class}">{row['priority'].upper()}</span>
                <h3 style="margin-top:10px;">{row['subject']}</h3>
                <p style="color:#475569;">{row['description']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Action controls inside an expander for "Clean" look
            with st.expander("📝 Review AI Triage"):
                c1, c2, c3 = st.columns(3)
                
                new_p = c1.selectbox("Priority", ["low", "medium", "high", "urgent"], 
                                   index=["low", "medium", "high", "urgent