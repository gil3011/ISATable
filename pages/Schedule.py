import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

st.set_page_config(page_title="Full Schedule", page_icon="📅", layout="wide")

# 📡 Connect to DB
conn = sqlite3.connect("isasoftball.db")

st.title("📅 Schedule")

games_query = """
SELECT g.id, ht.name AS home_team, at.name AS away_team,
    date, location, played, away_score, home_score, g.div AS Division,
    at.logo AS away_logo, ht.logo AS home_logo
FROM games g
JOIN teams ht ON g.home_team_id = ht.id
JOIN teams at ON g.away_team_id = at.id
ORDER BY g.date
"""
games_df = pd.read_sql_query(games_query, conn)
games_df["date"] = pd.to_datetime(games_df["date"], format='mixed')

# 🧠 Unique filter options
teams = sorted(games_df["home_team"].unique())
divisions = sorted(games_df["Division"].unique())
venues = sorted(games_df["location"].unique())
played_options = ["Scheduled", "Played"]

# 🎛️ Filter inputs
selected_teams = st.multiselect("Select teams:", teams, placeholder="All")
cols = st.columns([0.33, 0.33, 0.33])
with cols[0]:
    selected_venues = st.multiselect("Select venues:", venues, placeholder="All")
with cols[1]:
    selected_divisions = st.multiselect("Select divisions:", divisions, placeholder="All")
with cols[2]:
    selected_status = st.multiselect("Select status:", played_options, placeholder="All")

# 🧠 Filtering function
def filter_schedule(df, teams=None, divisions=None, venues=None, played_status=None):
    if teams:
        df = df[df["home_team"].isin(teams) | df["away_team"].isin(teams)]
    if divisions:
        df = df[df["Division"].isin(divisions)]
    if venues:
        df = df[df["location"].isin(venues)]
    if played_status:
        status_filter = []
        if "Scheduled" in played_status:
            status_filter.append(0)
        if "Played" in played_status:
            status_filter.append(1)
        df = df[df["played"].isin(status_filter)]
    return df

def display_games(games_df):
    st.markdown("""
    <style>
    .game-card {
        border-radius: 10px;
        padding: 10px;
        text-align: center;
        box-shadow: 0 4px 4px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    .played-game {
        background-color: #e8f5e9;
    }
    .scheduled-game {
        background-color: #e3f2fd;
    }
    .game-teams {
        display: flex;
        align-items: center;
        justify-content: space-around;
        gap: 10px;
    }
    .game-logo {
        width: 50px;
        height: 50px;
        border-radius: 5px;
    }
    .game-score-info {
        line-height: 1.4;
    }
    </style>
    """, unsafe_allow_html=True)
    for _, row in games_df.iterrows():
        is_played = row.get('played')
        card_class = "played-game" if is_played else "scheduled-game"
        
        game_info = ""
        if is_played:
            game_info = f"Final:<br>{int(row['home_score'])} - {int(row['away_score'])}"
        else:
            game_info = f"{pd.to_datetime(row['date']).strftime('%b %d')}<br>{pd.to_datetime(row['date']).strftime('%I:%M %p')}<br>{row['location']}"
        st.markdown(f"""
        <div class="game-card {card_class}">
            <div class="game-teams">
                <img src="{row['home_logo']}" class="game-logo">
                <div class="game-score-info">{game_info}</div>
                <img src="{row['away_logo']}" class="game-logo">
            </div>
        </div>
        """, unsafe_allow_html=True)

if st.button("Filter", use_container_width=True):
    filtered_df = filter_schedule(
        games_df,
        teams=selected_teams,
        divisions=selected_divisions,
        venues=selected_venues,
        played_status=selected_status
    ).reset_index(drop=True)
    display_games(filtered_df)
else:
    display_games(games_df)
