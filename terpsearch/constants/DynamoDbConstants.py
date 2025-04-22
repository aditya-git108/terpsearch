import os


class DynamoDbConstants:
    BSKY_POSTS_TABLE_NAME = 'BSKY_POSTS'
    BSKY_USERS_TABLE_NAME = 'BSKY_USERS'
    TERPSEARCH_LOGIN_TABLE_NAME = 'LOGIN'
    DYNAMODB_REGION = 'us-east-1'
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY_ID = os.getenv('AWS_SECRET_ACCESS_KEY')
    FASTAPI_URL = os.getenv('FASTAPI_URL', 'http://localhost:8010')
    DYNAMODB_URL = os.getenv('DYNAMODB_URL', 'http://localhost:8000')
    DYNAMODB_DEV_URL = 'http://localhost:8000'
    DB_MODE = os.getenv('DB_MODE', 'DEV')
    FERNET_KEY = 'FERNET_KEY'
