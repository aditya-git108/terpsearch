from boto3.dynamodb.conditions import Attr
from terpsearch.dynamodb.dynamodb_helpers import *
from terpsearch.dynamodb.tables.BskyPostsTable import BskyPostsTable
from terpsearch.dynamodb.tables.BskyUsersTable import BskyUsersTable
from terpsearch.dynamodb.tables.AppLoginTable import LoginTable
from terpsearch.constants.DynamoDbConstants import DynamoDbConstants
from terpsearch.search.bskySearch import TerpSearch
from botocore.exceptions import ClientError


class TerpSearchDb:
    """
    A class used to manage all Bluesky-related data as NoSQL tables in DynamoDB for the TerpSearch application.

    This class encapsulates operations for creating tables, formatting items, and writing Bluesky post data
    into the DynamoDB instance for the TerpSearch application. It uses helper classes and utilities for interacting with
    DynamoDB in a structured way.
    """

    def __init__(self, db_mode: str):
        """
        Initializes a TerpSearchDb instance by making the DynamoDB resource and client objects readily available
        """
        self.db_mode = db_mode
        self.dynamodb_resource = get_dynamodb_resource(db_mode=db_mode)
        self.client = get_dynamodb_client(db_mode=db_mode)

    def create_login_table(self):
        login_table = LoginTable(db_mode=self.db_mode)
        login_table.create_table()

    def create_bsky_posts_table(self):
        """
        Creates the BSKY_POSTS table in DynamoDB using the configured DynamoDB resource.
        """
        bsky_posts_table = BskyPostsTable(db_mode=self.db_mode)
        bsky_posts_table.create_table()

    def create_users_table(self):
        """
        Creates the BSKY_USERS table in DynamoDB using the configured DynamoDB resource.
        """
        cursor_table = BskyUsersTable(db_mode=self.db_mode)
        cursor_table.create_table()

    def __create_db_item(self, bsky_username: str, item: dict):
        """
        Formats a Bluesky post into a TerpSearch DynamoDB-compatible item by attaching the required keys (bskyUsername
        and bskyPostHash).

        The `bskyPostHash` is generated using a stable hashing function to uniquely identify each post by
        its text content.

        This method functions as a helper method for write_item()

        Args:
            bsky_username (str): The Bluesky username.
            item (dict): The original post data from a user's bluesky feed.

        Returns:
            dict: The item formatted for TerpSearch DynamoDB tables.
        """
        post_hash = stable_hash(input=item['text'])
        item_header = {'bskyUsername': bsky_username, 'bskyPostHash': post_hash}
        db_item = dict(item_header, **item)
        return db_item

    def write_item(self, item: dict, table_name: str, user: str):
        """
        Writes a post item to a specified DynamoDB table, using the given Bluesky username and a stable hash of
        the post's text.

        This method uses a conditional expression to ensure that duplicate items (based on the same user and post hash)
        are not inserted multiple times. If the item already exists, it will silently skip insertion.
        Other DynamoDB errors are logged.

        Args:
            item (dict): The Bluesky post data to insert into the database.
            table_name (str): The name of the DynamoDB table where the item should be stored.
            user (str): The Bluesky username associated with the post.

        Raises:
            ClientError: If there is a failure inserting the item that is not due to an existing record.

        Example:
            post = {'text': 'Hello from Bluesky!', 'created_at': '2024-03-30T12:00:00Z'}
            db.write_item(post, table_name='BskyPostsTable', user='user.bsky.social')
        """
        posts_table = get_dynamodb_table(dynamodb_resource=self.dynamodb_resource,
                                         table_name=table_name)

        try:
            db_item = self.__create_db_item(bsky_username=user, item=item)
            posts_table.put_item(
                Item=db_item,
                ConditionExpression="attribute_not_exists(bskyUsername) AND attribute_not_exists(bskyPostHash)"
            )
            # print("Item added successfully.")
        except ClientError as e:
            if e.response['Error']['Code'] != 'ConditionalCheckFailedException':
                print("Error inserting item:", e)
            # else:
            #     print("Item already exists. Skipping insertion.")


    def batch_write_items(self, items: list, table_name: str, user: str):
        """
        Batch writes multiple post items to DynamoDB, skipping any duplicates based on conditional checks.

        Args:
            items (List[Dict]): List of Bluesky post dictionaries.
            table_name (str): DynamoDB table name.
            user (str): The associated Bluesky username.
        """
        posts_table = get_dynamodb_table(dynamodb_resource=self.dynamodb_resource, table_name=table_name)

        with posts_table.batch_writer(overwrite_by_pkeys=['bskyUsername', 'bskyPostHash']) as batch:
            success_writes = 0
            for item in items:
                try:
                    db_item = self.__create_db_item(bsky_username=user, item=item)
                    batch.put_item(Item=db_item)
                    success_writes = success_writes + 1
                except ClientError as e:
                    print(f"Failed to write item {item} for user={user}: {e}")
        print(f'({user}) -> {success_writes}/{len(items)} items were written to the BSKY_POSTS')
