import atproto
import boto3
import uuid
from terpsearch.constants.DynamoDbConstants import DynamoDbConstants
from terpsearch.dynamodb.BskySessionEncryptor import BskySessionEncryptor
from atproto.exceptions import AtProtocolError


def get_dynamodb_resource(mode: str):
    """
    Returns a boto3 DynamoDB resource configured for the given environment.

    Args:
        mode (str): Deployment mode. Use 'PROD' for production; otherwise, development settings are used.

    Returns:
        boto3.resources.factory.dynamodb.ServiceResource: A DynamoDB resource object.
    """
    endpoint = (DynamoDbConstants.DYNAMODB_URL
                if mode.upper() == 'PROD'
                else DynamoDbConstants.DYNAMODB_DEV_URL)

    return boto3.resource(
        'dynamodb',
        region_name='ap-southeast-1',
        aws_access_key_id='dummy',
        aws_secret_access_key='dummy',
        endpoint_url=endpoint
    )


def get_dynamodb_client(mode: str):
    """
    Returns a low-level boto3 DynamoDB client configured for the given environment.

    Args:
        mode (str): Deployment mode. Use 'PROD' for production; otherwise, development settings are used.

    Returns:
        botocore.client.DynamoDB: A DynamoDB client object.
    """
    endpoint = (DynamoDbConstants.DYNAMODB_URL
                if mode.upper() == 'PROD'
                else DynamoDbConstants.DYNAMODB_DEV_URL)

    return boto3.client(
        'dynamodb',
        region_name='ap-southeast-1',
        aws_access_key_id='dummy',
        aws_secret_access_key='dummy',
        endpoint_url=endpoint
    )


def get_dynamodb_table(dynamodb_resource: boto3.resource, table_name: str):
    """
    Retrieves a reference to a DynamoDB table by name using a provided resource.

    Args:
        dynamodb_resource (boto3.resource): The DynamoDB resource object.
        table_name (str): The name of the table to access.

    Returns:
        boto3.dynamodb.Table: The table object reference.
    """
    table = dynamodb_resource.Table(table_name)
    return table


def table_exists(client: boto3.client, table_name: str):
    """
    Checks whether a DynamoDB table exists.

    Args:
        client (boto3.client): The DynamoDB client object.
        table_name (str): The name of the table to check.

    Returns:
        bool: True if the table exists, False otherwise.
    """
    exists = False
    tables = client.list_tables()

    if table_name in tables['TableNames']:
        exists = True

    return exists


def stable_hash(input: str):
    """
    Generates a deterministic UUID based on the input string using UUIDv5.

    Args:
        input (str): The input string to hash (e.g., post text).

    Returns:
        str: A UUIDv5-based hash string.
    """
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, input))


def get_user_cursor(table, username):
    return


def create_session(client: atproto.Client, bsky_username: str, bsky_password: str, table):
    """
    Authenticates a new Bluesky client session and stores the encrypted session token in DynamoDB.

    If the login is successful, the session is encrypted and written to the BSKY_USERS table under the
    'session_token' attribute.

    Args:
        client (atproto.Client): An unauthenticated Bluesky client.
        bsky_username (str): The user's Bluesky handle.
        bsky_password (str): The user's Bluesky app password.
        table (boto3.resources.factory.dynamodb.Table): The DynamoDB users table.

    Returns:
        atproto.Client or None: The authenticated client if successful; None otherwise.
    """
    try:
        print(f'Creating new session for {bsky_username}')
        encryptor = BskySessionEncryptor()
        client.login(bsky_username, bsky_password)
        print('Authenticated bluesky API client...')
        session_token = client.export_session_string()
        table.update_item(
            Key={'bskyUsername': bsky_username},
            UpdateExpression='SET session_token = :token',
            ExpressionAttributeValues={
                ':token': encryptor.encrypt(session_token)
            }
        )
        print(f'Added an active session token for {bsky_username}')
        print("Logged in successfully!")
        return client
    except AttributeError:
        print('Failed to find BskySessionEncryptor() key when creating a new session')
        return None
    except AtProtocolError as e:
        print("Login failed:", e)
        return None
