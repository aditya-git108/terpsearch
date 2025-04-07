from flask import Flask, render_template
from .analyzer import group_posts_by_period, summarize_trends
from .dynamodb_client import fetch_posts_for_last_n_weeks
from .mock_data import get_mock_posts
from .categorizer import CATEGORY_LABELS
from collections import defaultdict

app = Flask(__name__, template_folder="./templates")

@app.route("/")
def index():
    posts = get_mock_posts()
    #posts = fetch_posts_for_last_n_weeks(weeks=4)
    result = summarize_trends(group_posts_by_period(posts))

    #  Sort the weekly counts by date
    result["weekly_counts"] = dict(sorted(result["weekly_counts"].items()))

    pie_data = defaultdict(int)
    for week in result['weekly_counts'].values():
        for cat, count in week.items():
            pie_data[cat] += count

    return render_template("index.html", result=result, pie_data=pie_data)
