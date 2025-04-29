from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for, session
from flask_login import login_required, current_user
from terpsearch.search.bskySearch import TerpSearch
from terpsearch.dynamodb.TerpSearchDb import TerpSearchDb
from celery.result import AsyncResult
from fastapi_categorizer.celery_worker import celery_app
from terpsearch.constants.DynamoDbConstants import DynamoDbConstants
from terpsearch.dynamodb.dynamodb_helpers import *
from boto3.dynamodb.conditions import Key
import requests
import time
# from .models import Note
# from . import db
import json
from atproto import Client
from atproto.exceptions import BadRequestError

views = Blueprint('views', __name__)

bsky_dynamodb = TerpSearchDb(db_mode=DynamoDbConstants.DB_MODE)
FASTAPI_URL = DynamoDbConstants.FASTAPI_URL


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        bsky_email = request.form.get('blueskyUsername')
        bsky_password = request.form.get('blueskyPassword')

        client = Client()
        try:
            bsky_search = TerpSearch(bsky_client=client, username=bsky_email, password=bsky_password,
                                     db_mode=DynamoDbConstants.DB_MODE)
            results = bsky_search.get_timeline_posts(bsky_username=bsky_email)

            print(f"({bsky_email}) -> Ingesting {len(results['posts'])} posts")

            response = requests.post(url=f'{FASTAPI_URL}/categorize/',
                                     json={'bsky_posts': results['posts'], 'bsky_username': bsky_email}
                                     )
            task_id = response.json()["task_id"]
            flash("Posts submitted for classification! Please check back shortly.", category='success')
            # return redirect(url_for("views.home"))
            return redirect(url_for("views.task_status_page", task_id=task_id))

        except Exception as e:
            flash(f'The given password isn\'t associated with the given email id', category='error')
            print(type(e))
            print(e)

    return render_template("home.html")


@views.route('/task_status/<task_id>')
@login_required
def task_status_page(task_id):
    return render_template('task_status.html', task_id=task_id)


@views.route('/check_task/<task_id>', methods=['GET'])
@login_required
def check_task(task_id):
    task_result = AsyncResult(task_id, app=celery_app)

    if task_result.state == 'PENDING':
        status = 'pending'
    elif task_result.state == 'SUCCESS':
        status = 'success'
    elif task_result.state == 'FAILURE':
        status = 'failure'
    else:
        status = task_result.state.lower()

    return jsonify({'status': status})


@views.route('/update_bluesky_acct', methods=['GET', 'POST'])
@login_required
def bsky_link():
    if request.method == 'POST':
        bsky_email = request.form.get('new_bsky_email')
        bsky_password = request.form.get('bsky_password1')

        client = Client()
        try:
            bsky_client = client.login(login=bsky_email, password=bsky_password)
        except:
            flash('The given password isn\'t associated with the given email id', category='error')

        try:
            bsky_search = TerpSearch(bsky_client=client, username=bsky_email, password=bsky_password,
                                     db_mode=DynamoDbConstants.DB_MODE)
            results = bsky_search.get_timeline_posts(bsky_username=bsky_email)
        except:
            print('There was an issue updating your bluesky email')

    return render_template("link_bluesky.html")


@views.route('/health', methods=['GET'])
def health():
    return "Healthy!", 200
