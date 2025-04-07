# 🧠 NLP Trend Pipeline

> ⚠️ **Work in Progress**  
> This project is actively being developed.

A real-time NLP pipeline that analyzes Bluesky posts and identifies trending topics across categories like **tech**, **sports**, **politics**, and **entertainment**. Built for scalability and insight, the system uses semantic embeddings and keyword matching to categorize posts and track how topics evolve over time.

## 🚀 Features
- Semantic topic classification using MiniLM embeddings
- Fallback keyword-based categorization
- Weekly trend analysis by topic
- Interactive Flask dashboard with Chart.js visualizations

## 🛠 Tech Stack
- Python, FastAPI (API)
- Flask, Chart.js, Bootstrap (frontend)
- SentenceTransformers (MiniLM)



## ⚙️ How to Run

```bash
# Clone the repo
git clone https://github.com/Anagha-0010/nlp-trend-pipeline.git
cd nlp-trend-pipeline

# Set up environment
pip install -r requirements.txt

# Start the FastAPI backend
uvicorn app.main:app --reload


