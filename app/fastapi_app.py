from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
from .analyzer import group_posts_by_period, summarize_trends
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Post(BaseModel):
    text: str
    timestamp: str

class PostRequest(BaseModel):
    posts: List[Post]
    period: str = 'W'

@app.post("/analyze_trends/")
async def analyze_trends(data: PostRequest):
    posts = [post.dict() for post in data.posts]
    period_counts = group_posts_by_period(posts, data.period)
    result = summarize_trends(period_counts)
    return result
