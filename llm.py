from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_reply(post_text):

    prompt = f"""
You are a helpful Reddit user.

Write a natural, human-like comment replying to this post.

Rules:
- helpful and insightful
- not promotional
- conversational tone
- under 80 words
- ask a follow-up question if possible

Post:
{post_text}
"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return res.choices[0].message.content