import streamlit as st
import sqlite3
import pandas as pd

# Set Page Config
st.set_page_config(page_title="Support Ticket Audit Lab", layout="wide")

# FORCE THE THEME: Slate Gray Background, High-Contrast White/Cyan Text
st.markdown("""
    <style>
    /* 1. Main Background */
    .stApp {
        background-color: #0f172a; 
    }
    
    /* 2. Global Text Brightness */
    h1, h2, h3, p, span, label {
        color: #f8fafc !important;
        font-weight: 500 !important;
    }

    /* 3. Dropdown (Selectbox) Styling - The Fix */
    div[data-baseweb="select"] > div {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 1px solid #3b82f6 !important;
    }
    
    /* Dropdown Options (the list that pops out) */
    div[data-baseweb="popover"] ul {
        background-color: #1e293b !important;
    }
    
    div[data-baseweb="popover"] li {
        color: #ffffff !important;
        background-color: #1e293b !important;
    }

    /* 4. Expander Styling */
    .stExpander {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
    }

    /* 5. Metrics Branding */
    [data-testid="stMetricValue"] {
        color: #38bdf8 !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ Support Ticket Audit Lab")
st.markdown("### Human-in-the-Loop Vetting & Quality Assurance")

# --- Rest of your data loading and loop code remains the same ---
# (Make sure to keep the "Normalization" logic we wrote to prevent the 'High' vs 'high' error)