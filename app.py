import streamlit as st
import pandas as pd
import plotly.express as px
from data_pipeline import pull_all_data
from model import create_features, train_model, find_value_props

st.title("🚀 MLB Home Run Prop Betting Tool")
st.markdown("This tool predicts HR probabilities and finds undervalued prop bets using free data.")

st.sidebar.header("⚙️ Settings")
openweather_api_key = st.sidebar.text_input("OpenWeatherMap API Key (Free)", type="password")

if st.button("🔄 Pull Latest Data & Run Model"):
    with st.spinner("Pulling data from MLB and Baseball Reference..."):
        batters_df, pitchers_df, park_factors_df, odds_df, weather_data = pull_all_data(openweather_api_key)
        df = create_features(batters_df, pitchers_df, park_factors_df, odds_df, weather_data)
        model = train_model(df)
        value_props = find_value_props(df)
        st.success("✅ Data pulled and model trained!")

        st.header("📊 Top HR Probabilities")
        top_hr = df[["name_x", "name_y", "model_hr_prob", "HR_odds"]].sort_values("model_hr_prob", ascending=False).head(10)
        st.dataframe(top_hr, use_container_width=True)

        st.header("💰 Value Props (Model Edge > 20%)")
        if not value_props.empty:
            st.dataframe(value_props, use_container_width=True)
            fig = px.bar(value_props, x="name_x", y="model_hr_prob", title="Model HR Probability vs. Sportsbook Implied Probability", labels={"name_x": "Batter", "model_hr_prob": "HR Probability"}, color="model_hr_prob", color_continuous_scale="Viridis")
            st.plotly_chart(fig)
            best_prop = value_props.iloc[0]
            st.markdown(f"### 🏆 Best Value Prop Today:\n- **Batter:** {best_prop['name_x']} ({best_prop['model_hr_prob']:.1%} HR chance)\n- **Pitcher:** {best_prop['name_y']}\n- **Odds:** {best_prop['HR_odds']} (Implied: {best_prop['implied_prob']:.1%})\n- **Edge:** {(best_prop['model_hr_prob'] / best_prop['implied_prob'] - 1):.1%}")
        else:
            st.warning("No value props found today. Check back later!")

st.sidebar.markdown("""
### 📌 How to Use:
1. Get a **free API key** from [OpenWeatherMap](https://openweathermap.org/).
2. Paste it above.
3. Click **"Pull Latest Data"**.
4. View the results!
""")