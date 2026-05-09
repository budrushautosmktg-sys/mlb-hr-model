import requests
import pandas as pd
from bs4 import BeautifulSoup

def get_mlb_stats(year=2026):
    batters_url = f"https://statsapi.mlb.com/api/v1/stats?stats=season&season={year}&group=hitting"
    pitchers_url = f"https://statsapi.mlb.com/api/v1/stats?stats=season&season={year}&group=pitching"
    batters = requests.get(batters_url).json()["stats"]
    pitchers = requests.get(pitchers_url).json()["stats"]
    batters_df = pd.DataFrame([{
        "player_id": stat["person"]["id"],
        "name": stat["person"]["fullName"],
        "team": stat["team"]["name"],
        "HR": stat["stats"]["homeRuns"],
        "AB": stat["stats"]["atBats"],
        "ISO": stat["stats"].get("iso", 0),
        "wOBA": stat["stats"].get("woba", 0),
        "pull%": stat["stats"].get("pullPct", 0),
        "hardHit%": stat["stats"].get("hardHitPct", 0),
        "handedness": stat["person"]["batSide"]["code"]
    } for stat in batters if "stats" in stat])
    pitchers_df = pd.DataFrame([{
        "player_id": stat["person"]["id"],
        "name": stat["person"]["fullName"],
        "team": stat["team"]["name"],
        "HR9": stat["stats"]["homeRunsPer9"],
        "FB%": stat["stats"].get("flyBallPct", 0),
        "hardHit%_allowed": stat["stats"].get("hardHitPct", 0),
        "handedness": stat["person"]["pitchHand"]["code"]
    } for stat in pitchers if "stats" in stat])
    return batters_df, pitchers_df

def get_park_factors():
    url = "https://www.baseball-reference.com/leagues/MLB/2026.shtml"
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", {"id": "team_batting"})
        park_factors = []
        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) > 3:
                park_factors.append({
                    "team": cols[1].text,
                    "park": cols[2].text,
                    "HR_factor": float(cols[10].text) if cols[10].text else 1.0
                })
        return pd.DataFrame(park_factors)
    except:
        return pd.DataFrame({
            "team": ["Yankees", "Dodgers", "Red Sox", "Cubs", "Astros"],
            "park": ["Yankee Stadium", "Dodger Stadium", "Fenway Park", "Wrigley Field", "Minute Maid Park"],
            "HR_factor": [1.0, 0.9, 1.1, 1.0, 1.0]
        })

def get_weather(city, api_key):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=imperial"
    try:
        response = requests.get(url).json()
        if "main" in response:
            return {
                "temp": response["main"]["temp"],
                "humidity": response["main"]["humidity"],
                "wind_speed": response["wind"]["speed"],
                "wind_direction": response["wind"]["deg"]
            }
        return None
    except:
        return {"temp": 70, "humidity": 50, "wind_speed": 5, "wind_direction": 0}

def get_simulated_odds(batters_df):
    odds = []
    for _, row in batters_df.iterrows():
        hr_rate = row["HR"] / row["AB"] if row["AB"] > 0 else 0
        implied_prob = hr_rate * 10
        odds.append({
            "player_id": row["player_id"],
            "HR_odds": int(1 / implied_prob) if implied_prob > 0 else 1000
        })
    return pd.DataFrame(odds)

def pull_all_data(api_key):
    batters_df, pitchers_df = get_mlb_stats()
    park_factors_df = get_park_factors()
    odds_df = get_simulated_odds(batters_df)
    cities = ["New York", "Los Angeles", "Chicago", "Houston", "Boston"]
    weather_data = {city: get_weather(city, api_key) for city in cities}
    return batters_df, pitchers_df, park_factors_df, odds_df, weather_data