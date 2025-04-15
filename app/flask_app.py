from flask import Flask, render_template
from .analyzer import group_posts_by_period, summarize_trends
from .dynamodb_client import fetch_posts_for_last_n_weeks  # Optional, not currently used
from .mock_data import get_mock_posts  # Optional, not currently used
from .categorizer import CATEGORY_LABELS, CATEGORIZATION_LOG
from collections import defaultdict
import requests
from .data import get_real_posts
from .logger_config import logger  # ✅ Logger for tracking events

# --- Initialize Flask App ---
app = Flask(__name__, template_folder="./templates")

# --- Backend FastAPI endpoint for categorization ---
FASTAPI_URL = "http://127.0.0.1:8010/analyze_trends/"

# --- Main Dashboard Route ---
@app.route("/")
def index():
    """
    Homepage route that:
    - Loads posts from CSV
    - Sends them to FastAPI for categorization
    - Analyzes category trends over time
    - Renders the HTML dashboard with result visualizations
    """

    # Step 1: Load and clean real posts
    posts = get_real_posts()

    # Step 2: Send posts to FastAPI backend for categorization
    response = requests.post(FASTAPI_URL, json={"posts": posts})
    if response.status_code != 200:
        logger.error("❌ Error contacting backend FastAPI service")
        return "Error contacting backend", 500

    # Step 3: Receive categorized posts from backend
    categorized_posts = response.json()

    # Step 4: Analyze trends (group by week, summarize top categories)
    result = summarize_trends(group_posts_by_period(categorized_posts))
    result["weekly_counts"] = dict(sorted(result["weekly_counts"].items()))

    # Step 5: Log categorization summary for debugging
    logger.info("🔍 Categorization Summary:")
    for k, v in CATEGORIZATION_LOG.items():
        logger.info(f"  {k.replace('_', ' ').capitalize()}: {v}")

    # Step 6: Prepare data for pie chart visualization
    pie_data = defaultdict(int)
    for week in result['weekly_counts'].values():
        for cat, count in week.items():
            pie_data[cat] += count

    # Step 7: Render dashboard template with trend results
    return render_template("index.html", result=result, pie_data=pie_data)
