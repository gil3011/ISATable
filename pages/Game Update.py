import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Login Required")
    password = st.text_input("Enter password:", type="password")
    if st.button("Login"):
        if password == "ISA2025fall":  
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Incorrect password")
    st.stop()

conn = sqlite3.connect("isasoftball.db")
cursor = conn.cursor()

st.title("⚾ Update Game Results")

# 🔍 Load unplayed games
games_query = """
SELECT g.id, ht.name AS home_team, at.name AS away_team, date, location, played, away_score, home_score
FROM games g
JOIN teams ht ON g.home_team_id = ht.id
JOIN teams at ON g.away_team_id = at.id
ORDER BY g.date
"""
games_df = pd.read_sql_query(games_query, conn)
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
# ✅ Submit button
if st.button("Submit"):
    combined_date = datetime(date.year, date.month, date.day,time.hour, time.minute)
    if not played:
        home_score=0
        away_score=0
    update_query = f"""
    UPDATE games
    SET home_score = {home_score}, away_score = {away_score}, played = ?, date = ? , location = ?
    WHERE id = {selected_game["id"]}
    """
    try:
        cursor.execute(update_query,[played,combined_date, venue])
        conn.commit()
        st.success("🎉 Game result updated successfully!")


        
    except sqlite3.Error as e:
        st.error(f"❌ An error occurred: {e}")


conn.close()