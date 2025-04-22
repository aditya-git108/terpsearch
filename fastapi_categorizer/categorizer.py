from sentence_transformers import SentenceTransformer, util
from typing import List, Dict, Any
import time


class Categorizer:
    CATEGORY_LABELS = [
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
        "sports": [
            "football", "soccer", "basketball", "baseball", "nba", "nfl", "mlb", "nhl",
            "goal", "match", "game", "score", "team", "athlete", "tournament", "playoffs",
            "finals", "draft", "coach", "stadium", "sports"
        ],
        "politics": [
            "election", "vote", "voting", "president", "presidency", "government", "policy", "bill",
            "congress", "senate", "house", "reform", "democrats", "republicans", "GOP", "liberal",
            "conservative", "left-wing", "right-wing", "politics", "political", "campaign"
        ],
        "tech": [
            "tech", "AI", "artificial intelligence", "startup", "startups", "software", "hardware",
            "robotics", "robot", "machine learning", "ML", "gadget", "app", "apps", "dev", "programming",
            "coding", "engineer", "data science", "big data", "cloud", "cybersecurity", "blockchain", "web3"
        ],
        "entertainment": [
            "movie", "film", "cinema", "tv", "show", "series", "netflix", "hulu", "celebrity",
            "celeb", "drama", "comedy", "album", "music", "song", "pop", "rap", "hiphop", "hollywood",
            "streaming", "concert", "trailer", "entertainment"
        ],
        "finance": [
            "finance", "financial", "stock", "stocks", "market", "investment", "investing", "funding",
            "fund", "economy", "economic", "bank", "banking", "interest rate", "inflation", "bitcoin",
            "crypto", "ethereum", "btc", "eth", "portfolio", "wall street", "nasdaq", "s&p"
        ],
        "health": [
            "health", "healthy", "doctor", "nurse", "hospital", "clinic", "mental", "mental health",
            "therapy", "vaccine", "vaccination", "covid", "medicine", "medical", "wellness", "fitness",
            "exercise", "workout", "nutrition", "diet", "healthcare", "depression", "anxiety"
        ],
        "education": [
            "school", "college", "university", "education", "student", "studying", "study", "exam",
            "professor", "lecture", "course", "homework", "assignment", "teacher", "class", "academic"
        ],
        "climate": [
            "climate", "climate change", "global warming", "carbon", "carbon footprint", "sustainability",
            "environment", "environmental", "pollution", "emissions", "green energy", "eco", "renewable",
            "recycling", "solar", "wind power", "wildfire", "drought", "ice caps"
        ],
        "travel": [
            "travel", "flight", "fly", "vacation", "trip", "journey", "airbnb", "hotel", "resort",
            "destination", "tour", "tourism", "passport", "airport", "luggage", "cruise", "beach",
            "backpacking", "road trip", "explore"
        ],
        "memes": [
            "meme", "memes", "funny", "lol", "lmao", "rofl", "😂", "🤣", "joke", "shitpost", "dank",
            "relatable", "humor", "satire", "irony", "banter", "troll", "cringe", "memeing", "pov"
        ],
        "fashion": [
            "fashion", "clothes", "outfit", "ootd", "style", "trendy", "model", "runway", "wardrobe",
            "designer", "aesthetic", "lookbook", "shopping", "haute couture", "accessories", "fit check",
            "vogue", "chic", "streetwear"
        ]
    }

    def __init__(self, threshold: float = 0.22):
        print("Loading model...")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        print("Model loaded!")
        self.category_labels = Categorizer.CATEGORY_LABELS
        self.clean_labels = [label.split(",")[0].strip() for label in self.category_labels]
        self.keywords = Categorizer.KEYWORDS
        self.threshold = threshold
        self.category_embeddings = self.model.encode(
            Categorizer.CATEGORY_LABELS, convert_to_tensor=True, normalize_embeddings=True
        )
        print("Category embeddings loaded:", self.category_embeddings.shape)

    def categorize(self, post: str) -> List[str]:
        print('Entering categorize()...')
        text_lower = post.lower()
        embedding = self.model.encode(post, convert_to_tensor=True, normalize_embeddings=True)
        cosine_scores = util.cos_sim(embedding, self.category_embeddings)[0]

        matched = [
            self.clean_labels[i]
            for i, score in enumerate(cosine_scores)
            if score > self.threshold
        ]

        if not matched:
            matched = self._keyword_fallback(text_lower)

        return matched or ["uncategorized"]

    def batch_categorize(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        start_time = time.time()
        print('Entering batch_categorize...')
        texts = [post['text'] for post in posts]
        texts = [t.strip() for t in texts if t.strip()]
        if not texts:
            print("🚨 No valid texts to categorize.")
            return [{'category': 'unclassified'}]
        embeddings = self.model.encode(texts, convert_to_tensor=True, normalize_embeddings=True)
        cosine_scores = util.cos_sim(embeddings, self.category_embeddings)

        print('Finished creating embeddings')

        results = []
        for i, row in enumerate(cosine_scores):
            matched = [
                self.clean_labels[j] for j, score in enumerate(row) if score > self.threshold
            ]
            if not matched:
                matched = self._keyword_fallback(texts[i].lower())
            posts[i]['category'] = matched or ['uncategorized']
            # results.append(posts)
            # results.append(matched or ["uncategorized"])
        end_time = time.time()
        duration = end_time - start_time

        print(f'batch_categorize() took {duration:.4f} seconds')
        return posts

    def _keyword_fallback(self, text: str) -> List[str]:
        for cat, kwds in self.keywords.items():
            if any(keyword in text for keyword in kwds):
                return [cat]
        return []

    def categorize_with_scores(self, text: str) -> List[Dict[str, float]]:
        embedding = self.model.encode(text, convert_to_tensor=True, normalize_embeddings=True)
        scores = util.cos_sim(embedding, self.category_embeddings)[0]
        return [{self.clean_labels[i]: float(scores[i])} for i in range(len(self.clean_labels))]
