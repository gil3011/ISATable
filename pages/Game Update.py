import streamlit as st
import pandas as pd
from datetime import datetime , time
from sqlalchemy import create_engine,text
import numpy as np

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
    f"mysql+pymysql://{username}:{password}@{host}/{name}"
)


st.title("⚾ Update Game Results")

# 🔍 Load unplayed games
games_query = """
SELECT g.id, ht.name AS home_team, at.name AS away_team, date, location, played, away_score, home_score , g.division
FROM games g
JOIN teams ht ON g.home_team_id = ht.id
JOIN teams at ON g.away_team_id = at.id
ORDER BY g.date
"""
games_df = pd.read_sql_query(games_query, engine)
games_df["date"] = pd.to_datetime(games_df["date"],format='mixed')

# 🎯 Select a game

games_df["match"] = games_df.apply(
    lambda row: f"{row['home_team']} vs {row['away_team']} ({row['date'].strftime('%d/%m/%Y - %H:%M')})"
    if pd.notnull(row['date']) else f"{row['home_team']} vs {row['away_team']} (TBD)",
    axis=1
)
# Find the index of the next scheduled game
future_games = games_df[games_df["date"] > datetime.now()]
if not future_games.empty:
    next_game_match = future_games.iloc[0]["match"]
    default_index = int(games_df[games_df["match"] == next_game_match].index[0]) - 1
else:
    default_index = 0  # fallback if no future games




selected_match = st.selectbox("Select a game to update:", games_df["match"], index=default_index)
selected_game = games_df[games_df["match"] == selected_match].iloc[0]
default_date = selected_game["date"].date() if pd.notnull(selected_game["date"]) else datetime.today().date()


if pd.notnull(selected_game["date"]):
    default_time = selected_game["date"].time()
else:
    if selected_game["division"].lower() == "women":
        default_time = time(19, 30)
    else:
        default_time = time(20, 30)

tbd = st.checkbox("To be scheduled",disabled=selected_game["played"],value=selected_game["date"]==None)
date = st.date_input("Select Date:", value=default_date,disabled=tbd)
time = st.time_input("Select Time:", value=default_time,disabled=tbd)
venue = st.text_input("Venue:",value=selected_game["location"])
home_score_val = 0 if pd.isna(selected_game['home_score']) else int(selected_game['home_score'])
away_score_val = 0 if pd.isna(selected_game['away_score']) else int(selected_game['away_score'])

home_score = st.number_input(f"{selected_game['home_team']} score", min_value=0, step=1, value=home_score_val)
away_score = st.number_input(f"{selected_game['away_team']} score", min_value=0, step=1, value=away_score_val)


played = st.checkbox("played",value=selected_game['played'])

home_score = int(home_score) if isinstance(home_score, (np.integer, np.int64)) else home_score
away_score = int(away_score) if isinstance(away_score, (np.integer, np.int64)) else away_score
game_id = int(selected_game["id"]) if isinstance(selected_game["id"], (np.integer, np.int64)) else selected_game["id"]


# ✅ Submit button
if st.button("Submit"):
    if not tbd:
        combined_date = datetime(date.year, date.month, date.day, time.hour, time.minute)
    else:
        combined_date = None

    update_query = text("""
        UPDATE games
        SET home_score = :home_score,
            away_score = :away_score,
            played = :played,
            date = :date,
            location = :location
        WHERE id = :game_id
    """)
    st.markdown("### 📝 Update Preview")
    st.write({
        "Game ID": game_id,
        "Date": combined_date,
        "Venue": venue,
        "Home Score": home_score,
        "Away Score": away_score,
        "Played": played
    })

    try:
        with engine.begin() as connection:
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
with st.expander(label="Delete Game"):
    st.warning("Deleting this game will permanently remove all saved progress, settings, and associated data. This action cannot be undone. Are you sure you want to continue?")
    if st.button("Delete Game",type="secondary",use_container_width=True):
        remove_query = text("""
            Delete From games
            WHERE id = :game_id
        """)
        try:
            with engine.begin() as connection:  
                connection.execute(remove_query, {
                    "game_id": game_id
                })
            st.success("🎉 Game was removed successfully!")
        except Exception as e:
            st.error(f"❌ An error occurred: {e}")
