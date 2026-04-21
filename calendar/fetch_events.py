import requests
import json
import re
from datetime import datetime

FEED_URL = "https://events.rpi.edu/feeder/main/eventsFeed.do?f=y&sort=dtstart.utc:asc&fexpr=(categories.href!=%22/public/.bedework/categories/Ongoing%22)%20and%20(entity_type=%22event%22%20or%20entity_type=%22todo%22)&skinName=list-json&setappvar=objName(bwObject)&count=10"
OUTPUT_FILE = "events.json"


def extract_bwobject(text):
    """
    Extract the JavaScript object from:
    var bwObject = {...}
    """
    match = re.search(r'var\s+bwObject\s*=\s*(\{.*\})\s*$', text, re.DOTALL)
    if not match:
        raise ValueError("Could not find bwObject in feed response.")
    return match.group(1)


def clean_event(event):
    start = event.get("start", {})
    end = event.get("end", {})
    location = event.get("location", {})

    return {
        "title": event.get("summary", ""),
        "formatted_date": event.get("formattedDate", ""),
        "date": start.get("longdate", ""),
        "start_time": start.get("time", ""),
        "end_time": end.get("time", ""),
        "all_day": str(start.get("allday", "false")).lower() == "true",
        "location": location.get("address", ""),
        "description": event.get("description", ""),
        "event_link": event.get("eventlink", ""),
        "categories": event.get("categories", [])
    }


def main():
    response = requests.get(FEED_URL, timeout=15)
    response.raise_for_status()

    raw_text = response.text
    bwobject_text = extract_bwobject(raw_text)
    bwobject = json.loads(bwobject_text)

    raw_events = bwobject.get("bwEventList", {}).get("events", [])

    cleaned = {
        "title": "Upcoming Events",
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "events": [clean_event(event) for event in raw_events]
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(cleaned['events'])} events to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()