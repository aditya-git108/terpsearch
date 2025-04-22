import os
from celery import Celery
from categorizer import Categorizer
import multiprocessing

multiprocessing.set_start_method("spawn", force=True)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")  # default fallback
celery_app = Celery("worker", broker=REDIS_URL, backend=REDIS_URL)
# categorizer = Categorizer()

@celery_app.task
def categorize_texts_task(texts):
    print('Entering celery worker...')
    print(f'redis_url: {REDIS_URL}')
    from categorizer import Categorizer
    categorizer = Categorizer()
    print('Initialized categorizer within celery worker and now entering batch_categorize()')
    return categorizer.batch_categorize(texts)
