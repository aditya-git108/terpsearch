import botocore.exceptions
from terpsearch.dynamodb.dynamodb_helpers import *
from terpsearch.constants.DynamoDbConstants import DynamoDbConstants


class BskyPostsTable:
    """
    Handles the dynamodb table schema used to create the BSKY_POSTS DynamoDB table.

    This table is used to store posts that appear on a user's personal Bluesky feed.

    Each item in the table includes:
    - bskyPostHash: A unique identifier for the post.
    - text: The content of the post.
    - author: The post's author in the format of (e.g. FirstName LastName)
    - handle: The Bluesky handle of the post's author (e.g. author.bsky.social)
    - timestamp: A timestamp indicating when the post appeared on the user's timeline.
    """

    def __init__(self, db_mode):
        """
        Initializes a BskyPostsTable instance by making the DynamoDB resource and client objects readily available
        """
        self.dynamodb_resource = get_dynamodb_resource(db_mode=db_mode)
        self.dynamodb_client = get_dynamodb_client(db_mode=db_mode)

    def create_table(self):
        """
        Creates a BskyPosts DynamoDB table with the necessary schema and a global secondary index.

        The table uses 'bskyUsername' as the partition key and 'bskyPostHash' as the sort key.
        The schema also defines a global secondary index on 'timelineDate' to support queries by date.

        Returns:
            None
        """
        try:
            posts_table_exists = table_exists(client=self.dynamodb_client,
                                              table_name=DynamoDbConstants.BSKY_POSTS_TABLE_NAME)
            if posts_table_exists is True:
                print(f'✅{DynamoDbConstants.BSKY_POSTS_TABLE_NAME} table already exists')
                return
            else:
                print(f'🚧Creating {DynamoDbConstants.BSKY_POSTS_TABLE_NAME}...')
                table = self.dynamodb_resource.create_table(
                    TableName=DynamoDbConstants.BSKY_POSTS_TABLE_NAME,
                    KeySchema=[
                        {
                            'AttributeName': 'bskyUsername',
                            'KeyType': 'HASH'  # Partition key
                        },
                        {
                            'AttributeName': 'bskyPostHash',
                            'KeyType': 'RANGE'  # Sort key
                        }
                    ],
                    AttributeDefinitions=[
                        {
                            'AttributeName': 'bskyUsername',
                            'AttributeType': 'S'
                        },
                        {
                            'AttributeName': 'bskyPostHash',
                            'AttributeType': 'S'
                        },
                        {
                            'AttributeName': 'timestamp',
                            'AttributeType': 'S'
                        }
                        # {
                        #     'AttributeName': 'bskyPostClassification',
                        #     'AttributeType': 'M'
                        # },
                    ],
                    BillingMode='PAY_PER_REQUEST',
                    GlobalSecondaryIndexes=[
                        {
                            'IndexName': 'UserTimestampIndex',
                            'KeySchema': [
                                {
                                    'AttributeName': 'bskyUsername',
                                    'KeyType': 'HASH'
                                },
                                {
                                    'AttributeName': 'timestamp',
                                    'KeyType': 'RANGE'
                                }
                            ],
                            'Projection': {
                                'ProjectionType': 'INCLUDE',
                                'NonKeyAttributes': ['text', 'category']
                            }
                        }
                    ]
                )
                table.wait_until_exists()
                print(f"✅{DynamoDbConstants.BSKY_POSTS_TABLE_NAME} table created successfully.")

        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print(f"⚠️ {DynamoDbConstants.BSKY_POSTS_TABLE_NAME} is being created by another process. Skipping.")
            else:
                print(f'🚨DynamoDB error when trying to create {DynamoDbConstants.BSKY_POSTS_TABLE_NAME} table: {e}')
