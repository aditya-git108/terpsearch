from sentence_transformers import SentenceTransformer, util
import torch
import re

# Load model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Category definitions
CATEGORY_LABELS = {
    "sports": "Sports and athletic events including football, basketball, soccer",
    "politics": "Politics, elections, public policy, government decisions",
    "tech": "Technology, artificial intelligence, startups, software, gadgets",
    "entertainment": "Movies, music, celebrities, pop culture, drama",
    "finance": "Stock market, cryptocurrency, investing, business, economy",
    "health": "Medicine, hospitals, mental health, wellness, medical care",
    "education": "Schools, universities, students, learning, academic life",
    "climate": "Climate change, environment, emissions, global warming",
    "travel": "Vacations, destinations, tourism, cities, flights, trips",
    "memes": "Internet culture, jokes, funny posts, reactions, humor",
    "fashion": "Clothing, outfits, style, fashion trends, appearance"
}

CATEGORY_NAMES = list(CATEGORY_LABELS.keys())
CATEGORY_EMBEDDINGS = model.encode(list(CATEGORY_LABELS.values()), convert_to_tensor=True)

KEYWORDS = {
    "sports": ["football", "nba", "goal", "match", "score", "soccer", "basketball"],
    "politics": ["election", "president", "government", "policy", "senate", "reform"],
    "tech": ["ai", "technology", "startup", "software", "gadget", "robot"],
    "entertainment": ["movie", "music", "celebrity", "tv", "drama", "album"],
    "finance": ["stock", "market", "crypto", "bitcoin", "investing", "funding"],
    "health": ["doctor", "medicine", "hospital", "vaccine", "health", "mental"],
    "education": ["school", "college", "university", "education", "student"],
    "climate": ["climate", "global warming", "carbon", "environment", "emissions"],
    "travel": ["travel", "flight", "vacation", "tourism", "destination"],
    "memes": ["meme", "funny", "lol", "😂", "🤣", "joke"],
    "fashion": ["fashion", "clothes", "style", "outfit", "trendy"]
}

# Logging
CATEGORIZATION_LOG = {
    "semantic_match": 0,
    "keyword_fallback": 0,
    "uncategorized": 0
}

def chunk_text(text, max_length=300):
    sentences = re.split(r'[.!?\n]', text)
    chunks, current = [], ""
    for sentence in sentences:
        if len(current) + len(sentence) < max_length:
            current += " " + sentence.strip()
        else:
            chunks.append(current.strip())
            current = sentence.strip()
    if current:
        chunks.append(current.strip())
    return [c for c in chunks if c]

def categorize_post(text, threshold=0.07):
    text_lower = text.lower()

    chunks = chunk_text(text)
    chunk_embeddings = [model.encode(chunk, convert_to_tensor=True) for chunk in chunks]
    post_embedding = torch.stack(chunk_embeddings).mean(dim=0)
    cosine_scores = util.cos_sim(post_embedding, CATEGORY_EMBEDDINGS)[0]

    for i, cat in enumerate(CATEGORY_NAMES):
        if any(k in text_lower for k in KEYWORDS[cat]):
            cosine_scores[i] += 0.05

    best_idx = torch.argmax(cosine_scores).item()
    best_score = cosine_scores[best_idx].item()

    print(f"\n📝 POST: {text[:80]}...")
    for i, label in enumerate(CATEGORY_NAMES):
        print(f"  {label:<15}: {cosine_scores[i].item():.3f}")
    print(f"✅ Best match: {CATEGORY_NAMES[best_idx]} (confidence: {best_score:.3f})")
    print("-" * 40)

    if best_score > threshold:
        CATEGORIZATION_LOG["semantic_match"] += 1
        return [CATEGORY_NAMES[best_idx]], round(best_score, 3)

    for cat, keywords in KEYWORDS.items():
        if any(keyword in text_lower for keyword in keywords):
            CATEGORIZATION_LOG["keyword_fallback"] += 1
            return [cat], 0.0

    CATEGORIZATION_LOG["uncategorized"] += 1
    return ["uncategorized"], 0.0
