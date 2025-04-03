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

    def __init__(self):
        """
        Initializes a BskyPostsTable instance by making the DynamoDB resource and client objects readily available
        """
        self.dynamodb_resource = get_dynamodb_resource(mode=DynamoDbConstants.FLASK_MODE)
        self.dynamodb_client = get_dynamodb_client(mode=DynamoDbConstants.FLASK_MODE)

    def create_table(self, dynamodb_resource):
        """
        Creates a BskyPosts DynamoDB table with the necessary schema and a global secondary index.

        The table uses 'bskyUsername' as the partition key and 'bskyPostHash' as the sort key.
        The schema also defines a global secondary index on 'timelineDate' to support queries by date.

        Args:
            dynamodb_resource (boto3.resource): A Boto3 DynamoDB resource object to create a dynamodb table.

        Returns:
            None
        """
        table = dynamodb_resource.create_table(
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
                    'AttributeName': 'timelineDate',
                    'AttributeType': 'S'
                }
                # {
                #     'AttributeName': 'bskyPostClassification',
                #     'AttributeType': 'M'
                # },
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 1,
                'WriteCapacityUnits': 1
            },
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'timelineDateIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'timelineDate',
                            'KeyType': 'HASH'  # GSI partition key
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'  # Include all attributes in the index
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 1,
                        'WriteCapacityUnits': 1
                    }
                }
            ]
        )
        table.wait_until_exists()
        print(f"{DynamoDbConstants.BSKY_POSTS_TABLE_NAME} table created successfully.")
