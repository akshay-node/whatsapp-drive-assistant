import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def summarize_text(content):
    res = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": f"Summarize this:\n{content}"}],
        temperature=0.5
    )
    return res.choices[0].message.content.strip()