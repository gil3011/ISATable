import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 📡 Connect to DB
conn = sqlite3.connect("isasoftball.db")
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

# 🧾 Display games

def display_games(df):
    st.title("📅 Game Schedule & Results")
    st.divider()

    # Create a 2-column grid to display games side-by-side
    game_cols = st.columns(2)
    
    for index, row in df.iterrows():
        # Cycle through the columns for each game
        with game_cols[index % 2]:
            # Use a container to visually separate each game card
            with st.container(border=True):
                home_score_style = ""
                away_score_style = ""
                status_text = ""
                
                # Conditional styling logic remains the same
                if row['played']:
                    if row['home_score'] > row['away_score']:
                        home_score_style = "color: green; font-weight: bold; text-align: center;"
                        away_score_style = "color: #888; text-align: center;"
                        status_text = "Final"
                    elif row['away_score'] > row['home_score']:
                        away_score_style = "color: green; font-weight: bold; text-align: center;"
                        home_score_style = "color: #888; text-align: center;"
                        status_text = "Final"
                    else:
                        home_score_style = "font-weight: bold; text-align: center;"
                        away_score_style = "font-weight: bold; text-align: center;"
                        status_text = "Tie"
                else:
                    status_text = "Upcoming"
                    home_score_style = "color: #888; text-align: center;"
                    away_score_style = "color: #888; text-align: center;"

                # Internal layout for a single game card
                game_card_cols = st.columns([1, 2, 1])
                
                with game_card_cols[0]:
                    st.image(row['home_logo'],width=80)
                    st.markdown(f"<h3 style='{home_score_style}'>{int(row['home_score']) if row['played'] else '-'}</h3>", unsafe_allow_html=True)

                with game_card_cols[1]:
                    st.markdown(f"<p style='text-align: center;'>{status_text}</p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='text-align: center; color: #888;'>{row['date'].strftime('%d/%m')}</p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='text-align: center; color: #888;'>{row['date'].strftime('%H:%M')}</p>", unsafe_allow_html=True)
                
                with game_card_cols[2]:
                    st.image(row['away_logo'],width=80)
                    st.markdown(f"<h3 style='{away_score_style}'>{int(row['away_score']) if row['played'] else '-'}</h3>", unsafe_allow_html=True)
# 🧮 Apply filters or show all
if st.button("Filter", use_container_width=True):
    filtered_df = filter_schedule(
        games_df,
        teams=selected_teams,
        divisions=selected_divisions,
        venues=selected_venues,
        played_status=selected_status
    )
    display_games(filtered_df)
else:
    display_games(games_df)
