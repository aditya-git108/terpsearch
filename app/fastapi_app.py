from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from app.categorizer import categorize_post  # Core NLP categorization function

# --- Initialize FastAPI App ---
app = FastAPI()

# --- Request Schema Definitions ---

class Post(BaseModel):
    """
    Represents an individual post with required fields for analysis.
    """
    text: str
    timestamp: str

class PostRequest(BaseModel):
    """
    Container for a batch of posts in the request body.
    """
    posts: List[Post]

# --- API Endpoint for Trend Categorization ---

@app.post("/analyze_trends/")
def analyze_trends(data: PostRequest):
    """
    Endpoint to process a list of posts and return categorized results.

    Args:
        data (PostRequest): JSON body with a list of posts

    Returns:
        List[dict]: List of posts enriched with category and confidence score
    """
    enriched_posts = []

    # Categorize each post individually
    for post in data.posts:
        category, confidence = categorize_post(post.text)
        enriched_posts.append({
            "text": post.text,
            "timestamp": post.timestamp,
            "category": category[0],   # Currently returns a single best match
            "confidence": confidence
        })

    return enriched_posts
