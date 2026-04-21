import requests
import json
import re
import time
from datetime import datetime, timedelta

FEED_URL = "https://events.rpi.edu/feeder/main/eventsFeed.do?f=y&sort=dtstart.utc:asc&fexpr=(categories.href!=%22/public/.bedework/categories/Ongoing%22)%20and%20(entity_type=%22event%22%20or%20entity_type=%22todo%22)&skinName=list-json&setappvar=objName(bwObject)&count=10"
OUTPUT_HTML = "calendar.html"
REFRESH_SECONDS = 1800  # 30 minutes


def extract_bwobject(text):
    match = re.search(r'var\s+bwObject\s*=\s*(\{.*\})\s*$', text, re.DOTALL)
    if not match:
        raise ValueError("Could not find bwObject in feed response.")
    return match.group(1)


def fetch_events():
    response = requests.get(FEED_URL, timeout=20)
    response.raise_for_status()

    raw_text = response.text
    bwobject_text = extract_bwobject(raw_text)
    bwobject = json.loads(bwobject_text)

    return bwobject.get("bwEventList", {}).get("events", [])


def parse_event_datetime(date_str, time_str):
    if not date_str or not time_str:
        return None

    formats = [
        "%B %d, %Y %I:%M %p",
        "%b %d, %Y %I:%M %p",
    ]

    combined = f"{date_str} {time_str}".strip()
    for fmt in formats:
        try:
            return datetime.strptime(combined, fmt)
        except ValueError:
            continue
    return None


def clean_text(text, max_len=None):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    if max_len and len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text


def normalize_event(event):
    start = event.get("start", {})
    end = event.get("end", {})
    location = event.get("location", {})

    title = clean_text(event.get("summary", "Untitled Event"))
    description = clean_text(event.get("description", ""), 180)
    location_text = clean_text(location.get("address", "Location TBA"))
    event_link = event.get("eventlink", "")

    start_date = start.get("longdate", "")
    start_time = start.get("time", "")
    end_date = end.get("longdate", start_date)
    end_time = end.get("time", "")

    start_dt = parse_event_datetime(start_date, start_time)
    end_dt = parse_event_datetime(end_date, end_time)

    all_day = str(start.get("allday", "false")).lower() == "true"

    return {
        "title": title,
        "description": description,
        "location": location_text,
        "event_link": event_link,
        "start_date": start_date,
        "start_time": start_time,
        "end_date": end_date,
        "end_time": end_time,
        "start_dt": start_dt,
        "end_dt": end_dt,
        "all_day": all_day,
        "formatted_date": clean_text(event.get("formattedDate", "")),
    }


def choose_events(events):
    now = datetime.now()
    normalized = [normalize_event(e) for e in events]

    valid = [e for e in normalized if e["start_dt"] is not None]
    valid.sort(key=lambda e: e["start_dt"])

    current_event = None
    upcoming = []

    for event in valid:
        start_dt = event["start_dt"]
        end_dt = event["end_dt"]

        # If end time is missing, assume 2 hours after start
        if end_dt is None and start_dt is not None:
            end_dt = start_dt + timedelta(hours=2)
            event["end_dt"] = end_dt

        if start_dt <= now <= end_dt:
            current_event = event
        elif start_dt > now:
            upcoming.append(event)

    if current_event:
        return "Happening Now", current_event, upcoming[:2]

    if upcoming:
        return "Coming Up Next", upcoming[0], upcoming[1:3]

    return "No Upcoming Events", None, []


def format_main_event(event, status_label):
    if not event:
        return f"""
        <div class="main-event">
            <div class="status">{status_label}</div>
            <h1>No upcoming events found</h1>
            <p>Please check back later.</p>
        </div>
        """

    time_line = "All Day" if event["all_day"] else f'{event["start_time"]} - {event["end_time"]}'.strip(" -")
    description_html = f"<p class='description'>{event['description']}</p>" if event["description"] else ""

    return f"""
    <div class="main-event">
        <div class="status">{status_label}</div>
        <h1>{event["title"]}</h1>
        <p><strong>Date:</strong> {event["start_date"]}</p>
        <p><strong>Time:</strong> {time_line}</p>
        <p><strong>Location:</strong> {event["location"]}</p>
        {description_html}
    </div>
    """


