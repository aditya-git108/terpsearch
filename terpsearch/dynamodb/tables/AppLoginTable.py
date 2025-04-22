import botocore.exceptions
from terpsearch.dynamodb.dynamodb_helpers import get_dynamodb_resource, get_dynamodb_client, table_exists
from terpsearch.constants.DynamoDbConstants import DynamoDbConstants


class LoginTable:

    def __init__(self, db_mode):
        self.dynamodb_resource = get_dynamodb_resource(db_mode=db_mode)
        self.dynamodb_client = get_dynamodb_client(db_mode=db_mode)

    def create_table(self):
        try:
            login_table_exists = table_exists(client=self.dynamodb_client,
                                              table_name=DynamoDbConstants.TERPSEARCH_LOGIN_TABLE_NAME)
            if login_table_exists is True:
                print(f'✅{DynamoDbConstants.TERPSEARCH_LOGIN_TABLE_NAME} table already exists')
                return
            else:
                print(f'🚧Creating {DynamoDbConstants.TERPSEARCH_LOGIN_TABLE_NAME}...')
                table = self.dynamodb_resource.create_table(
                    TableName=DynamoDbConstants.TERPSEARCH_LOGIN_TABLE_NAME,
                    KeySchema=[
                        {
                            'AttributeName': 'user_id',
                            'KeyType': 'HASH'  # Partition key
                        }
                    ],
                    AttributeDefinitions=[
                        {
                            'AttributeName': 'user_id',
                            'AttributeType': 'S'
                        },
                        {
                            'AttributeName': 'email',
                            'AttributeType': 'S'
                        }
                    ],
                    BillingMode='PROVISIONED',
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 2,
                        'WriteCapacityUnits': 2
                    },
                    GlobalSecondaryIndexes=[
                        {
                            'IndexName': 'username-index',
                            'KeySchema': [
                                {
                                    'AttributeName': 'email',
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
                print(f"{DynamoDbConstants.TERPSEARCH_LOGIN_TABLE_NAME} table created successfully.")
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print(f"⚠️ {DynamoDbConstants.TERPSEARCH_LOGIN_TABLE_NAME} is being created by another process. \
                Skipping.")
            else:
                print(f'🚨DynamoDB error when trying to create {DynamoDbConstants.TERPSEARCH_LOGIN_TABLE_NAME} table: {e}')