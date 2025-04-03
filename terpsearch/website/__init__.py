from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from terpsearch.dynamodb.TerpSearchDb import TerpSearchDb
from terpsearch.dynamodb.dynamodb_helpers import table_exists,DynamoDbConstants
import boto3
from os import path

db = SQLAlchemy()
DB_NAME = "database.db"


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'final_terpsearch'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User

    # with app.app_context():
    #     db.create_all()
    create_database(app=app, db=db)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    bsky_dynamodb = TerpSearchDb()
    posts_table_exists = table_exists(client=bsky_dynamodb.client, table_name=DynamoDbConstants.BSKY_POSTS_TABLE_NAME)
    if posts_table_exists is False:
        bsky_dynamodb.create_bsky_posts_table()

    users_table_exists = table_exists(client=bsky_dynamodb.client, table_name=DynamoDbConstants.BSKY_USERS_TABLE_NAME)
    if users_table_exists is False:
        bsky_dynamodb.create_users_table()

    return app


def create_database(app, db):
    with app.app_context():
        db.create_all()
    # if not path.exists('website/' + DB_NAME):
    #     db.create_all()
    print('Created Database!')
