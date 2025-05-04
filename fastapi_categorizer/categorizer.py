from sentence_transformers import SentenceTransformer, util
from typing import List, Dict, Any
import time
import boto3
from datetime import datetime

# Setup CloudWatch client
cloudwatch = boto3.client("cloudwatch", region_name="us-east-1")

def log_metrics_to_cloudwatch(mean_conf, std_conf, uncategorized_rate, fallback_rate=None):
    metrics = [
        {'MetricName': 'ConfidenceScoreMean', 'Value': mean_conf, 'Unit': 'None'},
        {'MetricName': 'ConfidenceScoreStd', 'Value': std_conf, 'Unit': 'None'},
        {'MetricName': 'UncategorizedRate', 'Value': uncategorized_rate, 'Unit': 'Percent'}
    ]
    if fallback_rate is not None:
        metrics.append({'MetricName': 'FallbackRate', 'Value': fallback_rate, 'Unit': 'Percent'})

    cloudwatch.put_metric_data(Namespace='TerpsearchMonitors', MetricData=metrics)

def create_cloudwatch_dashboard():
    dashboard_body = {
        "widgets": [
            {"type": "metric", "x": 0, "y": 0, "width": 12, "height": 6, "properties": {
                "metrics": [["TerpsearchMonitors", "ConfidenceScoreMean"]],
                "period": 300, "stat": "Average", "region": "us-east-1",
                "title": "Mean Confidence Score"}},
            {"type": "metric", "x": 0, "y": 6, "width":  12, "height": 6, "properties": {
                "metrics": [["TerpsearchMonitors", "ConfidenceScoreStd"]],
                "period": 300, "stat": "Average", "region": "us-east-1",
                "title": "Confidence Score Std Dev"}},
            {"type": "metric", "x": 12, "y": 0, "width": 12, "height": 6, "properties": {
                "metrics": [["TerpsearchMonitors", "UncategorizedRate"]],
                "period": 300, "stat": "Average", "region": "us-east-1",
                "title": "Uncategorized Rate (%)"}},
            {"type": "metric", "x": 12, "y": 6, "width": 12, "height": 6, "properties": {
                "metrics": [["TerpsearchMonitors", "FallbackRate"]],
                "period": 300, "stat": "Average", "region": "us-east-1",
                "title": "Fallback Rate (%)"}}
        ]
    }
    cloudwatch.put_dashboard(DashboardName="Confidence Score Metrics", DashboardBody=str(dashboard_body).replace("'", '"'))

