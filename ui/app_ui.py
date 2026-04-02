import streamlit as st
import sqlite3
import pandas as pd

# Set Page Config
st.set_page_config(page_title="Support Ticket Audit Lab", layout="wide")

# FORCE THE THEME: Slate Gray Background, Bright White Text
st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background-color: #1e293b; 
    }
    /* All Text to White */
    h1, h2, h3, p, span, div, label {
        color: #ffffff !important;
    }
    /* Sidebar and Cards */
    .stExpander {
        background-color: #334155 !important;
        border: 1px solid #475569 !important;
        border-radius: 10px !important;
    }
    /* Metadata Boxes */
    .stStatusWidget {
        background-color: #0f172a !important;
        color: #ffffff !important;
    }
    /* Buttons */
    .stButton>button {
        background-color: #3b82f6 !important;
        color: white !important;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ Support Ticket Audit Lab")
st.markdown("### Human-in-the-Loop Vetting & Quality Assurance")

def get_data():
    conn = sqlite3.connect('db/app.db')
    df = pd.read_sql_query("SELECT * FROM ai_predictions", conn)
    conn.close()
    return df

df = get_data()

# Metrics Row
m1, m2, m3 = st.columns(3)
m1.metric("Total in Queue", len(df))
m2.metric("Pending Audit", len(df[df['reviewed_status'] == 'pending']))
m3.metric("Human Verified", len(df[df['reviewed_status'] == 'human_reviewed']))

st.divider()

# The Vetting Queue
st.subheader("🔍 Active Vetting Queue")

priority_options = ["low", "medium", "high", "urgent"]
team_options = ["Support", "SRE", "Billing", "Dev", "Security Operations"]

for index, row in df.iterrows():
    # FIX: Normalize the priority to lowercase so it matches our list
    current_p = str(row['priority']).lower().strip()
    if current_p not in priority_options:
        current_p = "medium" # Fallback if data is weird

    current_t = str(row['assigned_team']).strip()
    if current_t not in team_options:
        current_t = "Support" # Fallback

    label = f"[{current_p.upper()}] - {row['subject']}"
    
    with st.expander(label):
        col_text, col_action = st.columns([2, 1])
        
        with col_text:
            st.markdown(f"**Customer Message:** {row['description']}")
            with st.status("View AI Analysis"):
                st.write(f"**AI Reasoning:** {row['reasoning']}")
                st.write(f"**Detected Sentiment:** {row['sentiment']}")
                st.write(f"**Confidence Score:** {row['confidence']}%")

        with col_action:
            st.write("### Vetting Actions")
            
            # Use the normalized current_p for the index
            new_priority = st.selectbox("Correct Priority", priority_options, 
                                       index=priority_options.index(current_p), 
                                       key=f"p_{index}")
            
            new_team = st.selectbox("Correct Team", team_options, 
                                   index=team_options.index(current_t), 
                                   key=f"t_{index}")
            
            if st.button("Verify & Lock", key=f"btn_{index}"):
                conn = sqlite3.connect('db/app.db')
                conn.execute("""
                    UPDATE ai_predictions 
                    SET priority = ?, assigned_team = ?, reviewed_status = 'human_reviewed' 
                    WHERE ticket_id = ?
                """, (new_priority, new_team, row['ticket_id']))
                conn.commit()
                conn.close()
                st.success("Triage Verified.")
                st.rerun()