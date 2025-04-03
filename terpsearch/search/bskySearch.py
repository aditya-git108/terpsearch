import atproto
from atproto import Client
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

    def __init__(self, bsky_client: atproto.Client, username: str, password: str):
        """
        Initializes a TerpSearch instance with DynamoDB integration and Bluesky authentication.

        Args:
            - bsky_client (atproto.Client): An unauthenticated client object to use or initialize.
            - username (str): The Bluesky username.
            - password (str): The Bluesky password (ideally an app password).
        """
        self.bsky_username = username
        self.bsky_password = password
        self.posts_table = get_dynamodb_table(
            dynamodb_resource=get_dynamodb_resource(mode=DynamoDbConstants.FLASK_MODE),
            table_name=DynamoDbConstants.BSKY_POSTS_TABLE_NAME)
        self.bsky_users_table = get_dynamodb_table(
            dynamodb_resource=get_dynamodb_resource(mode=DynamoDbConstants.FLASK_MODE),
            table_name=DynamoDbConstants.BSKY_USERS_TABLE_NAME)
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

    def __get_bsky_client(self, client: atproto.Client, username:str, password:str):
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
            str or None: The last checked cursor, or None if not available.
        """
        stored_user_cursor_last_checked = self.__check_for_existing_cursor(bsky_username=bsky_username)

        if stored_user_cursor_last_checked:
            response = self.bsky_users_table.query(
                KeyConditionExpression=Key('bskyUsername').eq(bsky_username)
            )
            return response['Items'][0][TerpSearch.CURSOR_LAST_CHECKED]
        else:
            return None

    def get_timeline_posts(self, bsky_username:str, max_posts=5000):
        """
        Fetches as many posts as possible from a user's Bluesky timeline using pagination.

        The method starts from the last saved cursor (if any), walks through the timeline
        using the reverse-chronological algorithm, and stores details like text, author, action,
        and timestamps. It updates the cursor in the BSKY_USERS table at the end of the fetch.

        Args:
            bsky_username (str): The username for whom to fetch posts.
            max_posts (int): The maximum number of posts to fetch. (Currently unused in the loop.)

        Returns:
            dict: A response object containing:
                - 'posts': a list of structured post data dictionaries.
                - 'cursor_last_checked': the timestamp used as the new cursor.

        Example:
            terp = TerpSearch(client, username="user", password="pass")
            terp.get_timeline_posts("user.bsky.social")
        """
        all_posts = []
        cursor = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        cursor_last_checked = self.__get_user_cursor(bsky_username=bsky_username)
        posts_fetched = 0
        first_post_time = None
        last_post_time = None
        timeline_exists = True

        cursor_num = 0
        while cursor > cursor_last_checked:
            try:
                if cursor_num == 0:
                    timeline = self.bsky_client.get_timeline(algorithm='reverse-chronological', cursor=None)
                else:
                    timeline = self.bsky_client.get_timeline(algorithm='reverse-chronological', cursor=cursor)

                if not timeline.feed:
                    break

                for feed_view in timeline.feed:
                    post = feed_view.post.record
                    author = feed_view.post.author
                    action = "New Post"

                    if feed_view.reason:
                        action_by = feed_view.reason.by.handle
                        action = f"Reposted by @{action_by}"

                    # Store post timestamps
                    post_time = post.created_at if hasattr(post, 'created_at') else "Unknown"
                    if first_post_time is None:
                        first_post_time = post_time  # First (newest) post
                    last_post_time = post_time  # Last (oldest) post

                    all_posts.append({
                        "author": author.display_name,
                        "handle": author.handle,
                        "text": post.text,
                        "action": action,
                        "timestamp": post_time
                    })
                    posts_fetched += 1

                if cursor_num == 1:
                    cursor_last_checked = cursor

                cursor = getattr(timeline, "cursor", None)
                if not cursor:
                    timeline_exists = False
                    break

                cursor_num = cursor_num + 1

            except Exception as e:
                print(f"Error fetching posts: {e}")
                break

        print(f"✅ Fetched {posts_fetched} posts from {first_post_time} to {last_post_time}")
        print(f'cursor_last_checked: {cursor_last_checked}')

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
