from flask import Blueprint, render_template, request, flash, session, redirect, url_for
from flask_login import login_required, current_user
from terpsearch.search.bskySearch import TerpSearch
from terpsearch.dynamodb.TerpSearchDb import TerpSearchDb
from terpsearch.constants.DynamoDbConstants import DynamoDbConstants
from terpsearch.dynamodb.dynamodb_helpers import *
from boto3.dynamodb.conditions import Key, Attr
from collections import Counter
import random


trends = Blueprint('trends', __name__)

bsky_dynamodb = TerpSearchDb(db_mode=DynamoDbConstants.DB_MODE)
FASTAPI_URL = DynamoDbConstants.FASTAPI_URL


def get_category_counts(posts):
    category_counter = Counter()
    for post in posts:
        for cat in post.get('category', []):
            category_counter[cat] += 1
    return category_counter


def generate_color_palette(n):
    base_colors = [
        "rgba(75, 192, 192, 0.5)",
        "rgba(255, 99, 132, 0.5)",
        "rgba(255, 206, 86, 0.5)",
        "rgba(54, 162, 235, 0.5)",
        "rgba(153, 102, 255, 0.5)",
        "rgba(255, 159, 64, 0.5)",
        "rgba(201, 203, 207, 0.5)"
    ]
    return [random.choice(base_colors) for _ in range(n)]


@trends.route('/search_trends', methods=['GET', 'POST'])
@login_required
def search_trends():
    posts_table = get_dynamodb_table(dynamodb_resource=bsky_dynamodb.dynamodb_resource,
                                     table_name=DynamoDbConstants.BSKY_POSTS_TABLE_NAME)
    if request.method == 'POST':
        bsky_username = request.form.get('bsky_username')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        session['bsky_username'] = bsky_username
        session['start_date'] = start_date
        session['end_date'] = end_date

        # Redirect to a clean URL with no visible params
        return redirect(url_for('trends.timeline_trends'))


@trends.route('/trends')
@login_required
def timeline_trends():
    posts_table = get_dynamodb_table(dynamodb_resource=bsky_dynamodb.dynamodb_resource,
                                     table_name=DynamoDbConstants.BSKY_POSTS_TABLE_NAME)

    # Pull values from session and clear session so that old values won't be reused when refreshing the page
    bsky_username = session.pop('bsky_username', None)
    start_date = session.pop('start_date', None)
    end_date = session.pop('end_date', None)

    # If user hasn't submitted the form yet
    if not (bsky_username and start_date and end_date):
        return render_template("trends_base.html", user=current_user)

    # Convert to both dates to full ISO 8601 timestamps (to match DynamoDB timestamp)
    start_iso = f"{start_date}T00:00:00Z"
    end_iso = f"{end_date}T23:59:59Z"

    response = posts_table.query(
        IndexName='UserTimestampIndex',
        KeyConditionExpression=Key('bskyUsername').eq(bsky_username) & Key('timestamp').between(start_iso, end_iso)
    )

    posts = response['Items']

    # Prepare chart data
    counts = get_category_counts(posts)
    labels = list(counts.keys())
    values = list(counts.values())

    colors = generate_color_palette(n=len(labels))

    return render_template('category_chart.html',
                           user=current_user,
                           chart_labels=labels,
                           chart_values=values,
                           chart_colors=colors,
                           start_date=start_date,
                           end_date=end_date
                           )
