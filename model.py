import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split

def create_features(batters_df, pitchers_df, park_factors_df, odds_df, weather_data):
    df = pd.merge(batters_df, pitchers_df, how="cross")
    df = pd.merge(df, park_factors_df, left_on="team_x", right_on="team", how="left")
    df = pd.merge(df, odds_df, left_on="player_id_x", right_on="player_id", how="left")
    df["temp"] = df["team_x"].apply(lambda x: weather_data.get(x, {"temp": 70})["temp"])
    df["wind_speed"] = df["team_x"].apply(lambda x: weather_data.get(x, {"wind_speed": 5})["wind_speed"])
    df["handedness_matchup"] = df.apply(
        lambda x: 1 if (x["handedness_x"] == "L" and x["handedness_y"] == "R") or
                       (x["handedness_x"] == "R" and x["handedness_y"] == "L")
        else 0, axis=1
    )
    df["model_hr_prob"] = (df["ISO"] * 10 + df["HR9"] * 0.1 + df["HR_factor"] * 5 + df["wind_speed"] * 0.5) / 100
    df["is_HR"] = (df["model_hr_prob"] > 0.2).astype(int)
    return df

def train_model(df):
    features = ["ISO", "wOBA", "pull%", "hardHit%", "HR9", "FB%", "hardHit%_allowed", "HR_factor", "temp", "wind_speed", "handedness_matchup"]
    X = df[features]
    y = df["is_HR"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = XGBClassifier(objective="binary:logistic", n_estimators=50, max_depth=4, learning_rate=0.1, scale_pos_weight=9)
    model.fit(X_train, y_train)
    return model

def find_value_props(df, min_edge=0.2):
    df["implied_prob"] = 1 / (df["HR_odds"] + 1)
    value_props = df[(df["model_hr_prob"] > 1.2 * df["implied_prob"]) & (df["model_hr_prob"] > 0.1)]
    return value_props[["name_x", "name_y", "model_hr_prob", "HR_odds", "implied_prob"]]