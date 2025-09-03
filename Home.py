import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# Streamlit setup
st.set_page_config(page_title="Israel Softball", page_icon="🏆", layout="wide")
st.logo("https://raw.githubusercontent.com/gil3011/ISATable/refs/heads/main/logos/with%20white%20softball.png")

# SQLAlchemy connection string
username = st.secrets["database"]["username"]
password = st.secrets["database"]["password"]
host = st.secrets["database"]["host"]
name = st.secrets["database"]["name"]
engine = create_engine(
    f"mysql+pymysql://{username}:{password}@/{name}"
)


st.title("🏆 ISA Fall League Standings 2025")

# 🧠 Load all teams with division info
teams_query = "SELECT id, name, division, logo FROM teams"
teams_df = pd.read_sql_query(teams_query, engine)
standings = pd.DataFrame({
        "Team": teams_df["name"],
        "W": 0,
        "L": 0,
        "D": 0,
        "GP": 0,
        "W%": 0.0,
        "division": teams_df["division"]
    })
standings["logo"] = teams_df["logo"]

played_query = """
SELECT ht.name AS home_team, at.name AS away_team, g.home_score, g.away_score
FROM games g
JOIN teams ht ON g.home_team_id = ht.id
JOIN teams at ON g.away_team_id = at.id
WHERE g.played = TRUE
"""
games_df = pd.read_sql_query(played_query, engine)
home_wins = games_df['home_score'] > games_df['away_score']
away_wins = games_df['away_score'] > games_df['home_score']
draws = games_df['home_score'] == games_df['away_score']

standings.loc[standings['Team'].isin(games_df['home_team'][home_wins]), 'W'] += 1
standings.loc[standings['Team'].isin(games_df['home_team'][away_wins]), 'L'] += 1
standings.loc[standings['Team'].isin(games_df['home_team'][draws]), 'D'] += 1

standings.loc[standings['Team'].isin(games_df['away_team'][home_wins]), 'L'] += 1
standings.loc[standings['Team'].isin(games_df['away_team'][away_wins]), 'W'] += 1
standings.loc[standings['Team'].isin(games_df['away_team'][draws]), 'D'] += 1

# Convert to DataFrame
standings["GP"] = standings["W"] + standings["L"] + standings["D"]
standings["W%"] = (standings["W"] / standings["GP"]).round(2).fillna(0)

men_df = standings[standings["division"] == "Men"].sort_values(by=["W%", "W", "L","GP"], ascending=[False, False, True,False])
women_df = standings[standings["division"] == "Women"].sort_values(by=["W%", "W", "L","GP"], ascending=[False, False, True,False])
men_df["GB"] = ((men_df.iloc[0]["W"] + men_df.iloc[0]["D"] / 2) - (men_df["W"] + men_df["D"] / 2) + (men_df["L"] + men_df["D"] / 2) - (men_df.iloc[0]["L"] + men_df.iloc[0]["D"] / 2))/2
women_df["GB"] = ((women_df.iloc[0]["W"] + women_df.iloc[0]["D"] / 2) - (women_df["W"] + women_df["D"] / 2) + (women_df["L"] + women_df["D"] / 2) - (women_df.iloc[0]["L"] + women_df.iloc[0]["D"] / 2))/2

