import atproto
from atproto import Client
from dateutil.parser import isoparse
from terpsearch.dynamodb.dynamodb_helpers import *
from terpsearch.dynamodb.BskySessionEncryptor import BskySessionEncryptor
from atproto.exceptions import AtProtocolError
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime, timezone

"""
TerpSearch: Class used to manage Bluesky data ingestion and user session tracking required for backend bluesky API
            connectivity.

This class is responsible for:
    - Interacting with the Bluesky API
    - Managing authenticated sessions,
    - Querying and updating user metadata
    - Fetching timeline posts for a specific user.
"""


class TerpSearch:
    SESSION_TOKEN = 'session_token'
    CURSOR_LAST_CHECKED = 'cursor_last_checked'

    def __init__(self, bsky_client: atproto.Client, username: str, password: str, db_mode: str):
        """
        Initializes a TerpSearch instance with DynamoDB integration and Bluesky authentication.

        Args:
            - bsky_client (atproto.Client): An unauthenticated client object to use or initialize.
            - username (str): The Bluesky username.
            - password (str): The Bluesky password (ideally an app password).
        """
        self.db_mode = db_mode
        self.bsky_username = username
        self.bsky_password = password
        self.posts_table = get_dynamodb_table(
            dynamodb_resource=get_dynamodb_resource(db_mode=self.db_mode),
            table_name=DynamoDbConstants.BSKY_POSTS_TABLE_NAME
        )
        self.bsky_users_table = get_dynamodb_table(
            dynamodb_resource=get_dynamodb_resource(db_mode=self.db_mode),
            table_name=DynamoDbConstants.BSKY_USERS_TABLE_NAME
        )
        self.bsky_client = self.__get_bsky_client(bsky_client, username=self.bsky_username, password=self.bsky_password)

    def __get_existing_user_session(self, bsky_username):
        """
        Retrieves the encrypted Bluesky session token for a given user from the users table.

        Args:
            bsky_username (str): The username of the Bluesky account.

        Returns:
            session_token: The encrypted session token associated with the user.

        Raises:
            KeyError: If the session token is not found in the DynamoDB item.
        """
        response = self.bsky_users_table.query(
            KeyConditionExpression=Key('bskyUsername').eq(bsky_username)
        )
        session_token = response['Items'][0][TerpSearch.SESSION_TOKEN]
        return session_token

    def __get_bsky_client(self, client: atproto.Client, username: str, password: str):
        """
        Attempts to restore a Bluesky session using a stored encrypted token.

        If a session does not exist, creates a new session using the provided credentials
        and persists it securely into the BSKY_USERS table.

        Args:
            client (atproto.Client): An instance of the Bluesky client.
            username (str): Bluesky username.
            password (str): Bluesky password (or app password).

        Returns:
            atproto.Client: An authenticated Bluesky client.
        """
        try:
            encryptor = BskySessionEncryptor()
            session_token = self.__get_existing_user_session(bsky_username=username)
            client._import_session_string(encryptor.decrypt(session_token))
            print(f'{username} has an active bluesky session')
            return client
        except AtProtocolError as e:
            print('Removing expired session token...')
            self.bsky_users_table.update_item(
                Key={
                    'bskyUsername': username  # your partition key
                },
                UpdateExpression="REMOVE session_token"
            )
            client = create_session(client=client, bsky_username=username,
                                    bsky_password=password, table=self.bsky_users_table)
            return client
        except:
            print(f'An active session does not currently exist for {username}')
            client = create_session(client=client, bsky_username=username,
                                    bsky_password=password, table=self.bsky_users_table)
            return client

    def __check_for_existing_cursor(self, bsky_username):
        """
        Checks if a cursor (`cursor_last_checked`) exists for the user in the BSKY_USERS table.

        Args:
            bsky_username (str): The Bluesky username.

        Returns:
            bool: True if a cursor exists, False otherwise.
        """
        response = self.bsky_users_table.query(
            KeyConditionExpression=Key('bskyUsername').eq(bsky_username)
        )
        return True if TerpSearch.CURSOR_LAST_CHECKED in response['Items'][0] else False

    def __get_user_cursor(self, bsky_username):
        """
        Retrieves the last stored timeline cursor for a user from DynamoDB.
        Returns None if no cursor exists (i.e., it's the user's first fetch).

        Args:
            bsky_username (str): The Bluesky username.

        Returns:
            str: The last checked cursor, or '' if not available.
        """
        stored_user_cursor_last_checked = self.__check_for_existing_cursor(bsky_username=bsky_username)

        if stored_user_cursor_last_checked:
            response = self.bsky_users_table.query(
                KeyConditionExpression=Key('bskyUsername').eq(bsky_username)
            )
            return response['Items'][0][TerpSearch.CURSOR_LAST_CHECKED]
        else:
            return ''

    def get_timeline_posts(self, bsky_username: str, max_posts=5000):
        all_posts = []
        cursor = None
        cursor_last_checked = self.__get_user_cursor(bsky_username=bsky_username)  # stored timestamp
        posts_fetched = 0
        first_post_time = None
        last_post_time = None

        # Flag to control loop
        timeline_exists = True

        while timeline_exists:
            # print(f'Cursor: {cursor}')
            # print(f'Last checked: {cursor_last_checked}')

            try:
                timeline = None
                try:
                    timeline = self.bsky_client.get_timeline(
                        algorithm='reverse-chronological',
                        cursor=cursor
                    )
                except Exception as e:
                    if 'ExpiredToken' in str(e) or 'InvalidToken' in str(e):
                        print("⚠️ Token expired. Re-authenticating...")
                        new_bsky_client = Client()
                        update_expired_client(bsky_client=new_bsky_client, table=self.bsky_users_table,
                                              bsky_username=self.bsky_username, bsky_password=self.bsky_password)
                        print('>>> Updated expired session token')
                        self.bsky_client = new_bsky_client
                    timeline = self.bsky_client.get_timeline(
                        algorithm='reverse-chronological',
                        cursor=cursor
                    )

                if not timeline.feed:
                    break

                for feed_view in timeline.feed:
                    post = feed_view.post.record
                    author = feed_view.post.author
                    action = "New Post"

                    if feed_view.reason:
                        action_by = feed_view.reason.by.handle
                        action = f"Reposted by @{action_by}"

                    post_time = post.created_at if hasattr(post, 'created_at') else None
                    if post_time is None:
                        continue

                    # Stop fetching when we've hit already-seen posts
                    if cursor_last_checked and isoparse(post_time) <= isoparse(cursor_last_checked):
                        timeline_exists = False
                        break

                    # Track range of post times
                    if first_post_time is None:
                        first_post_time = post_time
                    last_post_time = post_time

                    all_posts.append({
                        "author": author.display_name,
                        "handle": author.handle,
                        "text": post.text,
                        "action": action,
                        "timestamp": post_time
                    })
                    posts_fetched += 1

                # Set the next cursor
                cursor = getattr(timeline, "cursor", None)
                if not cursor:
                    break

            except Exception as e:
                print(f"Error fetching posts: {e}")
                break

        # Use timestamp of the newest post as new cursor_last_checked
        if all_posts:
            cursor_last_checked = all_posts[0]['timestamp']

        print(f"✅ Fetched {posts_fetched} posts from {first_post_time} to {last_post_time}")
        print(f'Updated cursor_last_checked: {cursor_last_checked}')

        # Store cursor in users table
        response = {'posts': all_posts, TerpSearch.CURSOR_LAST_CHECKED: cursor_last_checked}
        self.bsky_users_table.update_item(
            Key={'bskyUsername': bsky_username},
            UpdateExpression='SET cursor_last_checked = :cursor',
            ExpressionAttributeValues={
                ':cursor': cursor_last_checked
            }
        )
        return response

    def get_discover_feed_posts(self):
        feed_view = self.bsky_client.app.bsky.feed.get_feed(
            {'feed': 'at://did:plc:z72i7hdynmk6r22z27h6tvur/app.bsky.feed.generator/whats-hot', 'limit': 100},
            headers={'Accept-Language': 'en'})

        for feed in feed_view.feed:
            print(type(feed.post.record))
            print('\n')

        return

    def get_topic_posts(self):
        return