class Categorizer:
    CATEGORY_KEYS = [
        "sports", "politics", "tech", "entertainment", "finance",
        "health", "education", "climate", "travel", "memes", "fashion"
    ]

    CATEGORY_DESCRIPTIONS = [
        "sports and athletics, football, basketball, soccer",
        "politics and government, elections, public policy",
        "technology, AI, software, startups",
        "entertainment, movies, music, celebrities",
        "finance, investing, stock market, crypto",
        "health, medicine, hospitals, wellness",
        "education, learning, universities, schools",
        "climate change, environment, global warming",
        "travel, tourism, destinations, vacations",
        "memes, internet culture, funny content",
        "fashion, clothing, trends, style"
    ]

    KEYWORDS = {
        "sports": ["game", "team", "match", "goal", "tournament", "score", "player", "league"],
        "politics": ["government", "election", "policy", "congress", "bill", "minister", "vote", "democracy"],
        "tech": ["ai", "software", "device", "machine learning", "app", "coding", "startup", "technology"],
        "entertainment": ["movie", "tv", "show", "music", "actor", "celebrity", "netflix", "hollywood"],
        "finance": ["stock", "crypto", "market", "investment", "economy", "bitcoin", "nasdaq", "interest"],
        "health": ["hospital", "doctor", "covid", "virus", "mental", "fitness", "disease", "wellness"],
        "education": ["school", "university", "degree", "exam", "teacher", "student", "academic", "learning"],
        "climate": ["global warming", "environment", "pollution", "emissions", "carbon", "climate", "sustainability"],
        "travel": ["flight", "vacation", "tourist", "destination", "trip", "journey", "beach", "resort"],
        "memes": ["meme", "funny", "lol", "joke", "troll", "humor", "dank", "relatable"],
        "fashion": ["style", "trend", "outfit", "wear", "design", "model", "clothing", "brand"]
    }

    def __init__(self, threshold: float = 0.18):
        print("Loading model...")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        print("Model loaded!")
        self.clean_labels = Categorizer.CATEGORY_KEYS
        self.keyword_map = Categorizer.KEYWORDS
        self.threshold = threshold
        self.category_embeddings = self.model.encode(
            Categorizer.CATEGORY_DESCRIPTIONS,
            convert_to_tensor=True,
            normalize_embeddings=True
        )
        print("Category embeddings loaded:", self.category_embeddings.shape)

        try:
            create_cloudwatch_dashboard()
        except Exception as e:
            print("⚠️ Failed to create CloudWatch dashboard:", str(e))

    def categorize(self, post: str) -> List[str]:
        text_lower = post.lower()
        embedding = self.model.encode(post, convert_to_tensor=True, normalize_embeddings=True)
        cosine_scores = util.cos_sim(embedding, self.category_embeddings)[0]
        best_idx = int(cosine_scores.argmax())
        best_score = float(cosine_scores[best_idx])
        best_label = self.clean_labels[best_idx]
        if best_score >= self.threshold:
            return [best_label]
        fallback = self._keyword_fallback(text_lower)
        return fallback or [best_label]

    def batch_categorize(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        start_time = time.time()
        texts = [post['text'].strip() for post in posts if post.get('text')]
        if not texts:
            print("🚨 No valid texts to categorize.")
            return [{'category': 'unclassified'}]
        embeddings = self.model.encode(texts, convert_to_tensor=True, normalize_embeddings=True)
        cosine_scores = util.cos_sim(embeddings, self.category_embeddings)

        confidence_scores = []
        uncategorized_count = 0
        fallback_count = 0

        for i, row in enumerate(cosine_scores):
            best_idx = int(row.argmax())
            best_score = float(row[best_idx])
            best_label = self.clean_labels[best_idx]
            confidence_scores.append(best_score)

            if best_score >= self.threshold:
                posts[i]['category'] = [best_label]
            else:
                fallback = self._keyword_fallback(texts[i].lower())
                if fallback:
                    fallback_count += 1
                else:
                    uncategorized_count += 1
                posts[i]['category'] = fallback or [best_label]

        duration = time.time() - start_time
        print(f'batch_categorize() took {duration:.4f} seconds')

        mean_conf = sum(confidence_scores) / len(confidence_scores)
        std_conf = (sum((x - mean_conf) ** 2 for x in confidence_scores) / len(confidence_scores)) ** 0.5
        uncategorized_rate = 100.0 * uncategorized_count / len(posts)
        fallback_rate = 100.0 * fallback_count / len(posts)

        log_metrics_to_cloudwatch(mean_conf, std_conf, uncategorized_rate, fallback_rate)
        return posts

    def _keyword_fallback(self, text: str) -> List[str]:
        for cat, kwds in self.keyword_map.items():
            if any(keyword in text for keyword in kwds):
                return [cat]
        return []

    def categorize_with_scores(self, text: str) -> List[Dict[str, float]]:
        embedding = self.model.encode(text, convert_to_tensor=True, normalize_embeddings=True)
        scores = util.cos_sim(embedding, self.category_embeddings)[0]
        return [{self.clean_labels[i]: float(scores[i])} for i in range(len(self.clean_labels))]



# from sentence_transformers import SentenceTransformer, util
# from typing import List, Dict, Any
# import time

# class Categorizer:
#     CATEGORY_KEYS = [
#         "sports", "politics", "tech", "entertainment", "finance",
#         "health", "education", "climate", "travel", "memes", "fashion"
#     ]

#     CATEGORY_DESCRIPTIONS = [
#         "sports and athletics, football, basketball, soccer",
#         "politics and government, elections, public policy",
#         "technology, AI, software, startups",
#         "entertainment, movies, music, celebrities",
#         "finance, investing, stock market, crypto",
#         "health, medicine, hospitals, wellness",
#         "education, learning, universities, schools",
#         "climate change, environment, global warming",
#         "travel, tourism, destinations, vacations",
#         "memes, internet culture, funny content",
#         "fashion, clothing, trends, style"
#     ]

#     KEYWORDS = {
#         "sports": [
#             "football", "soccer", "basketball", "baseball", "nba", "nfl", "mlb", "nhl",
#             "goal", "match", "game", "score", "team", "athlete", "tournament", "playoffs",
#             "finals", "draft", "coach", "stadium", "sports"
#         ],
#         "politics": [
#             "election", "vote", "voting", "president", "presidency", "government", "policy", "bill",
#             "congress", "senate", "house", "reform", "democrats", "republicans", "GOP", "liberal",
#             "conservative", "left-wing", "right-wing", "politics", "political", "campaign"
#         ],
#         "tech": [
#             "tech", "AI", "artificial intelligence", "startup", "startups", "software", "hardware",
#             "robotics", "robot", "machine learning", "ML", "gadget", "app", "apps", "dev", "programming",
#             "coding", "engineer", "data science", "big data", "cloud", "cybersecurity", "blockchain", "web3"
#         ],
#         "entertainment": [
#             "movie", "film", "cinema", "tv", "show", "series", "netflix", "hulu", "celebrity",
#             "celeb", "drama", "comedy", "album", "music", "song", "pop", "rap", "hiphop", "hollywood",
#             "streaming", "concert", "trailer", "entertainment"
#         ],
#         "finance": [
#             "finance", "financial", "stock", "stocks", "market", "investment", "investing", "funding",
#             "fund", "economy", "economic", "bank", "banking", "interest rate", "inflation", "bitcoin",
#             "crypto", "ethereum", "btc", "eth", "portfolio", "wall street", "nasdaq", "s&p"
#         ],
#         "health": [
#             "health", "healthy", "doctor", "nurse", "hospital", "clinic", "mental", "mental health",
#             "therapy", "vaccine", "vaccination", "covid", "medicine", "medical", "wellness", "fitness",
#             "exercise", "workout", "nutrition", "diet", "healthcare", "depression", "anxiety"
#         ],
#         "education": [
#             "school", "college", "university", "education", "student", "studying", "study", "exam",
#             "professor", "lecture", "course", "homework", "assignment", "teacher", "class", "academic"
#         ],
#         "climate": [
#             "climate", "climate change", "global warming", "carbon", "carbon footprint", "sustainability",
#             "environment", "environmental", "pollution", "emissions", "green energy", "eco", "renewable",
#             "recycling", "solar", "wind power", "wildfire", "drought", "ice caps"
#         ],
#         "travel": [
#             "travel", "flight", "fly", "vacation", "trip", "journey", "airbnb", "hotel", "resort",
#             "destination", "tour", "tourism", "passport", "airport", "luggage", "cruise", "beach",
#             "backpacking", "road trip", "explore"
#         ],
#         "memes": [
#             "meme", "memes", "funny", "lol", "lmao", "rofl", "😂", "🤣", "joke", "shitpost", "dank",
#             "relatable", "humor", "satire", "irony", "banter", "troll", "cringe", "memeing", "pov"
#         ],
#         "fashion": [
#             "fashion", "clothes", "outfit", "ootd", "style", "trendy", "model", "runway", "wardrobe",
#             "designer", "aesthetic", "lookbook", "shopping", "haute couture", "accessories", "fit check",
#             "vogue", "chic", "streetwear"
#         ]
#     }

#     def __init__(self, threshold: float = 0.18):
#         print("Loading model...")
#         self.model = SentenceTransformer("all-MiniLM-L6-v2")
#         print("Model loaded!")
#         self.clean_labels = Categorizer.CATEGORY_KEYS
#         self.keyword_map = Categorizer.KEYWORDS
#         self.threshold = threshold
#         self.category_embeddings = self.model.encode(
#             Categorizer.CATEGORY_DESCRIPTIONS,
#             convert_to_tensor=True,
#             normalize_embeddings=True
#         )
#         print("Category embeddings loaded:", self.category_embeddings.shape)

#     def categorize(self, post: str) -> List[str]:
#         text_lower = post.lower()
#         embedding = self.model.encode(post, convert_to_tensor=True, normalize_embeddings=True)
#         cosine_scores = util.cos_sim(embedding, self.category_embeddings)[0]

#         best_idx = int(cosine_scores.argmax())
#         best_score = float(cosine_scores[best_idx])
#         best_label = self.clean_labels[best_idx]

#         if best_score >= self.threshold:
#             return [best_label]

#         fallback = self._keyword_fallback(text_lower)
#         if fallback:
#             return fallback

#         return [best_label]

#     def batch_categorize(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
#         start_time = time.time()
#         texts = [post['text'].strip() for post in posts if post.get('text')]
#         if not texts:
#             print("🚨 No valid texts to categorize.")
#             return [{'category': 'unclassified'}]

#         embeddings = self.model.encode(texts, convert_to_tensor=True, normalize_embeddings=True)
#         cosine_scores = util.cos_sim(embeddings, self.category_embeddings)

#         for i, row in enumerate(cosine_scores):
#             best_idx = int(row.argmax())
#             best_score = float(row[best_idx])
#             best_label = self.clean_labels[best_idx]

#             if best_score >= self.threshold:
#                 posts[i]['category'] = [best_label]
#             else:
#                 fallback = self._keyword_fallback(texts[i].lower())
#                 posts[i]['category'] = fallback or [best_label]

#         print(f'batch_categorize() took {time.time() - start_time:.4f} seconds')
#         return posts

#     def _keyword_fallback(self, text: str) -> List[str]:
#         for cat, kwds in self.keyword_map.items():
#             if any(keyword in text for keyword in kwds):
#                 return [cat]
#         return []

#     def categorize_with_scores(self, text: str) -> List[Dict[str, float]]:
#         embedding = self.model.encode(text, convert_to_tensor=True, normalize_embeddings=True)
#         scores = util.cos_sim(embedding, self.category_embeddings)[0]
#         return [{self.clean_labels[i]: float(scores[i])} for i in range(len(self.clean_labels))]





