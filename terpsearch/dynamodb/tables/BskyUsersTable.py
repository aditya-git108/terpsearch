from terpsearch.dynamodb.dynamodb_helpers import *
from terpsearch.constants.DynamoDbConstants import DynamoDbConstants
import botocore.exceptions


class BskyUsersTable:
    """
    Handles the dynamodb table schema used to create the BSKY_USERS DynamoDB table.

    This table is used to store and manage user-specific metadata required to interact with the Bluesky API.

    Stored metadata attributes include:
    1) Bluesky Username (bskyUsername): A unique identifier for the user's Bluesky handle
        ('user@gmail.com and/or 'user.bsky.social').
    2) Encrypted Session Token (session_token): A securely encrypted token used to authenticate and authorize Bluesky
        API requests on behalf of the user.
    3) Last Sync Timestamp (cursor_last_checked): An ISO 8601 UTC timestamp (e.g., '2025-04-03T15:55:39.665Z')
        indicating when the user's Bluesky feed was last synced.
    """

    def __init__(self, db_mode: str):
        """
        Initializes a BskyUsersTable instance by making the DynamoDB resource and client objects readily available
        """
        self.dynamodb_resource = get_dynamodb_resource(db_mode=db_mode)
        self.dynamodb_client = get_dynamodb_client(db_mode=db_mode)

    def create_table(self):
        """
        Creates the Bluesky users DynamoDB table with the following schema:
        - Partition Key: bskyUsername (String)

        This table is used to store user session metadata keyed by their Bluesky username.

        Returns:
            None
        """
        print(f'Creating {DynamoDbConstants.BSKY_USERS_TABLE_NAME}...')
        try:
            users_table_exists = table_exists(client=self.dynamodb_client,
                                              table_name=DynamoDbConstants.BSKY_USERS_TABLE_NAME)
            if users_table_exists is True:
                print(f'✅{DynamoDbConstants.BSKY_USERS_TABLE_NAME} table already exists')
                return
            else:
                table = self.dynamodb_resource.create_table(
                    TableName=DynamoDbConstants.BSKY_USERS_TABLE_NAME,
                    KeySchema=[
                        {
                            'AttributeName': 'bskyUsername',
                            'KeyType': 'HASH'  # Partition key
                        }
                    ],
                    AttributeDefinitions=[
                        {
                            'AttributeName': 'bskyUsername',
                            'AttributeType': 'S'
                        }
                    ],
                    BillingMode='PROVISIONED',
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 1,
                        'WriteCapacityUnits': 1
                    }
                )
                table.wait_until_exists()
                print(f"{DynamoDbConstants.BSKY_USERS_TABLE_NAME} table created successfully.")
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print(f"⚠️ {DynamoDbConstants.BSKY_USERS_TABLE_NAME} is being created by another process. Skipping.")
            else:
                print(f'🚨DynamoDB error when trying to create {DynamoDbConstants.BSKY_USERS_TABLE_NAME} table: {e}')