def format_sidebar_events(events):
    if not events:
        return "<p class='small-note'>No additional upcoming events.</p>"

    html_parts = ["<div class='upcoming-list'><h2>Also Coming Up</h2>"]
    for event in events:
        time_line = "All Day" if event["all_day"] else event["start_time"]
        html_parts.append(f"""
        <div class="mini-event">
            <div class="mini-title">{event["title"]}</div>
            <div>{event["start_date"]}</div>
            <div>{time_line}</div>
            <div>{event["location"]}</div>
        </div>
        """)
    html_parts.append("</div>")
    return "".join(html_parts)


def build_html(status_label, main_event, sidebar_events):
    updated_at = datetime.now().strftime("%m/%d/%Y %I:%M %p")
    main_html = format_main_event(main_event, status_label)
    sidebar_html = format_sidebar_events(sidebar_events)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="{REFRESH_SECONDS}">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RPI Events Display</title>
    <style>
        body {{
            margin: 0;
            font-family: Arial, sans-serif;
            background: transparent;
            color: white;
        }}

        .page {{
            width: 100%;
            height: 100vh;
            box-sizing: border-box;
            padding: 30px 40px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            background: transparent;
        }}

        .top {{
            display: flex;
            gap: 30px;
            align-items: stretch;
            min-height: 80vh;
        }}

        .left-panel {{
            flex: 0 0 58%;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #cc0000;
            border-radius: 10px;
            padding: 20px;
            box-sizing: border-box;
        }}

        .left-panel .placeholder {{
            text-align: center;
        }}

        .left-panel .placeholder h1 {{
            font-size: 88px;
            margin: 0 0 20px 0;
            font-weight: normal;
        }}

        .left-panel .placeholder p {{
            font-size: 34px;
            margin: 10px 0;
            font-weight: bold;
        }}

        .right-panel {{
            flex: 0 0 38%;
            padding: 20px 10px;
            box-sizing: border-box;
        }}

        .status {{
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 18px;
            color: #ffffff;
            letter-spacing: 1px;
            text-transform: uppercase;
        }}

        .main-event h1 {{
            font-size: 54px;
            line-height: 1.1;
            margin: 0 0 20px 0;
        }}

        .main-event p {{
            font-size: 30px;
            line-height: 1.3;
            margin: 10px 0;
        }}

        .description {{
            margin-top: 22px;
            font-size: 26px;
        }}

        .upcoming-list {{
            margin-top: 35px;
        }}

        .upcoming-list h2 {{
            font-size: 28px;
            margin-bottom: 12px;
        }}

        .mini-event {{
            margin-bottom: 18px;
            padding-bottom: 12px;
            border-bottom: 1px solid rgba(255,255,255,0.25);
        }}

        .mini-title {{
            font-size: 22px;
            font-weight: bold;
            margin-bottom: 4px;
        }}

        .mini-event div {{
            font-size: 18px;
            line-height: 1.25;
        }}

        .footer {{
            font-size: 18px;
            opacity: 0.9;
            text-align: right;
        }}

        .small-note {{
            font-size: 18px;
            opacity: 0.9;
        }}
    </style>
</head>
<body>
    <div class="page">
        <div class="top">
            <div class="left-panel">
                <div class="placeholder">
                    <h1>RPI Events</h1>
                    <p>Current and upcoming campus events</p>
                </div>
            </div>

            <div class="right-panel">
                {main_html}
                {sidebar_html}
            </div>
        </div>

        <div class="footer">
            Last updated: {updated_at}
        </div>
    </div>
</body>
</html>
"""
    return html


def write_html(html):
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)


def update_display():
    events = fetch_events()
    status_label, main_event, sidebar_events = choose_events(events)
    html = build_html(status_label, main_event, sidebar_events)
    write_html(html)
    print(f"Updated {OUTPUT_HTML} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    while True:
        try:
            update_display()
        except Exception as e:
            print("Error updating display:", e)

        time.sleep(REFRESH_SECONDS)


if __name__ == "__main__":
    main()