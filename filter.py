KEYWORDS = [
    "looking for",
    "recommend",
    "any tool",
    "how do you",
    "need help",
    "best way to",
    "opinions",
]

def is_lead(text):
    text = text.lower()
    return any(k in text for k in KEYWORDS)