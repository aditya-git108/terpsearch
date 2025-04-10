from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from app.categorizer import categorize_post

app = FastAPI()

# Define expected structure of incoming data
class Post(BaseModel):
    text: str
    timestamp: str

class PostRequest(BaseModel):
    posts: List[Post]

@app.post("/analyze_trends/")
def analyze_trends(data: PostRequest):
    enriched_posts = []
    for post in data.posts:
        category, confidence = categorize_post(post.text)
        enriched_posts.append({
            "text": post.text,
            "timestamp": post.timestamp,
            "category": category[0],
            "confidence": confidence
        })

    return enriched_posts
