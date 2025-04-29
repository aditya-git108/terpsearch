from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
# from . import db
from flask_login import login_user, login_required, logout_user, current_user
import uuid
from boto3.dynamodb.conditions import Key
from terpsearch.dynamodb.dynamodb_helpers import get_dynamodb_table, get_dynamodb_resource
from terpsearch.constants.DynamoDbConstants import DynamoDbConstants

auth = Blueprint('auth', __name__)
db_resource = get_dynamodb_resource(db_mode=DynamoDbConstants.DB_MODE)
login_table = get_dynamodb_table(dynamodb_resource=db_resource,
                                 table_name=DynamoDbConstants.TERPSEARCH_LOGIN_TABLE_NAME)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Query the user table to see whether the entered credentials match a valid account
        # user = User.query.filter_by(email=email).first()

        response = login_table.query(
            IndexName='username-index',
            KeyConditionExpression=Key('email').eq(email)
        )
        items = response.get('Items', [])

        if items:
            user_data = items[0]
            if check_password_hash(user_data['password'], password):
                user = User(user_data['user_id'], user_data['email'], user_data['bsky_email'], user_data['firstName'],
                            user_data['password'])
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist', category='error')
    return render_template('login.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You’ve been logged out.", "success")
    return redirect(url_for('auth.login'))


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        bsky_email = request.form.get('bsky_email')
        first_name = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        # Query the login table to see whether the entered credentials match a valid account
        response = login_table.query(
            IndexName='username-index',
            KeyConditionExpression=Key('email').eq(email)
        )
        user = response.get('Items', [])

        if user:
            flash('Email already exists', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(first_name) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            user_id = str(uuid.uuid4())
            password_hash = generate_password_hash(password1, method='pbkdf2:sha256:600000')

            new_user = User(user_id=user_id, email=email, bsky_email=bsky_email,
                            first_name=first_name, password_hash=password_hash)

            # Store user in DynamoDB
            login_table.put_item(Item={
                'user_id': user_id,
                'email': email,
                'bsky_email': bsky_email,
                'firstName': first_name,
                'password': password_hash
            })
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            return redirect(url_for('views.home'))

    # return render_template('sign_up.html', user=current_user)
    return render_template('sign_up.html')
