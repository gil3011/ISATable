import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import numpy as np # Import numpy for conditional logic

st.set_page_config(page_title="Full Schedule", page_icon="🪐", layout="wide")

# 📡 Connect to DB
username = st.secrets["database"]["username"]
password = st.secrets["database"]["password"]
host = st.secrets["database"]["host"]
name = st.secrets["database"]["name"]
engine = create_engine(
    f"mysql+pymysql://{username}:{password}@{host}/{name}"
)
st.title("📅 Schedule")

games_query = """
SELECT g.id, ht.name AS home_team, at.name AS away_team,
    date, location, played, away_score, home_score, g.division AS Division,
    at.logo AS away_logo, ht.logo AS home_logo
FROM games g
JOIN teams ht ON g.home_team_id = ht.id
JOIN teams at ON g.away_team_id = at.id
ORDER BY g.date
"""
games_df = pd.read_sql_query(games_query, engine)
games_df["date"] = pd.to_datetime(games_df["date"], format='mixed')

# --- FORFEIT LOGIC IMPLEMENTATION ---

# 1. Identify the forfeit condition: score 7-0 or 0-7 AND played = 0 (False)
forfeit_condition = (
    ((games_df['home_score'] == 7) & (games_df['away_score'] == 0)) |
    ((games_df['home_score'] == 0) & (games_df['away_score'] == 7))
) & (games_df['played'] == 0)

# 2. Add a new column to explicitly flag forfeits for display logic
games_df['is_forfeit'] = np.where(forfeit_condition, True, False)

# 3. Update the 'played' status for forfeited games to True (1)
# This ensures forfeits are treated as "Played" games for general filtering/display
games_df.loc[forfeit_condition, 'played'] = 1

# --- END FORFEIT LOGIC IMPLEMENTATION ---


# 🧠 Unique filter options
teams = sorted(games_df["home_team"].unique())
divisions = sorted(games_df["Division"].unique())
venues = sorted(games_df["location"].unique())
# Updated played_options to be correct for the logic
played_options = ["Scheduled", "Played", "Unscheduled"] 

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
    # Make a copy to prevent SettingWithCopyWarning
    df_filtered = df.copy() 
    
    if teams:
        df_filtered = df_filtered[df_filtered["home_team"].isin(teams) | df_filtered["away_team"].isin(teams)]
    if divisions:
        df_filtered = df_filtered[df_filtered["Division"].isin(divisions)]
    if venues:
        df_filtered = df_filtered[df_filtered["location"].isin(venues)]
    
    if played_status:
        # Separate filtering for games with a scheduled date (played or scheduled)
        has_date_filter = df_filtered[df_filtered["date"].notna()]
        
        status_filter_list = []
        
        if "Played" in played_status:
            # Played includes officially played and forfeited games (due to previous logic)
            status_filter_list.append(1) 
        if "Scheduled" in played_status:
            # Scheduled are games with a date that haven't been played/forfeited
            status_filter_list.append(0) 
            
        if status_filter_list:
            has_date_filter = has_date_filter[has_date_filter["played"].isin(status_filter_list)]
        
        # Separate filtering for unscheduled games
        unscheduled_filter = df_filtered[df_filtered["date"].isna()]
        
        if "Unscheduled" in played_status:
            if not status_filter_list:
                # If only Unscheduled is selected
                df_filtered = unscheduled_filter
            else:
                # If Scheduled/Played are selected along with Unscheduled
                df_filtered = pd.concat([has_date_filter, unscheduled_filter]).drop_duplicates(subset=['id'])
        else:
            # If only Scheduled/Played are selected
            df_filtered = has_date_filter
            
    return df_filtered

# 🎨 Display function
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
    .forfeit-game {
        background-color: #ffebcc; /* Light orange/yellow for forfeit */
        border: 2px solid #ff9800;
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
        font-weight: bold;
    }
    .game-status {
        font-size: 16px;
        color: #555;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Sort the DataFrame to ensure forfeits (now played=1) are still ordered by date
    games_df = games_df.sort_values(by='date', ascending=True, na_position='last')

    for _, row in games_df.iterrows():
        is_played = row.get('played') # Now includes forfeits
        is_forfeit = row.get('is_forfeit', False) # Check the explicit forfeit flag
        
        # Determine the correct card style
        if is_forfeit:
            card_class = "forfeit-game"
        elif is_played:
            card_class = "played-game"
        else:
            card_class = "scheduled-game"
        
        game_status_text = ""
        game_info = ""
        
        if is_forfeit:
            game_status_text = "FORFEIT"
            game_info = f"{int(row['home_score'])} - {int(row['away_score'])}"
        elif is_played:
            game_status_text = "FINAL"
            game_info = f"{int(row['home_score'])} - {int(row['away_score'])}"
        elif pd.isna(row['date']):
            game_status_text = "TBD"
            game_info = f"{row['location']}"
        else:
            game_status_text = "SCHEDULED"
            game_info = f"{row['date'].strftime('%b %d')}<br>{row['date'].strftime('%I:%M %p')}<br>{row['location']}"
            
        st.markdown(f"""
        <div class="game-card {card_class}">
            <div class="game-teams">
                <img src="{row['home_logo']}" class="game-logo" title="{row['home_team']}">
                <div>
                    <div class="game-status">{game_status_text}</div>
                    <div class="game-score-info">{game_info}</div>
                </div>
                <img src="{row['away_logo']}" class="game-logo" title="{row['away_team']}">
            </div>
        </div>  
        """, unsafe_allow_html=True)

if st.button("Filter", use_container_width=True):
    st.session_state["games"] = filter_schedule(
        games_df,
        teams=selected_teams,
        divisions=selected_divisions,
        venues=selected_venues,
        played_status=selected_status
    ).reset_index(drop=True)
    # The st.rerun() is unnecessary and can cause issues if clicked multiple times quickly
    # The assignment to session_state is enough, and the subsequent logic will handle the display.

# Display logic
if st.button("Clear Filter", key="clear_filter"):
    if "games" in st.session_state:
        del st.session_state["games"]
    st.rerun()

if "games" not in st.session_state or st.session_state["games"].empty:
    if "games" in st.session_state and st.session_state["games"].empty:
         st.warning("No games match the selected filters.")
    else:
        # Initial display of all games
        display_games(games_df) 
else:
    # Display filtered games
    display_games(st.session_state["games"])