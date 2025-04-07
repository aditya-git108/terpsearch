from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('all-MiniLM-L6-v2')

# labels 
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

CLEAN_LABELS = [label.split(",")[0] for label in CATEGORY_LABELS]

# Basic keyword dictionary for fallback
KEYWORDS = {
    "sports": ["football", "nba", "goal", "match", "score", "soccer", "basketball"],
    "politics": ["election", "president", "government", "policy", "senate", "reform"],
    "tech": ["AI", "technology", "startup", "software", "gadget", "robot"],
    "entertainment": ["movie", "music", "celebrity", "tv", "drama", "album"],
    "finance": ["stock", "market", "crypto", "bitcoin", "investing", "funding"],
    "health": ["doctor", "medicine", "hospital", "vaccine", "health", "mental"],
    "education": ["school", "college", "university", "education", "student"],
    "climate": ["climate", "global warming", "carbon", "environment", "emissions"],
    "travel": ["travel", "flight", "vacation", "tourism", "destination"],
    "memes": ["meme", "funny", "lol", "😂", "🤣", "joke"],
    "fashion": ["fashion", "clothes", "style", "outfit", "trendy"]
}

CATEGORY_EMBEDDINGS = model.encode(CATEGORY_LABELS, convert_to_tensor=True)

def categorize_post(text, threshold=0.22):
    text_lower = text.lower()
    post_embedding = model.encode(text, convert_to_tensor=True)
    cosine_scores = util.cos_sim(post_embedding, CATEGORY_EMBEDDINGS)[0]

    # semantic similarity 
    matched = [
        CLEAN_LABELS[i]
        for i in range(len(CATEGORY_LABELS))
        if cosine_scores[i] > threshold
    ]

    # Fallback to keyword match if NLP fails
    if not matched:
        for cat, keywords in KEYWORDS.items():
            if any(keyword.lower() in text_lower for keyword in keywords):
                matched.append(cat)
                break

    if not matched:
        matched.append("uncategorized")

    return matched
