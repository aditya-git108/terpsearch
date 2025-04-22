import boto3
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_session import Session
from terpsearch.dynamodb.TerpSearchDb import TerpSearchDb
from terpsearch.dynamodb.dynamodb_helpers import (table_exists, DynamoDbConstants, get_dynamodb_resource,
                                                  get_dynamodb_client, get_dynamodb_table)
import redis

# db = SQLAlchemy()
# DB_NAME = "database.db"
db_resource = get_dynamodb_resource(db_mode=DynamoDbConstants.DB_MODE)
db_client = get_dynamodb_client(db_mode=DynamoDbConstants.DB_MODE)


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'final_terpsearch'

    # Configure Redis for session storage
    app.config['SESSION_TYPE'] = 'redis'
    app.config['SESSION_REDIS'] = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    app.config['SESSION_PERMANENT'] = False  # Optional: make session expire on browser close
    Session(app)
    # app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    # db.init_app(app)

    from .views import views
    from .auth import auth
    from .trends import trends

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(trends, url_prefix='/')

    from .models import User

    # with app.app_context():
    #     db.create_all()
    # create_database(app=app, db=db)
    bsky_dynamodb = TerpSearchDb(db_mode=DynamoDbConstants.DB_MODE)
    print('Initializing Terpsearch Database...')

    login_table_exists = table_exists(client=db_client, table_name=DynamoDbConstants.TERPSEARCH_LOGIN_TABLE_NAME)
    if login_table_exists is False:
        bsky_dynamodb.create_login_table()

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    login_table = get_dynamodb_table(dynamodb_resource=db_resource,
                                     table_name=DynamoDbConstants.TERPSEARCH_LOGIN_TABLE_NAME)

    @login_manager.user_loader
    def load_user(user_id):
        response = login_table.get_item(Key={'user_id': user_id})
        item = response.get('Item')
        if item:
            return User(user_id=item['user_id'], email=item['email'], first_name=item['firstName'],
                        password_hash=item['password'])
        return None

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
