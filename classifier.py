import pandas as pd
import json
import sqlite3
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()
GEMINI_KEY = os.getenv("GOOGLE_API_KEY")
OR_KEY = os.getenv("OPENROUTER_API_KEY")

def get_prediction(subject, description):
    prompt = f"Return ONLY a raw JSON object for this ticket. Subject: {subject} Description: {description}. Keys: category, priority, escalation_needed (bool), assigned_team, sentiment, confidence (int), reasoning."
    
    # --- TRY GEMINI FIRST ---
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={GEMINI_KEY}"
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=10)
        if res.status_code == 200:
            return json.loads(res.json()["candidates"][0]["content"]["parts"][0]["text"])
    except:
        pass

    # --- FAILOVER TO OPENROUTER FREE MODELS ---
    print(f"🔄 Gemini Busy. Using OpenRouter Free Tier...")
    headers = {
        "Authorization": f"Bearer {OR_KEY}",
        "HTTP-Referer": "http://localhost:3000", # Required by OpenRouter
        "X-Title": "AI Triage Project"
    }
    # 'openrouter/free' is a special ID that rotates through available free models
    payload = {
        "model": "openrouter/free", 
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=15)
        data = res.json()
        if 'choices' in data:
            content = data['choices'][0]['message']['content']
            # Clean JSON from markdown
            clean_json = content.replace('```json', '').replace('```', '').strip()
            return json.loads(clean_json)
        else:
            print(f"⚠️ Both APIs exhausted. Error: {data.get('error')}")
            return None
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return None

def run_triage():
    csv_path = "data/sample_tickets.csv"
    db_path = "db/app.db"
    df = pd.read_csv(csv_path)
    conn = sqlite3.connect(db_path)

    # Ensure table exists
    conn.execute("CREATE TABLE IF NOT EXISTS ai_predictions (ticket_id INTEGER PRIMARY KEY, subject TEXT, description TEXT, category TEXT, priority TEXT, escalation_needed BOOLEAN, assigned_team TEXT, sentiment TEXT, confidence INTEGER, reasoning TEXT, reviewed_status TEXT)")

    print(f"🚀 Resuming Triage for {len(df)} tickets...")

    for index, row in df.iterrows():
        # Check if already done
        if conn.execute("SELECT 1 FROM ai_predictions WHERE ticket_id = ?", (index,)).fetchone():
            continue

        print(f"[{index + 1}/{len(df)}] Analyzing: {row['subject'][:30]}...")
        pred = get_prediction(row['subject'], row['description'])
        
        if pred:
            pred.update({'ticket_id': index, 'subject': row['subject'], 'description': row['description'], 'reviewed_status': 'auto_approved'})
            pd.DataFrame([pred]).to_sql('ai_predictions', conn, if_exists='append', index=False)
            print("✅ Saved.")
        
        time.sleep(3) # Small delay to be polite to the free providers

    print("🎉 BATCH COMPLETE!")
    conn.close()

if __name__ == "__main__":
    run_triage()