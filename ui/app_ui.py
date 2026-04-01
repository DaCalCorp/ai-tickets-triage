import streamlit as st
import sqlite3
import pandas as pd

# Set page config
st.set_page_config(page_title="AI Ticket Triage", layout="wide")

st.title("🛡️ AI Support Ticket Triage & Annotation")
st.markdown("Review AI classifications and provide human corrections below.")

# 1. Connect to our Database
def load_data():
    conn = sqlite3.connect('db/app.db')
    df = pd.read_sql_query("SELECT * FROM ai_predictions", conn)
    conn.close()
    return df

try:
    df = load_data()

    # 2. Sidebar Metrics
    st.sidebar.header("Triage Metrics")
    st.sidebar.metric("Total Tickets", len(df))
    st.sidebar.metric("Pending Review", len(df[df['reviewed_status'] == 'pending']))
    
    # 3. The Ticket List
    st.subheader("All AI-Classified Tickets")
    
    # We use st.data_editor so you can actually edit the values in the table!
    edited_df = st.data_editor(
        df,
        column_config={
            "confidence": st.column_config.ProgressColumn(
                "Confidence", help="AI Confidence Score", min_value=0, max_value=100, format="%d"
            ),
            "priority": st.column_config.SelectboxColumn(
                "Priority", options=["low", "medium", "high", "urgent"]
            ),
            "reviewed_status": st.column_config.SelectboxColumn(
                "Status", options=["pending", "auto_approved", "human_verified"]
            )
        },
        disabled=["ticket_id", "subject", "description"], # Don't let user change the raw ticket
        hide_index=True,
    )

    # 4. Save Corrections
    if st.button("💾 Save Human Corrections"):
        conn = sqlite3.connect('db/app.db')
        edited_df.to_sql('ai_predictions', conn, if_exists='replace', index=False)
        conn.close()
        st.success("Database updated with human annotations!")
        st.balloons()

except Exception as e:
    st.error(f"Could not load database. Did you run the classifier script first? Error: {e}")

# 5. Detail View
st.divider()
st.subheader("Deep Dive Reasoning")
if not df.empty:
    selected_subject = st.selectbox("Select a ticket to see AI reasoning:", df['subject'])
    reason = df[df['subject'] == selected_subject]['reasoning'].values[0]
    st.info(f"**AI Logic:** {reason}")
