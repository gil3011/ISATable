import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine,text

st.set_page_config(page_title="Games Update", page_icon="⚾", layout="wide")
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Login Required")
    password = st.text_input("Enter password:", type="password")
    if st.button("Login"):
        if password == st.secrets["passwords"]["login"]:  
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Incorrect password")
    st.stop()

username = st.secrets["database"]["username"]
password = st.secrets["database"]["password"]
host = st.secrets["database"]["host"]
name = st.secrets["database"]["name"]
engine = create_engine(
    f"mysql+pymysql://{username}:{password}@/{name}"
)


st.title("⚾ Update Game Results")

# 🔍 Load unplayed games
games_query = """
SELECT g.id, ht.name AS home_team, at.name AS away_team, date, location, played, away_score, home_score
FROM games g
JOIN teams ht ON g.home_team_id = ht.id
JOIN teams at ON g.away_team_id = at.id
ORDER BY g.date
"""
games_df = pd.read_sql_query(games_query, engine)
games_df["date"] = pd.to_datetime(games_df["date"],format='mixed')

# 🎯 Select a game

games_df["match"] = games_df["home_team"] + " vs " + games_df["away_team"] + " (" + games_df["date"].dt.strftime("%d/%m/%Y - %H:%M") + ")"
selected_match = st.selectbox("Select a game to update:", games_df["match"])
selected_game = games_df[games_df["match"] == selected_match].iloc[0]
# 📝 Input scores
date = st.date_input("Select Date:", value=selected_game["date"].date())
time = st.time_input("Select Time:", value=selected_game["date"].time())
venue = st.text_input("Venue:",value=selected_game["location"])
played = st.checkbox("played",value=selected_game['played'])
home_score = st.number_input(f"{selected_game['home_team']} score", min_value=0, step=1,value=0 if pd.isna(selected_game['home_score'])  else int(selected_game['home_score']))
away_score = st.number_input(f"{selected_game['away_team']} score", min_value=0, step=1,value=0 if pd.isna(selected_game['away_score']) else int(selected_game['away_score']))
import numpy as np

# Convert to native Python types

home_score = int(home_score) if isinstance(home_score, (np.integer, np.int64)) else home_score
away_score = int(away_score) if isinstance(away_score, (np.integer, np.int64)) else away_score
game_id = int(selected_game["id"]) if isinstance(selected_game["id"], (np.integer, np.int64)) else selected_game["id"]


# ✅ Submit button
if st.button("Submit"):
    combined_date = datetime(date.year, date.month, date.day, time.hour, time.minute)
    
    if not played:
        home_score = 0
        away_score = 0

    update_query = text("""
        UPDATE games
        SET home_score = :home_score,
            away_score = :away_score,
            played = :played,
            date = :date,
            location = :location
        WHERE id = :game_id
    """)

    try:
        with engine.connect() as connection:
            connection.execute(update_query, {
                "home_score": home_score,
                "away_score": away_score,
                "played": played,
                "date": combined_date,
                "location": venue,
                "game_id": game_id
            })
        st.success("🎉 Game result updated successfully!")

    except Exception as e:
        st.error(f"❌ An error occurred: {e}")