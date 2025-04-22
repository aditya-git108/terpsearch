from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for, session
from flask_login import login_required, current_user
from terpsearch.search.bskySearch import TerpSearch
from terpsearch.dynamodb.TerpSearchDb import TerpSearchDb
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
            flash('The credentials passed matched a valid Bluesky account!', category='success')

            results = bsky_search.get_timeline_posts(bsky_username=bsky_email)

            print(f"({bsky_email}) -> Ingesting {len(results['posts'])} posts")

            response = requests.post(url=f'{FASTAPI_URL}/categorize/',
                                     json={'bsky_posts': results['posts'], 'bsky_username': bsky_email}
                                     )
            task_id = response.json()["task_id"]

            classifications = None
            # Poll for result
            for _ in range(20):
                result = requests.get(f"{FASTAPI_URL}/status/{task_id}").json()
                if result["status"].upper() == "SUCCESS":
                    classifications = result['result']
                    break
                time.sleep(15)
            print(f'({bsky_email}) -> Number of classified posts: {len(classifications)}')

            if len(classifications) > 0:
                bsky_dynamodb.batch_write_items(items=classifications,
                                                table_name=DynamoDbConstants.BSKY_POSTS_TABLE_NAME,
                                                user=bsky_email)

            # if len(classifications) > 0:
            #     print('Single writes...')
            #     counter = 0
            #     success_writes = 0
            #     for post in results['posts']:
            #         try:
            #             bsky_dynamodb.write_item(item=post, table_name=DynamoDbConstants.BSKY_POSTS_TABLE_NAME,
            #                                      user=bsky_email)
            #             success_writes = success_writes + 1
            #         except Exception as e:
            #             print(e)
            #             counter = counter + 1
            #     print(f'{success_writes}/{len(classifications)} items were written to the BSKY_POSTS')
            print(f'({bsky_email}) -> Fetched all bluesky posts')

        except Exception as e:
            flash(f'The given password isn\'t associated with the given email id', category='error')
            print(type(e))
            print(e)

    return render_template("home.html", user=current_user)

@views.route('/link_bluesky_acct', methods=['GET', 'POST'])
@login_required
def bsky_link():
    if request.method == 'POST':
        bsky_email = request.form.get('blueskyUsername')
        bsky_password = request.form.get('blueskyPassword')

        try:
            bsky_client = Client().login(login=bsky_email, password=bsky_password)
        except:
            flash('The given password isn\'t associated with the given email id', category='error')

        try:
            bsky_search = TerpSearch(username=bsky_email, password=bsky_password)
            results = bsky_search.get_timeline_posts(bsky_username=bsky_email, cursor_last_checked=None)
        except:
            print()

    return render_template("link_bluesky.html", user=current_user)
