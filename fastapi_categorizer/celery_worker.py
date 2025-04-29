import os
from celery import Celery
import multiprocessing

multiprocessing.set_start_method("spawn", force=True)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")  # default fallback
celery_app = Celery("worker", broker=REDIS_URL, backend=REDIS_URL)
# categorizer = Categorizer()

@celery_app.task
def categorize_texts_task(texts, bsky_username):
    print('Entering celery worker...')
    print(f'redis_url: {REDIS_URL}')
    from fastapi_categorizer.categorizer import Categorizer
    from terpsearch.dynamodb.TerpSearchDb import TerpSearchDb
    from terpsearch.constants.DynamoDbConstants import DynamoDbConstants

    categorizer = Categorizer()
    print('Initialized categorizer within celery worker and now entering batch_categorize()')
    classified_posts = categorizer.batch_categorize(texts)
    print(f'Finished classification: {classified_posts[0:2]}', flush=True)

    # Write results to DynamoDB
    if len(classified_posts) > 0:
        print(f'📝 Writing {len(classified_posts)} classified posts to DynamoDB for {bsky_username}')
        bsky_dynamodb = TerpSearchDb(db_mode=DynamoDbConstants.DB_MODE)
        try:
            bsky_dynamodb.batch_write_items(items=classified_posts,
                                            table_name=DynamoDbConstants.BSKY_POSTS_TABLE_NAME,
                                            user=bsky_username)
            print("✅ Successfully wrote to DynamoDB!")
        except Exception as e:
            print(f"❌ Failed to write to DynamoDB: {str(e)}")
