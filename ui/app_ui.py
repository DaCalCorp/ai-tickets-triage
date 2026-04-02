import streamlit as st
import sqlite3
import pandas as pd

# Set Page Config for Branding
st.set_page_config(page_title="Support Ticket Vetting Lab", layout="wide")

# Custom CSS for the "Command Center" look
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #fafafa; }
    div[data-testid="stMetricValue"] { color: #00d4ff; }
    .stExpander { border: 1px solid #262730; border-radius: 10px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ Support Ticket Vetting Lab")
st.caption("AI-Powered Triage Audit & Human-in-the-Loop Vetting")

def get_data():
    conn = sqlite3.connect('db/app.db')
    # Pulling only what we need for the audit
    query = "SELECT ticket_id, subject, description, priority, category, sentiment, assigned_team, reviewed_status, reasoning FROM ai_predictions"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

df = get_data()

# --- HIGH-LEVEL METRICS ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Tickets", len(df))
m2.metric("Pending Review", len(df[df['reviewed_status'] == 'pending']))
m3.metric("Auto-Approved", len(df[df['reviewed_status'] == 'auto_approved']))
m4.metric("Human Vetted", len(df[df['reviewed_status'] == 'human_reviewed']))

st.divider()

# --- VETTING QUEUE ---
st.subheader("🔍 Active Audit Queue")
st.info("Expand a ticket to review AI reasoning and confirm or adjust the triage.")

for index, row in df.iterrows():
    # Header logic: Show Priority and Subject
    header = f"{row['priority'].upper()} | {row['subject']}"
    
    with st.expander(header):
        # Description and Reasoning are the most important context
        st.write(f"**Customer Message:** {row['description']}")
        st.write(f"**AI Reasoning:** *{row['reasoning']}*")
        
        st.divider()
        
        # Action Area
        c1, c2, c3 = st.columns(3)
        
        new_priority = c1.selectbox("Adjust Priority", ["low", "medium", "high", "urgent"], 
                                   index=["low", "medium", "high", "urgent"].index(row['priority']), 
                                   key=f"p_{index}")
        
        new_team = c2.selectbox("Reassign Team", ["Support", "SRE", "Billing", "Dev", "Security Operations"], 
                               index=["Support", "SRE", "Billing", "Dev", "Security Operations"].index(row['assigned_team']), 
                               key=f"t_{index}")
        
        # Submit Button
        if c3.button("Confirm & Vet Ticket", key=f"btn_{index}"):
            conn = sqlite3.connect('db/app.db')
            conn.execute("""
                UPDATE ai_predictions 
                SET priority = ?, assigned_team = ?, reviewed_status = 'human_reviewed' 
                WHERE ticket_id = ?
            """, (new_priority, new_team, row['ticket_id']))
            conn.commit()
            conn.close()
            st.success(f"Ticket #{row['ticket_id']} Vetted!")
            st.rerun()