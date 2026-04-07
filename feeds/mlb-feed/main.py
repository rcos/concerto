from typing import Dict, List
from fastapi import FastAPI
import requests
import datetime

app = FastAPI()


MLB_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule"


def format_game_line(game: dict) -> str:
    teams = game.get("teams", {})
    away = teams.get("away", {})
    home = teams.get("home", {})

    away_team = away.get("team", {}).get("name", "Away")
    home_team = home.get("team", {}).get("name", "Home")

    away_score = away.get("score")
    home_score = home.get("score")

    status = game.get("status", {})
    detailed_state = status.get("detailedState", "Scheduled")
    abstract_state = status.get("abstractGameState", "Preview")

    game_datetime = game.get("gameDate")
    display_time = "TBD"

    if game_datetime:
        try:
            dt = datetime.datetime.fromisoformat(game_datetime.replace("Z", "+00:00"))
            display_time = dt.astimezone().strftime("%I:%M %p").lstrip("0")
        except ValueError:
            pass

    if abstract_state == "Final":
        return f"FINAL: {away_team} {away_score}, {home_team} {home_score}"
    elif abstract_state == "Live":
        return f"LIVE: {away_team} {away_score}, {home_team} {home_score} ({detailed_state})"
    else:
        return f"{display_time}: {away_team} at {home_team}"


def get_mlb_games() -> List[str]:
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    response = requests.get(
        MLB_SCHEDULE_URL,
        params={
            "sportId": 1,
            "date": today,
            "hydrate": "linescore,team,flags",
        },
        timeout=20,
    )

    data = response.json()
    dates = data.get("dates", [])
    if not dates:
        return ["No MLB games scheduled today."]

    games = dates[0].get("games", [])
    if not games:
        return ["No MLB games scheduled today."]

    lines = [format_game_line(game) for game in games[:12]]
    return lines


@app.get("/mlb.json")
def read_mlb_scores() -> List[Dict[str, str]] | Dict[str, str]:
    now = datetime.datetime.now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    try:
        game_lines = get_mlb_games()
    except Exception as e:
        return {"Error": "Response Failed", "info": str(e)}

    html = "  |  ".join(game_lines)

    return [{
        "name": "MLB Scores",
        "type": "RichText",
        "render_as": "html",
        "start_time": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end_time": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "text": html
    }]