def display_standings(df, division_name):
    st.subheader(f"{division_name} Standings")
    st.markdown("""
        <style>
        .table-container {
            border: 1px solid #ddd;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            background-color: #fff;
            padding: 10px;
        }
        .table-header, .table-row {
            display: flex;
            align-items: center;
            font-weight: bold;
            padding: 10px;
            border-bottom: 1px solid #eee;
        }
        .table-row:hover {
            background-color: #f0f0f0;
            cursor: pointer;
        }
        .header-item, .row-item {
            flex: 1;
            text-align: center;
        }

        .header-item:nth-child(2), .row-item:nth-child(2) {
            flex: 0 0 70px; /* Logo column */
            text-align: center;
        }
        .team-logo {
            width: 40px;
            height: 40px;
            border-radius: 5px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    with st.container():        
        st.markdown("""
            <div class="table-header">
                <span class="header-item">Rank</span>
                <span class="header-item">Team</span>
                <span class="header-item">W</span>
                <span class="header-item">L</span>
                <span class="header-item">D</span>
                <span class="header-item">W%</span>
                <span class="header-item">GB</span>
            </div>
        """, unsafe_allow_html=True)
        
        rank = 1
        for _, row in df.iterrows():
            logo = row["logo"]
            wins = row["W"]
            losses = row["L"]
            draws = row["D"]
            win_percent = row["W%"]
            games_behind = row["GB"]
            
            # Table Row for each team
            st.markdown(f"""
                <div class="table-row">
                    <span class="row-item">{rank}</span>
                    <span class="row-item"><img src="{logo}" class="team-logo"></span>
                    <span class="row-item">{wins}</span>
                    <span class="row-item">{losses}</span>
                    <span class="row-item">{draws}</span>
                    <span class="row-item">{win_percent}</span>
                    <span class="row-item">{games_behind}</span>
                </div>
            """, unsafe_allow_html=True)
            rank += 1
            
        st.markdown('</div>', unsafe_allow_html=True)

st.subheader("Stangings")
tab1, tab2 = st.tabs(["Men’s Division", "Women’s Division"])

with tab1:
    display_standings(men_df, "Men’s Division")

with tab2:
    display_standings(women_df, "Women’s Division")

games_query = """
SELECT ht.name AS home_team, at.name AS away_team, g.home_score, g.away_score,
    at.logo AS away_logo, ht.logo AS home_logo, g.date, g.division, g.location, g.played
FROM games g
JOIN teams ht ON g.home_team_id = ht.id
JOIN teams at ON g.away_team_id = at.id
"""

def display_games_row_dynamic(played_games_df, scheduled_games_df):
    st.subheader("Upcoming & Previous Games")
    st.markdown("""
        <style>
        .game-card {
            border-radius: 10px;
            padding: 10px;
            text-align: center;
            box-shadow: 0 4px 4px rgba(0,0,0,0.1);
            margin-bottom:15px;
        }
        .played-game {
            background-color: #e8f5e9; /* Light green */
        }
        .scheduled-game {
            background-color: #e3f2fd; /* Light blue */
        }
        .game-teams {
            display: flex;
            align-items: center;
            justify-content: space-evenly;
            gap: 10px;
        }
        .game-logo {
            width: 30px;
            height: 30px;
            border-radius: 5px;
            border: 1px solid #eee;
        }
        .game-score-info {
            font-size: 14px;
            color: #555;
            margin: 10px 0;
            line-height: 1.4;
        }
        .game-details {
            font-size: 12px;
            color: #888;
        }
        </style>
    """, unsafe_allow_html=True)
    if len(played_games_df)<2:
        last_played = played_games_df.tail(len(played_games_df))
        next_scheduled = scheduled_games_df.head(4-len(played_games_df))
    elif len(scheduled_games_df)<2:
        last_played = played_games_df.tail(4-len(scheduled_games_df))
        next_scheduled = scheduled_games_df.head(len(scheduled_games_df))        
    else:
        last_played = played_games_df.tail(2)
        next_scheduled = scheduled_games_df.head(2)
    
    # Combine the dataframes
    all_games = pd.concat([last_played, next_scheduled]).reset_index(drop=True)
    
    # Create a number of columns equal to the number of games
    cols= st.columns(len(all_games))
    for i, row in all_games.iterrows():
        is_played = row.get('played')
        card_class = "played-game" if is_played else "scheduled-game"
        game_info = ""
        if is_played:
            game_info = f"Final:<br>{int(row['home_score'])} - {int(row['away_score'])}"
        else:
            game_info = f"{pd.to_datetime(row['date']).strftime('%b %d')}<br>{pd.to_datetime(row['date']).strftime('%I:%M %p')}"
        with(cols[i]):    
            st.markdown(f"""
                <div class="game-card {card_class}">
                    <div class="game-teams">
                        <img src="{row['home_logo']}" class="game-logo">
                        <span>vs</span>
                        <img src="{row['away_logo']}" class="game-logo">
                    </div>
                    <div class="game-score-info">
                        {game_info}
                    </div>
                    <div class="game-details">
                        <span>{row['location']}</span><br>
                    </div>
                </div>
            """,unsafe_allow_html=True)


    
    st.page_link(label="Full Schedule",page="pages/Schedule.py")

games = pd.read_sql_query(games_query, engine)
played_games_df = games[games["played"]==True].sort_values(by='date')
scheduled_games_df = games[games["played"]==False].sort_values(by='date')
display_games_row_dynamic(played_games_df, scheduled_games_df)