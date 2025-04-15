from sentence_transformers import SentenceTransformer, util
import torch
import re
from .logger_config import logger  # ✅ Centralized logger setup

# --- Load Sentence Embedding Model ---
model = SentenceTransformer("all-MiniLM-L6-v2")  # Pretrained lightweight transformer for semantic similarity

# --- Define Category Descriptions for Semantic Matching ---
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

# Category names and their corresponding embeddings
CATEGORY_NAMES = list(CATEGORY_LABELS.keys())
CATEGORY_EMBEDDINGS = model.encode(list(CATEGORY_LABELS.values()), convert_to_tensor=True)

# --- Keyword Mapping for Fallback Matching ---
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

# --- Categorization Counters for Logging/Reporting ---
CATEGORIZATION_LOG = {
    "semantic_match": 0,
    "keyword_fallback": 0,
    "uncategorized": 0
}

# --- Chunking Function: Break long text into manageable pieces ---
def chunk_text(text, max_length=300):
    """
    Breaks a long text into shorter chunks based on punctuation.

    Args:
        text (str): The full text to chunk
        max_length (int): Maximum characters per chunk

    Returns:
        List[str]: List of text chunks
    """
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

# --- Main Categorization Function ---
def categorize_post(text, threshold=0.07):
    """
    Categorizes a post based on semantic similarity to category labels,
    with keyword fallback if the semantic score is too low.

    Args:
        text (str): Post text
        threshold (float): Confidence threshold for semantic matching

    Returns:
        Tuple[List[str], float]: Matched category (or categories), and confidence score
    """
    text_lower = text.lower()

    # Step 1: Semantic embedding from chunked text
    chunks = chunk_text(text)
    chunk_embeddings = [model.encode(chunk, convert_to_tensor=True) for chunk in chunks]
    post_embedding = torch.stack(chunk_embeddings).mean(dim=0)

    # Step 2: Compute cosine similarity with all category embeddings
    cosine_scores = util.cos_sim(post_embedding, CATEGORY_EMBEDDINGS)[0]

    # Step 3: Boost score slightly for categories with keyword matches
    for i, cat in enumerate(CATEGORY_NAMES):
        if any(k in text_lower for k in KEYWORDS[cat]):
            cosine_scores[i] += 0.05

    # Step 4: Determine best-matching category
    best_idx = torch.argmax(cosine_scores).item()
    best_score = cosine_scores[best_idx].item()

    # Step 5: Log all category scores for this post
    logger.info(f"📝 POST: {text[:80]}...")
    for i, label in enumerate(CATEGORY_NAMES):
        logger.info(f"  {label:<15}: {cosine_scores[i].item():.3f}")
    logger.info(f"✅ Best match: {CATEGORY_NAMES[best_idx]} (confidence: {best_score:.3f})")
    logger.info("-" * 40)

    # Step 6: Return result based on confidence threshold
    if best_score > threshold:
        CATEGORIZATION_LOG["semantic_match"] += 1
        return [CATEGORY_NAMES[best_idx]], round(best_score, 3)

    # Step 7: Fallback to keyword detection
    for cat, keywords in KEYWORDS.items():
        if any(keyword in text_lower for keyword in keywords):
            CATEGORIZATION_LOG["keyword_fallback"] += 1
            return [cat], 0.0

    # Step 8: If no match found
    CATEGORIZATION_LOG["uncategorized"] += 1
    return ["uncategorized"], 0.0
