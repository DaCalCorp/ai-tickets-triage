import pandas as pd
import json
import sqlite3
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_ID = "models/gemini-3-flash-preview"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/{MODEL_ID}:generateContent?key={API_KEY}"

def classify_ticket(subject, description):
    prompt_text = f"Analyze this ticket and return ONLY a raw JSON object. Subject: {subject} Description: {description}. Required keys: category, priority, escalation_needed (bool), assigned_team, sentiment, confidence (int), reasoning."
    payload = {"contents": [{"parts": [{"text": prompt_text}]}], "generationConfig": {"responseMimeType": "application/json"}}
    
    try:
        response = requests.post(API_URL, json=payload)
        response_data = response.json()
        if "candidates" in response_data:
            content_text = response_data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(content_text)
        else:
            print(f"⚠️ Limit hit: {response_data.get('error', {}).get('message', 'Busy')}")
            return None
    except: return None

def run_triage_loop(csv_path, db_path):
    df = pd.read_csv(csv_path)
    conn = sqlite3.connect(db_path)
    
    # NEW: Create table if it doesn't exist so we can check progress
    conn.execute("CREATE TABLE IF NOT EXISTS ai_predictions (ticket_id INTEGER PRIMARY KEY, subject TEXT, description TEXT, category TEXT, priority TEXT, escalation_needed BOOLEAN, assigned_team TEXT, sentiment TEXT, confidence INTEGER, reasoning TEXT, reviewed_status TEXT)")
    
    print(f"🚀 Resuming Triage with {MODEL_ID}...")

    for index, row in df.iterrows():
        # NEW: Check if this ticket ID is already in the DB
        cursor = conn.execute("SELECT 1 FROM ai_predictions WHERE ticket_id = ?", (index,))
        if cursor.fetchone():
            continue # Skip if already done
            
        print(f"[{index + 1}/{len(df)}] Analyzing: {row['subject'][:30]}...")
        prediction = classify_ticket(row['subject'], row['description'])
        
        if prediction:
            prediction.update({'ticket_id': index, 'subject': row['subject'], 'description': row['description']})
            prediction['reviewed_status'] = "pending" if int(prediction.get('confidence', 0)) < 95 else "auto_approved"
            
            # Save this single ticket immediately
            res_df = pd.DataFrame([prediction])
            res_df.to_sql('ai_predictions', conn, if_exists='replace', index=False)
            print("✅ Progress saved.")
            
            # 12 seconds ensures we never hit the 20 RPM limit
            time.sleep(1) 
        else:
            print("🛑 Stopping loop to wait for quota reset. Run again in 1 minute.")
            break

    conn.close()

if __name__ == "__main__":
    run_triage_loop("data/sample_tickets.csv", "db/app.db")