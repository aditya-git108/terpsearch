from flask import Flask, render_template
from .analyzer import group_posts_by_period, summarize_trends
from .dynamodb_client import fetch_posts_for_last_n_weeks
from .mock_data import get_mock_posts
from .categorizer import CATEGORY_LABELS, CATEGORIZATION_LOG
from collections import defaultdict
import requests
from .data import get_real_posts

app = Flask(__name__, template_folder="./templates")
FASTAPI_URL = "http://127.0.0.1:8010/analyze_trends/"

@app.route("/")
def index():
    posts = get_real_posts()

    # Send posts to FastAPI backend
    response = requests.post(FASTAPI_URL, json={"posts": posts})
    if response.status_code != 200:
        return "Error contacting backend", 500

    categorized_posts = response.json()  # This should contain categorized posts

    # Use backend results for analysis
    result = summarize_trends(group_posts_by_period(categorized_posts))

    result["weekly_counts"] = dict(sorted(result["weekly_counts"].items()))

    # Log categorization summary
    print("\n🔍 Categorization Summary:")
    for k, v in CATEGORIZATION_LOG.items():
        print(f"  {k.replace('_', ' ').capitalize()}: {v}")

    # Pie chart data prep
    pie_data = defaultdict(int)
    for week in result['weekly_counts'].values():
        for cat, count in week.items():
            pie_data[cat] += count

    return render_template("index.html", result=result, pie_data=pie_data)
