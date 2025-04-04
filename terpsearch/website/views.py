from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user
from terpsearch.search.bskySearch import TerpSearch
from terpsearch.dynamodb.TerpSearchDb import TerpSearchDb
from terpsearch.constants.DynamoDbConstants import DynamoDbConstants
from terpsearch.dynamodb.dynamodb_helpers import *
# from .models import Note
from . import db
import json
from atproto import Client
from atproto.exceptions import BadRequestError

views = Blueprint('views', __name__)

bsky_dynamodb = TerpSearchDb()

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        bsky_email = request.form.get('blueskyUsername')
        bsky_password = request.form.get('blueskyPassword')

        client = Client()
        try:
            bsky_search = TerpSearch(bsky_client=client, username=bsky_email, password=bsky_password)
            flash('The credentials passed matched a valid Bluesky account!', category='success')

            results = bsky_search.get_timeline_posts(bsky_username=bsky_email)
            for post in results['posts']:
                bsky_dynamodb.write_item(item=post, table_name=DynamoDbConstants.BSKY_POSTS_TABLE_NAME,
                                         user=bsky_email)
            print(f'Fetched all bluesky posts for user: {bsky_email}')

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
