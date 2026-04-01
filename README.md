# 🛡️ AI-Powered Support Ticket Triage

An automated system that uses **Gemini 3 Flash** to classify, prioritize, and sentiment-analyze customer support tickets. 

## 🚀 Features
- **Automated Classification:** Categorizes tickets into Bug, Billing, SRE, etc.
- **Sentiment Analysis:** Detects frustrated or sarcastic customers.
- **Human-in-the-Loop:** A Streamlit dashboard for manual review of low-confidence predictions.
- **Resilient Pipeline:** State-aware processing that handles API rate limits gracefully.

## 🛠️ Setup
1. Clone the repo: `git clone <your-repo-link>`
2. Install dependencies: `pip install -r requirements.txt`
3. Add your `GOOGLE_API_KEY` to a `.env` file.
4. Run the classifier: `python3 classifier.py`
5. Launch the UI: `streamlit run ui/app_ui.py`