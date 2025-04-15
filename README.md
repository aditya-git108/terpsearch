### Pipeline Flow

```
1. Data Source (CSV or DynamoDB)
         ↓
2. Data Cleaning & Timestamp Parsing (`data.py`)
         ↓
3. Categorization using Sentence Transformers (`categorizer.py`)
    - Semantic similarity via MiniLM embeddings
    - Keyword-based fallback
         ↓
4. Categorized Data Sent to FastAPI (`fastapi_app.py`)
         ↓
5. Trend Aggregation (`analyzer.py`)
    - Weekly grouping
    - Top category per week and overall
         ↓
6. Logging Confidence Scores (`confidenceScore_logger.py`)
         ↓
7. Flask Dashboard (`flask_app.py`)
    - Shows top category, pie chart, line chart
```

---

## Running This App

### 1.  Install Requirements

```bash
pip install -r requirements.txt
```

---

### 2. ▶ Run the FastAPI Backend

This handles NLP categorization.

```bash
python run.py fastapi
```

Runs FastAPI at: `http://127.0.0.1:8010/analyze_trends/`

---

### 3.  Run the Flask Frontend Dashboard

This shows weekly and overall trends.

Open a new terminal:

```bash
python run.py flask
```

Then go to `http://127.0.0.1:5000` in your browser.

---

##  Project Structure

```txt
app/
├── flask_app.py              # Flask UI for trends
├── fastapi_app.py            # FastAPI backend for categorization
├── analyzer.py               # Aggregates trends weekly and overall
├── categorizer.py            # NLP logic using MiniLM + keyword fallback
├── confidenceScore_logger.py # Logs confidence stats to CSV
├── data.py                   # Reads and cleans post data from CSV
├── logger_config.py          # Centralized logging setup
├── templates/index.html      # HTML dashboard (Jinja2 + Chart.js)
run.py                        # Entry point for running backend/frontend
requirements.txt              # Project dependencies
results.csv                   # Input data file with posts
```

---
\