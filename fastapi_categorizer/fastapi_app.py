from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, AnyStr
from fastapi_categorizer.celery_worker import categorize_texts_task, celery_app

app = FastAPI()


class TextsRequest(BaseModel):
    bsky_posts: List[Dict]
    bsky_username: AnyStr


@app.post("/categorize/")
def categorize(payload: TextsRequest):
    print(f"🚀 Received {payload.bsky_username} payload of {len(payload.bsky_posts)} items")
    # print("🚀 Type of payload.bsky_posts:", type(payload.bsky_posts))
    # print("🚀 Contents:", payload.bsky_posts)
    posts = [post['text'] for post in payload.bsky_posts]
    texts = [p.strip() for p in posts if p.strip()]
    if not texts:
        return {"task_id": None, "error": "No valid texts provided."}

    task = categorize_texts_task.delay(payload.bsky_posts, payload.bsky_username)
    return {"task_id": task.id}


@app.get("/status/{task_id}")
def get_status(task_id: str):
    task = celery_app.AsyncResult(task_id)
    if task.state == "PENDING":
        return {"status": "pending"}
    elif task.state == "SUCCESS":
        return {"status": "success", "result": task.result}
    elif task.state == "FAILURE":
        return {"status": "failed", "error": str(task.result)}
    else:
        return {"status": task.state}
