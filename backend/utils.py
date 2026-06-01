from difflib import SequenceMatcher
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# Simple similarity (string-based)
def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()


# Cosine similarity (better)
def cosine_sim(text1, text2):
    vec = TfidfVectorizer().fit_transform([text1, text2])
    return cosine_similarity(vec)[0][1]


# Final authenticity score
def authenticity_score(sim_score, complexity_score):
    return (0.6 * (1 - sim_score)) + (0.4 * complexity_score)


# Fraud detection
def fraud_check(score, sim_score):
    if sim_score > 0.9:
        return True
    if score < 0.3:
        return True
    return False

# Measure code complexity (very simple heuristic)
def complexity_score(code):
    length = len(code)
    keywords = ["for", "while", "if", "def", "return"]

    keyword_count = sum(code.count(k) for k in keywords)

    return min(1.0, (length / 100) + (keyword_count / 10))


# Measure diversity (unique tokens)
def diversity_score(code):
    tokens = code.split()
    unique_tokens = len(set(tokens))

    if len(tokens) == 0:
        return 0

    return unique_tokens / len(tokens)    