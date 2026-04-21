import json
from datetime import datetime

INPUT_FILE = "events.json"
OUTPUT_FILE = "calendar.html"
MAX_EVENTS = 5


def load_events():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def format_event_html(event):
    title = event.get("title", "Untitled Event")
    date = event.get("date", "")
    start_time = event.get("start_time", "")
    end_time = event.get("end_time", "")
    location = event.get("location", "No location listed")
    description = event.get("description", "")
    link = event.get("event_link", "")

    time_text = start_time
    if end_time:
        time_text += f" - {end_time}"

    if len(description) > 180:
        description = description[:177] + "..."

    link_html = ""
    if link:
        link_html = f"<p><a href='{link}' target='_blank'>More Info</a></p>"

    return f"""
    <div class="event-card">
        <h2>{title}</h2>
        <p><strong>Date:</strong> {date}</p>
        <p><strong>Time:</strong> {time_text}</p>
        <p><strong>Location:</strong> {location}</p>
        <p>{description}</p>
        {link_html}
    </div>
    """


def build_html(data):
    title = data.get("title", "Upcoming Events")
    updated_at = data.get("updated_at", "")
    events = data.get("events", [])[:MAX_EVENTS]

    events_html = "".join(format_event_html(event) for event in events)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="300">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background: #111;
            color: #fff;
            margin: 0;
            padding: 30px;
        }}

        .container {{
            max-width: 1000px;
            margin: auto;
        }}

        h1 {{
            font-size: 48px;
            margin-bottom: 10px;
            text-align: center;
        }}

        .updated {{
            text-align: center;
            font-size: 16px;
            color: #ccc;
            margin-bottom: 30px;
        }}

        .event-card {{
            background: #1e1e1e;
            border-left: 6px solid #cc0000;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
        }}

        .event-card h2 {{
            margin-top: 0;
            font-size: 28px;
            color: #ffcccc;
        }}

        .event-card p {{
            font-size: 20px;
            margin: 8px 0;
        }}

        a {{
            color: #99ccff;
            text-decoration: none;
        }}

        a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <div class="updated">Last updated: {updated_at}</div>
        {events_html}
    </div>
</body>
</html>
"""
    return html


def main():
    data = load_events()
    html = build_html(data)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Created {OUTPUT_FILE}")


if __name__ == "__main__":
    main()