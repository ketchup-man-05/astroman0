"""Topic -> KP house mapping. Extracted from ai_narrator.py so the site has no
streamlit/openai dependency for topic detection. Logic is identical."""
import re

_PREFIX_EXCEPTIONS = {"pass": "port"}

def _has_any(text, words):
    for w in words:
        if w in _PREFIX_EXCEPTIONS:
            pattern = rf"\b{w}(?!{_PREFIX_EXCEPTIONS[w]})\w*\b"
        elif len(w) <= 3:
            pattern = rf"\b{w}s?\b"
        else:
            pattern = rf"\b{w}"
        if re.search(pattern, text):
            return True
    return False

def _count_hits(text, words):
    return sum(1 for w in words if _has_any(text, [w]))

# (name, keywords, positive houses, negative houses, KEY HOUSE)
TOPICS = [
    ("career",   ["job", "career", "promotion", "work", "interview", "salary", "business",
                  "employ", "hire", "hiring", "startup"],
                 [2, 6, 10, 11], [1, 5, 9, 12], 10),
    ("marriage", ["marry", "marri", "wife", "husband", "wedding", "spouse", "love", "relationship",
                  "partner", "boyfriend", "girlfriend", "fiance", "engagement", "engaged"],
                 [2, 7, 11], [1, 6, 10], 7),
    ("travel",   ["travel", "visa", "abroad", "foreign", "relocate", "pr", "passport",
                  "immigra", "emigra", "migrat", "overseas", "canada", "usa", "uk", "england",
                  "australia", "germany", "dubai", "america", "europe"],
                 [3, 9, 12], [2, 4, 11], 12),
    ("health",   ["health", "recover", "sick", "surgery", "disease", "illness", "cure",
                  "medic", "doctor", "hospital", "treatment", "heal"],
                 [1, 5, 11], [6, 8, 12], 6),
    ("property", ["property", "house", "buy", "land", "flat", "vehicle", "car",
                  "apartment", "plot", "bike", "scooter"],
                 [4, 11, 12], [3, 10], 4),
    ("exam",     ["exam", "education", "study", "studi", "pass", "result", "test", "admission",
                  "marks", "rank", "college", "university", "scholarship", "degree"],
                 [4, 9, 11], [3, 8], 4),
    ("children", ["child", "pregnan", "baby", "babies", "conceiv"],
                 [2, 5, 11], [1, 4, 10], 5),
    ("court",    ["court", "lawsuit", "litigation", "legal", "dispute", "lawyer", "judge",
                  "court case", "legal case", "criminal case", "civil case"],
                 [6, 11], [12], 6),
]
DEFAULT_HOUSES = ([2, 11], [8, 12])
DEFAULT_KEY_HOUSE = 11

TOPIC_OPTIONS = {
    "Auto-detect from my question": None,
    "Career / Job / Business": "career",
    "Marriage / Relationship": "marriage",
    "Travel / Visa / Abroad": "travel",
    "Health / Recovery": "health",
    "Property / Vehicle": "property",
    "Exam / Education": "exam",
    "Children / Pregnancy": "children",
    "Court case / Legal": "court",
    "Money / Anything else": "general",
}

TOPIC_LABEL = {v: k for k, v in TOPIC_OPTIONS.items() if v}


def get_query_houses(user_question, topic=None):
    """Maps a question (or an explicitly chosen topic) to KP positive & negative houses."""
    if topic == "general":
        return {"positive_houses": list(DEFAULT_HOUSES[0]),
                "negative_houses": list(DEFAULT_HOUSES[1]),
                "key_house": DEFAULT_KEY_HOUSE, "topic": "general"}
    if topic:
        for key, _, pos, neg, kh in TOPICS:
            if key == topic:
                return {"positive_houses": list(pos), "negative_houses": list(neg),
                        "key_house": kh, "topic": key}
    text = user_question.lower()
    best = None
    for order, (_, keywords, pos, neg, kh) in enumerate(TOPICS):
        hits = _count_hits(text, keywords)
        if hits and (best is None or hits > best[0]):
            best = (hits, order, pos, neg, kh)
    if best is not None:
        _, _, pos, neg, kh = best
        topic_name = TOPICS[best[1]][0]
        return {"positive_houses": list(pos), "negative_houses": list(neg),
                "key_house": kh, "topic": topic_name}
    return {"positive_houses": list(DEFAULT_HOUSES[0]),
            "negative_houses": list(DEFAULT_HOUSES[1]),
            "key_house": DEFAULT_KEY_HOUSE, "topic": "general"}
