import json
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer, util

# Load first 100 rows from results.csv
df = pd.read_csv("results.csv", nrows=100)
texts = df["text"].dropna().astype(str).tolist()

# Category setup
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


# Load model
model = SentenceTransformer("all-MiniLM-L6-v2")
desc_embeddings = model.encode(CATEGORY_DESCRIPTIONS, convert_to_tensor=True, normalize_embeddings=True)

thresholds = np.arange(0.10, 0.35, 0.02)
results = []

for threshold in thresholds:
    uncategorized = 0
    confidences = []

    for text in texts:
        emb = model.encode(text, convert_to_tensor=True, normalize_embeddings=True)
        sims = util.cos_sim(emb, desc_embeddings)[0]
        best_score = float(sims.max())
        confidences.append(best_score)
        if best_score < threshold:
            uncategorized += 1

    total = len(texts)
    mean_conf = round(np.mean(confidences), 4)
    uncategorized_rate = round(uncategorized / total, 4)
    results.append({
        "threshold": round(threshold, 2),
        "mean_confidence": mean_conf,
        "uncategorized_rate": uncategorized_rate
    })

# Pick threshold with highest mean confidence while keeping uncategorized rate < 0.2
filtered = [r for r in results if r["uncategorized_rate"] <= 0.2]
best = max(filtered, key=lambda x: x["mean_confidence"]) if filtered else results[0]

# Save config
with open("model_config.json", "w") as f:
    json.dump({"threshold": best["threshold"]}, f, indent=2)

# Save CSV of tuning results
with open("threshold_tuning_confidence.csv", "w") as f:
    f.write("threshold,mean_confidence,uncategorized_rate\n")
    for r in results:
        f.write(f"{r['threshold']},{r['mean_confidence']},{r['uncategorized_rate']}\n")

print(f"✅ Best threshold: {best['threshold']} (mean confidence: {best['mean_confidence']}, uncategorized rate: {best['uncategorized_rate']})")
print("Saved to model_config.json and threshold_tuning_confidence.csv")
