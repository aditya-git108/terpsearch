import os
import pandas as pd

# --- Load and clean real posts from results.csv ---
def get_real_posts():
    """
    Reads real posts from 'results.csv', cleans the data,
    and returns a list of post dictionaries with 'text' and 'timestamp' keys.

    Returns:
        List[dict]: Cleaned post data suitable for JSON processing
    """

    # Get the path to results.csv relative to this script
    base_dir = os.path.dirname(__file__)
    csv_path = os.path.join(base_dir, "results.csv")

    # Load the CSV into a DataFrame
    df = pd.read_csv(csv_path)

    # Keep only the relevant columns
    df = df[["text", "timestamp"]]

    # Drop rows where either column is missing
    df = df.dropna(subset=["text", "timestamp"])

    # Clean up the text column: remove quotes and trim whitespace
    df["text"] = df["text"].astype(str).str.replace('"', "").str.strip()

    # Convert timestamps to valid datetime objects; drop rows with invalid timestamps
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"])

    # Format timestamps as ISO strings without milliseconds or time zone info
    df["timestamp"] = df["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%S")

    # Convert DataFrame to a list of dictionaries for use in the backend
    return df.to_dict(orient="records")


"""
Getting the posts directly from BlueSky API Server  
"""

# def get_real_posts():
#     """
#     Fetches posts from the Bluesky API and returns cleaned records
#     in the same format as the CSV: [{"text": str, "timestamp": ISO str}]
#     """
#     # Placeholder URL — replace with actual Bluesky API endpoint and params
#     API_URL = "https://bsky.social/xrpc/app.bsky.feed.getAuthorFeed"
#     params = {
#         "actor": "your-bluesky-handle.bsky.social",
#         "limit": 20
#     }

#     response = requests.get(API_URL, params=params)
#     response.raise_for_status()
#     data = response.json()

#     # Transform response into the desired format
#     posts = []
#     for item in data.get("feed", []):
#         record = item.get("post", {})
#         text = record.get("text", "").strip()
#         timestamp = record.get("createdAt")

#         if text and timestamp:
#             posts.append({
#                 "text": text,
#                 "timestamp": datetime.fromisoformat(timestamp.rstrip("Z")).strftime("%Y-%m-%dT%H:%M:%S")
#             })

#     return posts
