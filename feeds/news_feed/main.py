from typing import Dict, List
from fastapi import FastAPI
import datetime
import feedparser

app = FastAPI()

# Example local RSS feed (Albany Times Union)
RSS_URL = "https://www.news10.com/feed/"

def get_news_headlines() -> List[str]:
    feed = feedparser.parse(RSS_URL)

    headlines = []

    for entry in feed.entries[:10]:
        title = entry.get("title", "").strip()
        if title:
            headlines.append(title[:90] + "..." if len(title) > 90 else title)

    if not headlines:
        return ["No news available"]

    return headlines


@app.get("/news.json")
def news_feed() -> List[Dict[str, str]] | Dict[str, str]:
    now = datetime.datetime.now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    try:
        headlines = get_news_headlines()
    except Exception as e:
        return {"Error": "Failed to fetch news", "info": str(e)}

    # Format for ticker (IMPORTANT)
    text = "Capital Region News: " + "  |  ".join(headlines)

    return [{
        "name": "Local News",
        "type": "RichText",
        "render_as": "html",
        "start_time": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end_time": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "text": text
    }]