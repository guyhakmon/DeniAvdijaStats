import streamlit as st
# Set the page configuration

from nba_api.stats.endpoints import playercareerstats, playergamelog, PlayerNextNGames, boxscoretraditionalv2
from nba_api.stats.static import players
import plotly.graph_objects as go
import pandas as pd
from pytube import Search
from datetime import datetime
from sklearn.linear_model import LinearRegression
import numpy as np
from nba_api.stats.endpoints import teamgamelog
from nba_api.stats.static import teams
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from streamlit_gsheets import GSheetsConnection

st.set_page_config(
    page_title='Maakabdi-App',
    page_icon="https://cdn.nba.com/headshots/nba/latest/1040x760/1630166.png",
    layout="centered",
    initial_sidebar_state="expanded"
)
# Add custom CSS for page styling
st.markdown(
    """
    <style>
    .basketball {
        position: fixed;
        bottom: 20px;
        right: 30px;
        width: 50px;
        height: 50px;
        background-image: url('https://upload.wikimedia.org/wikipedia/commons/7/7a/Basketball.png');
        background-size: cover;
        border-radius: 50%;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    </style>
    <div class="basketball"></div>
    """,
    unsafe_allow_html=True
)

# Streamlit app title
st.markdown(
    """
    <style>
    body {
        direction: rtl;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("מעקבדי-דף")
# Add a photo of Deni Avdija
st.image("https://cdn.nba.com/headshots/nba/latest/1040x760/1630166.png", caption="Deni Avdija", width=300)


# Find player ID for Deni Avdija
player_dict = players.find_players_by_full_name("Deni Avdija")
player_id = player_dict[0]['id']

# Get career stats for Deni Avdija
career = playercareerstats.PlayerCareerStats(player_id=player_id)
career_stats = career.get_data_frames()[0]

# Get game logs for the current season
current_season = '2024-25'  # Update this to the current season
gamelog = playergamelog.PlayerGameLog(player_id=player_id, season=current_season)
gamelog_stats = gamelog.get_data_frames()[0]

# Get stats for the last game
last_game_stats = gamelog_stats.iloc[0]
last_game_date = pd.to_datetime(last_game_stats['GAME_DATE']).strftime('%B %d, %Y')

# Initialize Google Sheets connection
conn = st.connection("gsheets", type=GSheetsConnection)

# Read data from Google Sheets
def read_sheet(sheet_name):
    return conn.read(worksheet=sheet_name)

# Write data to Google Sheets
def write_sheet(sheet_name, data):
    try:
        existing_data = conn.read(worksheet=sheet_name)
        updated_data = pd.concat([existing_data, data], ignore_index=True)
        conn.update(worksheet=sheet_name, data=updated_data)
    except Exception as e:
        conn.create(worksheet=sheet_name, data=data)
    # Clear the cache and reload the data
    st.cache_data.clear()


# Function to calculate points based on the accuracy of the guess
def calculate_points(guess, actual):
    points = 0
    # Basic stats (up to 10 points each)
    points += max(0, 10 - abs(guess["points"] - actual["points"]))
    points += max(0, 10 - abs(guess["rebounds"] - actual["rebounds"]))
    points += max(0, 10 - abs(guess["assists"] - actual["assists"]))
    points += max(0, 10 - abs(guess["steals"] - actual["steals"]))
    points += max(0, 10 - abs(guess["blocks"] - actual["blocks"]))
    
    # Shooting stats (up to 15 points each)
    points += max(0, 15 - 3 * abs(guess["fgm"] - actual["fgm"]))
    points += max(0, 15 - 3 * abs(guess["fga"] - actual["fga"]))
    points += max(0, 15 - 3 * abs(guess["fg3m"] - actual["fg3m"]))
    points += max(0, 15 - 3 * abs(guess["fg3a"] - actual["fg3a"]))
    
    # Bonus points for perfect predictions
    if guess["points"] == actual["points"]: points += 5
    if guess["fgm"] == actual["fgm"] and guess["fga"] == actual["fga"]: points += 10
    if guess["fg3m"] == actual["fg3m"] and guess["fg3a"] == actual["fg3a"]: points += 10
    
    return points

# Read the actual stats from the game log
def get_actual_stats(game_date, gamelog_stats):
    game_stats = gamelog_stats[gamelog_stats['GAME_DATE'] == game_date].iloc[0]
    return {
        "points": game_stats['PTS'],
        "rebounds": game_stats['REB'],
        "assists": game_stats['AST'],
        "steals": game_stats['STL'],
        "blocks": game_stats['BLK'],
        "fgm": game_stats['FGM'],
        "fga": game_stats['FGA'],
        "fg3m": game_stats['FG3M'],
        "fg3a": game_stats['FG3A']
    }
def update_points_from_guesses(guesses_df, points_df, gamelog_stats):
    # Get list of played games from gamelog_stats
    played_game_dates = gamelog_stats['GAME_DATE'].tolist()

    # Get guesses for games that have been played but points haven't been calculated yet
    for game_date in played_game_dates:
        # Check if points already calculated for this game
        if len(points_df[points_df['game_date'] == game_date]) == 0:
            # Get guesses for this game
            game_guesses = guesses_df[guesses_df['game_date'] == game_date]
            
            if not game_guesses.empty:
                try:
                    actual_stats = get_actual_stats(game_date, gamelog_stats)
                    for _, guess in game_guesses.iterrows():
                        name = guess['name']
                        guess_dict = {
                            "points": guess['points'],
                            "rebounds": guess['rebounds'],
                            "assists": guess['assists'],
                            "steals": guess['steals'],
                            "blocks": guess['blocks'],
                            "fgm": guess['fgm'],
                            "fga": guess['fga'],
                            "fg3m": guess['fg3m'],
                            "fg3a": guess['fg3a']
                        }
                        points = calculate_points(guess_dict, actual_stats)
                        new_point = pd.DataFrame({
                            "game_date": [game_date], 
                            "name": [name], 
                            "points": [points]
                        })
                        points_df = pd.concat([points_df, new_point], ignore_index=True)
                    write_sheet("points", points_df)
                except Exception as e:
                    st.warning(f"Could not calculate points for game {game_date}: {str(e)}")
                    
    return points_df

# Calculate points if not already calculated for played games
guesses_df = read_sheet("guesses")
points_df = read_sheet("points")
points_df = update_points_from_guesses(guesses_df, points_df, gamelog_stats)

# Create a new reaction for each new game
game_date_str = last_game_date.replace(" ", "_")
reactions_df = read_sheet("reactions")

# Summarize current season stats
current_season_stats = gamelog_stats[['GAME_DATE', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'FG_PCT', 'FG3_PCT']]
current_season_stats['GAME_DATE'] = pd.to_datetime(current_season_stats['GAME_DATE'])


# Calculate average stats for the current season
average_stats = current_season_stats.mean(numeric_only=True)[['PTS', 'REB', 'AST', 'STL', 'BLK', 'FG_PCT', 'FG3_PCT']]

# Create a DataFrame for the average stats
average_stats_df = pd.DataFrame({
    'Points': [average_stats['PTS']],
    'Rebounds': [average_stats['REB']],
    'Assists': [average_stats['AST']],
    'Steals': [average_stats['STL']],
    'Blocks': [average_stats['BLK']],
    'Field Goal %': [average_stats['FG_PCT'] * 100],
    'Three-Point %': [average_stats['FG3_PCT'] * 100]
})

# Display the average stats in a table
st.subheader("ממוצעים אבדי-עונתיים")
st.dataframe(average_stats_df)

# Create a DataFrame for the last game stats
st.subheader("אבדי-סטטיסטיקות משחק האחרון")
last_game_stats_df = pd.DataFrame({
    'Date': [last_game_date],
    'Points': [last_game_stats['PTS']],
    'Rebounds': [last_game_stats['REB']],
    'Assists': [last_game_stats['AST']],
    'Steals': [last_game_stats['STL']],
    'Blocks': [last_game_stats['BLK']],
    'Field Goal %': [last_game_stats['FG_PCT'] * 100],
    'Three-Point %': [last_game_stats['FG3_PCT'] * 100],
    'Minutes': [last_game_stats['MIN']],
    'Turnovers': [last_game_stats.get('TO', 0)],
    'Personal Fouls': [last_game_stats['PF']],
    'Free Throws Made': [last_game_stats['FTM']],
    'Free Throws Attempted': [last_game_stats['FTA']],
    'Free Throw %': [last_game_stats['FT_PCT'] * 100],
    'Offensive Rebounds': [last_game_stats['OREB']],
    'Defensive Rebounds': [last_game_stats['DREB']],
    'Field Goals Made': [last_game_stats['FGM']],
    'Field Goals Attempted': [last_game_stats['FGA']],
    'Three-Point Field Goals Made': [last_game_stats['FG3M']],
    'Three-Point Field Goals Attempted': [last_game_stats['FG3A']]
})



# Display the last game stats in a table
st.dataframe(last_game_stats_df)

if st.button("פתח את תיבת התוצאות המלאה"):
    # Get the boxscore for the last game

    # Get the game ID for the last game
    last_game_id = last_game_stats['Game_ID']

    # Fetch the boxscore for the last game
    boxscore = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=last_game_id)
    boxscore_stats = boxscore.get_data_frames()[0]
    # Filter the boxscore to show only relevant columns
    relevant_columns = ['PLAYER_NAME', 'MIN', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TO', 'PF', 'FGM', 'FGA', 'FG_PCT', 'FG3M', 'FG3A', 'FG3_PCT', 'FTM', 'FTA', 'FT_PCT']
    boxscore_stats = boxscore_stats[['PLAYER_NAME', 'TEAM_ABBREVIATION'] + relevant_columns[1:]]

    # Split the boxscore into two DataFrames, one for each team
    team1_abbr = boxscore_stats['TEAM_ABBREVIATION'].unique()[0]
    team2_abbr = boxscore_stats['TEAM_ABBREVIATION'].unique()[1]

    if team1_abbr == 'POR':
        por_stats = boxscore_stats[boxscore_stats['TEAM_ABBREVIATION'] == team1_abbr]
        other_team_stats = boxscore_stats[boxscore_stats['TEAM_ABBREVIATION'] == team2_abbr]
        other_team_name = teams.find_team_by_abbreviation(team2_abbr)['full_name']
    else:
        por_stats = boxscore_stats[boxscore_stats['TEAM_ABBREVIATION'] == team2_abbr]
        other_team_stats = boxscore_stats[boxscore_stats['TEAM_ABBREVIATION'] == team1_abbr]
        other_team_name = teams.find_team_by_abbreviation(team1_abbr)['full_name']

    # Remove the TEAM_ABBREVIATION column
    por_stats = por_stats.drop(columns=['TEAM_ABBREVIATION'])
    other_team_stats = other_team_stats.drop(columns=['TEAM_ABBREVIATION'])

    # Display the boxscore for each team
    st.subheader("תיבת תוצאות עבור פורטלנד טרייל בלייזרס")
    st.dataframe(por_stats)

    st.subheader(f"תיבת תוצאות עבור {other_team_name}")
    st.dataframe(other_team_stats)

    if st.button("סגור את תיבת התוצאות"):
        st.experimental_rerun()

# Display the guessers' points for this game
st.subheader("תוצאות האבדי-מנחשים של המשחק האחרון")

# Fetch points data from Google Sheets
points_df = read_sheet("points")
# Get the last game date
last_game_date_str = pd.to_datetime(last_game_stats['GAME_DATE']).strftime("%b %d, %Y").upper()
# Filter points for the last game
last_game_points = points_df[points_df['game_date'] == last_game_date_str]
# Display points for each guesser for the last game
if not last_game_points.empty:
    # Create a DataFrame with formatted columns
    display_df = last_game_points[['name', 'points']].copy()
    display_df.columns = ['Name', 'Points Scored']
    
    # Sort by points in descending order
    display_df = display_df.sort_values('Points Scored', ascending=False)
    
    # Add icons based on rank
    def add_rank_icon(rank):
        if rank == 0:
            return '🏆'  # Gold trophy
        elif rank == 1:
            return '🥈'  # Silver medal
        elif rank == 2:
            return '🥉'  # Bronze medal
        else:
            return '💩'  # Poop emoji
            
    display_df['Rank'] = [add_rank_icon(i) for i in range(len(display_df))]
    
    # Reorder columns to show rank first
    display_df = display_df[['Rank', 'Name', 'Points Scored']]
    
    # Add styling
    st.markdown("""
        <style>
        .dataframe {
            font-size: 16px !important;
            text-align: left !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Display as a styled table
    st.dataframe(
        display_df,
        hide_index=True,
        use_container_width=True
    )
else:
    st.info("No points data available for the last game.")

# Format the search keywords for the highlights video
search_keywords = f"Deni Avdija {last_game_date}"

# Search for the highlights video on YouTube
search = Search(search_keywords)
video = search.results[0] if search.results else None

if video:
    video_url = video.watch_url
    video_thumbnail = video.thumbnail_url
    st.markdown(f"""
        <h4 style="text-align:center; color:#FF6347;">צפה בהיילייטס של דני אבדיה מהמשחק ב-{last_game_date}</h4>
        <a href="{video_url}" target="_blank">
            <img src="{video_thumbnail}" alt="צפה בהיילייטס של דני אבדיה מהמשחק ב-{last_game_date}" style="width:70%; border-radius:10px;">
        </a>
    """, unsafe_allow_html=True)
else:
    st.markdown("Highlights not available yet.")

# Calculate and display the average rating
reactions_df = read_sheet("reactions")
ratings = reactions_df[reactions_df['game_date'] == game_date_str]['rating'].dropna().tolist()
if ratings:
    average_rating = sum(ratings) / len(ratings)
    st.markdown(f"**Average Rating:** {'🌟' * int(average_rating)} {average_rating:.2f} stars")
else:
    st.markdown("No reactions yet.")

# Add a reaction to the last game stats with stars, option to comment, and identify by name
st.subheader("תן אבדי-תגובה למשחקו האחרון של דני")
with st.expander("תן אבדי-תגובה למשחקו האחרון של דני", expanded=False):
    # Load existing names from Google Sheets
    names_df = read_sheet("names")
    names = names_df['name'].tolist()

    # Dropdown to select a name from the list
    selected_name = st.selectbox("Select your name", options=names, key="selectbox_name")

    # Option to add a new name
    new_name = st.text_input("Or add a new name", key="new_name_input")
    if new_name:
        selected_name = new_name

    name = selected_name

    st.markdown("דרג באמצעות האבדי-כוכבים את משחקו האחרון של דני")
    reaction = st.slider("Rate the game", 1, 5, 3)
    comment = st.text_area("השאר אבדי-תגובה על ביצועיו המרהיבים או לא של דני (אבדיה)")

    if st.button("Submit Reaction"):
        if not name:
            st.error("Please enter your name.")
        else:
            # Check if the user has already submitted a reaction for this game
            if not reactions_df[(reactions_df['game_date'] == game_date_str) & (reactions_df['name'] == name)].empty:
                st.error("You have already submitted a reaction for this game.")
            else:
                if reaction == 5:
                    st.write("🌟🌟🌟🌟🌟 המשחק היה אבדי-מושלם!!")
                elif reaction == 4:
                    st.write("🌟🌟🌟🌟 משחק טובדי-מאוד")
                elif reaction == 3:
                    st.write("🌟🌟🌟 הפעם הוא היה אבדי-ממוצע")
                elif reaction == 2:
                    st.write("🌟🌟 משחק מתחת לאבדי-ממוצע")
                else:
                    st.write("🌟 משחק אבדון")
                
                if comment:
                    st.write("**האבדי-תגובה שלך:**", comment)
                
                # Save the reaction and comment with the game date
                new_reaction = pd.DataFrame({
                    "game_date": [game_date_str], 
                    "name": [name],
                    "rating": [reaction], 
                    "comment": [comment]
                })
                reactions_df =  new_reaction
                if new_name:
                    if new_name not in names:
                        new_name_df = pd.DataFrame({"name": [new_name]})
                        names_df = new_name_df
                        write_sheet("names", names_df)
                write_sheet("reactions", reactions_df)
                st.success("האבדי-תגובה שלך למשחק נשמרה!")


# Display the last 5 reactions in a compact way
st.subheader("חמשת האבדי-תגובות האחרונות")
last_reactions = reactions_df[reactions_df['game_date'] == game_date_str].tail(5)
for _, reaction in last_reactions.iterrows():
    name = reaction['name']
    rating = reaction['rating']
    comment = reaction['comment'] 
    if name or rating or comment:  # Only display if there is content
        stars = '🌟' * int(rating)
        st.markdown(f"**{name}**: {stars} - {comment}")
        st.markdown("<hr style='border: 1px solid #ddd;'>", unsafe_allow_html=True)

# Get Deni's next game details
next_games = PlayerNextNGames(player_id=player_id, number_of_games=1)
next_game_df = next_games.get_data_frames()[0]

# Extract the next game details
next_game_details = next_game_df.iloc[0]
next_game_date = next_game_details['GAME_DATE']
next_game_opponent = next_game_details.get('MATCHUP') 
next_game_time = next_game_details['GAME_TIME']

# Display the next game details in a more visually appealing way
# Extract and display the next game details in a humorous Hebrew way
next_game_details = next_game_df.iloc[0]
next_game_date = pd.to_datetime(next_game_details['GAME_DATE'] + ' ' + next_game_details['GAME_TIME'])+ timedelta(hours=7)
home_team_name = next_game_details.get('HOME_TEAM_NAME')
next_game_time = (pd.to_datetime(next_game_details['GAME_DATE'] + ' ' + next_game_details['GAME_TIME']) + timedelta(hours=7)).strftime('%H:%M')
home_team_name = next_game_details['HOME_TEAM_NAME']
visitor_team_name = next_game_details['VISITOR_TEAM_NAME']
home_team_abbr = next_game_details['HOME_TEAM_ABBREVIATION']
visitor_team_abbr = next_game_details['VISITOR_TEAM_ABBREVIATION']
home_team_nickname = next_game_details['HOME_TEAM_NICKNAME']
visitor_team_nickname = next_game_details['VISITOR_TEAM_NICKNAME']
home_wl = next_game_details['HOME_WL']
visitor_wl = next_game_details['VISITOR_WL']

# Calculate the time remaining until the next game in Israel's GMT+2 timezone
try:
    next_game_datetime = pd.to_datetime(f"{next_game_date} {next_game_time}")
    next_game_datetime = next_game_datetime + timedelta(hours=7)  # Convert to Israel's GMT+2 timezone
    time_remaining = next_game_datetime - datetime.now()

    # Format the time remaining
    days, seconds = time_remaining.days, time_remaining.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    st.markdown(f"""
        <div style="background-color: #f9f9f9; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);">
            <h3 style="text-align:center; color:#FF6347;">פרטי המשחק הבא של דני</h3>
            <p><strong>תאריך:</strong> {next_game_date.date()}</p>
            <p><strong>שעה:</strong> {next_game_time}</p>
            <p><strong>קבוצה מארחת:</strong> {home_team_name} ({home_team_abbr})</p>
            <p><strong>קבוצה אורחת:</strong> {visitor_team_name} ({visitor_team_abbr})</p>
            <p><strong>מאזן קבוצה מארחת:</strong> {home_wl}</p>
            <p><strong>מאזן קבוצה אורחת:</strong> {visitor_wl}</p>
            <p><strong>זמן נותר עד המשחק:</strong> {days} ימים, {hours} שעות, {minutes} דקות, {seconds} שניות</p>
        </div>
    """, unsafe_allow_html=True)
except ValueError as e:
    st.error(f"Error parsing date and time: {e}")


next_game_date = next_game_details['GAME_DATE']

# Predict next game performance based on stats and opponent team
st.subheader("אבדי-חיזוי של ביצועיו של דני במשחק האבדי-בא")

# Get the opponent team ID
opponent_team_name = next_game_details['VISITOR_TEAM_NAME'] if next_game_details['HOME_TEAM_NAME'] == 'Portland (POR)' else next_game_details['HOME_TEAM_NAME']
st.write(f"Opponent Team: {opponent_team_name}")

# Handle special team name cases
team_name_mapping = {
    'L.A. Lakers': 'Los Angeles Lakers',
    'L.A. Clippers': 'Los Angeles Clippers',
    'LA Lakers': 'Los Angeles Lakers',
    'LA Clippers': 'Los Angeles Clippers'
}
search_team_name = team_name_mapping.get(opponent_team_name, opponent_team_name)
opponent_team = teams.find_teams_by_full_name(search_team_name)[0]
opponent_team_id = opponent_team['id']

# Get the opponent team's defensive stats for the current season
opponent_gamelog = teamgamelog.TeamGameLog(team_id=opponent_team_id, season=current_season)
opponent_stats = opponent_gamelog.get_data_frames()[0]

# Calculate the opponent's average defensive stats
opponent_avg_defensive_stats = opponent_stats[['PTS', 'REB', 'AST', 'STL', 'BLK', 'FG_PCT', 'FG3_PCT']].mean()
# Prepare the data for regression
features = ['PTS', 'REB', 'AST', 'STL', 'BLK', 'FG_PCT', 'FG3_PCT']
X = np.concatenate((current_season_stats[features].values[:-1], opponent_avg_defensive_stats.values.reshape(1, -1).repeat(len(current_season_stats) - 1, axis=0)), axis=1)
y = current_season_stats[features].values[1:]

# Combine features for prediction
combined_features = np.concatenate((X, opponent_avg_defensive_stats.values.reshape(1, -1).repeat(X.shape[0], axis=0)), axis=1)

# Train the linear regression model
model = LinearRegression()
model.fit(X, y)

# Prepare the data for prediction
last_game_features = current_season_stats[features].values[-1].reshape(1, -1)
opponent_features = opponent_avg_defensive_stats.values.reshape(1, -1)
combined_features = np.concatenate((last_game_features, opponent_features), axis=1)

# Predict the next game's performance
predicted_stats = model.predict(combined_features)[0]

# Round the predicted stats to the nearest integer where appropriate
predicted_points = round(predicted_stats[0])
predicted_rebounds = round(predicted_stats[1])
predicted_assists = round(predicted_stats[2])
predicted_steals = round(predicted_stats[3])
predicted_blocks = round(predicted_stats[4])
predicted_fg_pct = round(predicted_stats[5] * 100, 1)
predicted_fg3_pct = round(predicted_stats[6] * 100, 1)

# Create a DataFrame for the predicted stats
predicted_stats_df = pd.DataFrame({
    'Points': [predicted_points],
    'Rebounds': [predicted_rebounds],
    'Assists': [predicted_assists],
    'Steals': [predicted_steals],
    'Blocks': [predicted_blocks],
    'Field Goal %': [predicted_fg_pct],
    'Three-Point %': [predicted_fg3_pct]
})

# Display the predicted stats in a table
st.dataframe(predicted_stats_df)

# Add a section for users to guess Deni's next game stats
st.subheader("נחש את ביצועיו של דני במשחק האבדי-בא")

# Read guesses data from Google Sheets
guesses_df = read_sheet("guesses")

# Ask if the user wants to guess the next game stats
with st.expander("נחש את ביצועיו של דני במשחק האבדי-בא", expanded=False):
    # Input fields for user guesses
    guessed_points = st.number_input("Guess Points", min_value=0, max_value=100, value=predicted_points)
    guessed_rebounds = st.number_input("Guess Rebounds", min_value=0, max_value=50, value=predicted_rebounds)
    guessed_assists = st.number_input("Guess Assists", min_value=0, max_value=50, value=predicted_assists)
    guessed_steals = st.number_input("Guess Steals", min_value=0, max_value=20, value=predicted_steals)
    guessed_blocks = st.number_input("Guess Blocks", min_value=0, max_value=20, value=predicted_blocks)
    guessed_fgm = st.number_input("Guess Field Goals Made", min_value=0, max_value=50, value=round(predicted_fg_pct / 100 * predicted_points))
    guessed_fga = st.number_input("Guess Field Goals Attempted", min_value=0, max_value=50, value=round(predicted_fg_pct / 100 * predicted_points * 1.5))
    guessed_fg3m = st.number_input("Guess Three-Point Field Goals Made", min_value=0, max_value=50, value=round(predicted_fg3_pct / 100 * predicted_points))
    guessed_fg3a = st.number_input("Guess Three-Point Field Goals Attempted", min_value=0, max_value=50, value=round(predicted_fg3_pct / 100 * predicted_points * 1.5))

    # Dropdown to select a name from the list
    selected_name = st.selectbox("Select your name", options=names)

    # Option to add a new name
    new_name = st.text_input("Or add a new name")

    if new_name:
        selected_name = new_name

    name = selected_name

    if st.button("Submit Guess"):
        if not name:
            st.error("Please enter your name.")
        else:
            # Check if the user has already submitted a guess for the next game
            if not guesses_df[(guesses_df['game_date'] == next_game_date) & (guesses_df['name'] == name)].empty:
                st.error("You have already submitted a guess for this game.")
            else:
                st.write("Your guess has been submitted!")
                st.markdown(f"**Guessed Points:** {guessed_points}")
                st.markdown(f"**Guessed Rebounds:** {guessed_rebounds}")
                st.markdown(f"**Guessed Assists:** {guessed_assists}")
                st.markdown(f"**Guessed Steals:** {guessed_steals}")
                st.markdown(f"**Guessed Blocks:** {guessed_blocks}")
                st.markdown(f"**Guessed Field Goals Made:** {guessed_fgm}")
                st.markdown(f"**Guessed Field Goals Attempted:** {guessed_fga}")
                st.markdown(f"**Guessed Three-Point Field Goals Made:** {guessed_fg3m}")
                st.markdown(f"**Guessed Three-Point Field Goals Attempted:** {guessed_fg3a}")
                
                # Save the guess with the name of the guesser and the date of the next game
                new_guess = pd.DataFrame({
                    "game_date": [next_game_date],
                    "name": [name],
                    "points": [guessed_points],
                    "rebounds": [guessed_rebounds],
                    "assists": [guessed_assists],
                    "steals": [guessed_steals],
                    "blocks": [guessed_blocks],
                    "fgm": [guessed_fgm],
                    "fga": [guessed_fga],
                    "fg3m": [guessed_fg3m],
                    "fg3a": [guessed_fg3a]
                })
                guesses_df = new_guess
                if new_name:
                    if new_name not in names:
                        new_name_df = pd.DataFrame({"name": [new_name]})
                        names_df = new_name_df
                        write_sheet("names", names_df)
                write_sheet("guesses", guesses_df)
                st.success("Your guess has been saved!")

# Update the display of guesses to show shooting stats
st.subheader("חמשת האבדי-ניחושים האחרונים")
last_guesses = guesses_df[guesses_df['game_date'] == next_game_date].tail(5)
st.write(f"Total number of guesses: {len(last_guesses)}")
for _, guess in last_guesses.iterrows():
    st.write(
        f"**{guess['name']}**: "
        f"PTS: {guess['points']}, "
        f"REB: {guess['rebounds']}, "
        f"AST: {guess['assists']}, "
        f"STL: {guess['steals']}, "
        f"BLK: {guess['blocks']}, "
        f"FG: {guess['fgm']}/{guess['fga']}, "
        f"3P: {guess['fg3m']}/{guess['fg3a']}"
    )
    st.markdown("---")

# Aggregate total points for each guesser from current points_df
current_points = points_df.groupby('name')['points'].sum().reset_index()
current_points.columns = ['name', 'total_points']
try:
    # Read existing total points
    existing_points = read_sheet("total_points")
    
    # Get most recent game date from gamelog_stats
    last_played_game_date = pd.to_datetime(gamelog_stats['GAME_DATE'].iloc[0]).strftime("%Y-%m-%d")
    
    # Check if we need to update points based on last_game_date_updated
    needs_update = True
    if not existing_points.empty and 'last_game_date_updated' in existing_points.columns:
        last_updated = existing_points['last_game_date_updated'].iloc[0]
        if last_updated == last_played_game_date:
            needs_update = False
    
    if needs_update:
        if not existing_points.empty:
            # Create a set of all unique names
            all_names = set(current_points['name']).union(set(existing_points['name']))
            
            # Initialize the final DataFrame with all names
            total_points_df = pd.DataFrame({'name': list(all_names)})
            
            # Merge with current points
            total_points_df = total_points_df.merge(current_points, on='name', how='left')
            # Merge with existing points
            total_points_df = total_points_df.merge(existing_points, on='name', how='left', suffixes=('', '_old'))
            
            # Sum the points, treating NaN as 0
            total_points_df['total_points'] = total_points_df['total_points'].fillna(0) + \
                                            total_points_df['total_points_old'].fillna(0)
            
            # Add last_game_date_updated
            total_points_df['last_game_date_updated'] = last_played_game_date
            
            # Keep only required columns
            total_points_df = total_points_df[['name', 'total_points', 'last_game_date_updated']]
        else:
            total_points_df = current_points.copy()
            total_points_df['last_game_date_updated'] = last_played_game_date
        
        # Create a new connection instance and update Google Sheets
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(worksheet="total_points", data=total_points_df)
    else:
        total_points_df = existing_points

except Exception as e:
    st.warning(f"Could not read or update total points: {str(e)}")
    # Create basic DataFrame if error occurs
    total_points_df = current_points.copy()
    total_points_df['last_game_date_updated'] = last_played_game_date

# Display the total points for each guesser
st.subheader("אבדי-נקודות סופיות לכל מנחש")

# Sort total points in descending order
total_points_df = total_points_df.sort_values('total_points', ascending=False)

# Add rank icons and create display DataFrame 
display_df = total_points_df.copy()
display_df.columns = ['Name', 'Total Points', 'Last Updated']

# Add rank icons based on position
def add_rank_icon(rank):
    if rank == 0:
        return '👑'  # Crown for 1st
    elif rank == 1:
        return '🥈'  # Silver medal
    elif rank == 2:
        return '🥉'  # Bronze medal
    else:
        return '💩'  # Poop emoji for others

display_df['Rank'] = [add_rank_icon(i) for i in range(len(display_df))]

# Reorder columns
display_df = display_df[['Rank', 'Name', 'Total Points']]

# Add styling
st.markdown("""
    <style>
    .dataframe {
        font-size: 16px !important;
        text-align: left !important;
    }
    </style>
""", unsafe_allow_html=True)

# Display as a styled table
st.dataframe(
    display_df,
    hide_index=True,
    use_container_width=True
)

# Summarize stats
st.write("אבדי-סיכום סטטיסטיקות קריירה")
summary_stats = career_stats[['SEASON_ID', 'GP', 'PTS', 'REB', 'AST', 'STL', 'BLK']]
st.dataframe(summary_stats)

# Get game logs for the current season
current_season = '2024-25'  # Update this to the current season
gamelog = playergamelog.PlayerGameLog(player_id=player_id, season=current_season)
gamelog_stats = gamelog.get_data_frames()[0]

# Display the game log for the current season
st.subheader("אבדי-יומן משחקים לעונה הנוכחית")
st.dataframe(gamelog_stats)

# Summarize current season stats
current_season_stats = gamelog_stats[['GAME_DATE', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'FG_PCT', 'FG3_PCT']]
current_season_stats['GAME_DATE'] = pd.to_datetime(current_season_stats['GAME_DATE'])

# Calculate cumulative points after each game
current_season_stats = current_season_stats.sort_values(by='GAME_DATE')
current_season_stats['Cumulative_Points'] = current_season_stats['PTS'].cumsum()
# Calculate points per game (PPG) after each game
current_season_stats['Game_Number'] = range(1, len(current_season_stats) + 1)
current_season_stats['PPG'] = current_season_stats['Cumulative_Points'] / current_season_stats['Game_Number']

# Calculate cumulative rebounds after each game
current_season_stats['Cumulative_Rebounds'] = current_season_stats['REB'].cumsum()
# Calculate rebounds per game (RPG) after each game
current_season_stats['RPG'] = current_season_stats['Cumulative_Rebounds'] / current_season_stats['Game_Number']

# Calculate cumulative assists after each game
current_season_stats['Cumulative_Assists'] = current_season_stats['AST'].cumsum()
# Calculate assists per game (APG) after each game
current_season_stats['APG'] = current_season_stats['Cumulative_Assists'] / current_season_stats['Game_Number']

# Calculate cumulative FG% after each game
current_season_stats['Cumulative_FG_PCT'] = current_season_stats['FG_PCT'].expanding().mean()
# Calculate cumulative 3P% after each game
current_season_stats['Cumulative_FG3_PCT'] = current_season_stats['FG3_PCT'].expanding().mean()

# Plot PPG, RPG, APG progress over the season
st.write("אבדי-התפתחות PPG, RPG, APG לאורך העונה")
fig = go.Figure()
fig.add_trace(go.Scatter(x=current_season_stats['GAME_DATE'], y=current_season_stats['PPG'], mode='lines+markers', name='PPG Progress', line=dict(color='green')))
fig.add_trace(go.Scatter(x=current_season_stats['GAME_DATE'], y=current_season_stats['RPG'], mode='lines+markers', name='RPG Progress', line=dict(color='blue')))
fig.add_trace(go.Scatter(x=current_season_stats['GAME_DATE'], y=current_season_stats['APG'], mode='lines+markers', name='APG Progress', line=dict(color='red')))
fig.update_layout(title='PPG, RPG, APG Progress Over the Season', xaxis_title='Game Date', yaxis_title='Per Game Stats')
st.plotly_chart(fig)

# Plot FG% and 3P% progress over the season
st.write("אבדי-התפתחות FG% ו-3P% לאורך העונה")
fig = go.Figure()
fig.add_trace(go.Scatter(x=current_season_stats['GAME_DATE'], y=current_season_stats['Cumulative_FG_PCT'], mode='lines+markers', name='FG% Progress', line=dict(color='magenta')))
fig.add_trace(go.Scatter(x=current_season_stats['GAME_DATE'], y=current_season_stats['Cumulative_FG3_PCT'], mode='lines+markers', name='3P% Progress', line=dict(color='cyan')))
fig.update_layout(title='FG% and 3P% Progress Over the Season', xaxis_title='Game Date', yaxis_title='Percentage')
st.plotly_chart(fig)

# Calculate points from FT, 2FG, and 3FG
current_season_stats['FT_PTS'] = gamelog_stats['FTM'] * 1
current_season_stats['2FG_PTS'] = (gamelog_stats['FGM'] - gamelog_stats['FG3M']) * 2
current_season_stats['3FG_PTS'] = gamelog_stats['FG3M'] * 3

# Calculate cumulative FT points after each game
current_season_stats['Cumulative_FT_PTS'] = current_season_stats['FT_PTS'].cumsum()
# Calculate FT points per game (FT_PPG) after each game
current_season_stats['FT_PPG'] = current_season_stats['Cumulative_FT_PTS'] / current_season_stats['Game_Number']

# Calculate cumulative 2FG points after each game
current_season_stats['Cumulative_2FG_PTS'] = current_season_stats['2FG_PTS'].cumsum()
# Calculate 2FG points per game (2FG_PPG) after each game
current_season_stats['2FG_PPG'] = current_season_stats['Cumulative_2FG_PTS'] / current_season_stats['Game_Number']

# Calculate cumulative 3FG points after each game
current_season_stats['Cumulative_3FG_PTS'] = current_season_stats['3FG_PTS'].cumsum()
# Calculate 3FG points per game (3FG_PPG) after each game
current_season_stats['3FG_PPG'] = current_season_stats['Cumulative_3FG_PTS'] / current_season_stats['Game_Number']

# Plot points distribution
st.write("אבדי-התפלגות נקודות מ-2FG, 3FG, ו-FT לאורך העונה")
fig = go.Figure()
fig.add_trace(go.Scatter(x=current_season_stats['GAME_DATE'], y=current_season_stats['2FG_PPG'], mode='lines+markers', name='Points from 2FG Per Game', line=dict(color='green')))
fig.add_trace(go.Scatter(x=current_season_stats['GAME_DATE'], y=current_season_stats['3FG_PPG'], mode='lines+markers', name='Points from 3FG Per Game', line=dict(color='red')))
fig.add_trace(go.Scatter(x=current_season_stats['GAME_DATE'], y=current_season_stats['FT_PPG'], mode='lines+markers', name='Points from FT Per Game', line=dict(color='blue')))
fig.update_layout(title='Points Distribution from 2FG, 3FG, and FT Over the Season', xaxis_title='Game Date', yaxis_title='Points Per Game')
st.plotly_chart(fig)

# Calculate cumulative steals after each game
current_season_stats['Cumulative_Steals'] = current_season_stats['STL'].cumsum()
# Calculate steals per game (SPG) after each game
current_season_stats['SPG'] = current_season_stats['Cumulative_Steals'] / current_season_stats['Game_Number']

# Calculate cumulative blocks after each game
current_season_stats['Cumulative_Blocks'] = current_season_stats['BLK'].cumsum()
# Calculate blocks per game (BPG) after each game
current_season_stats['BPG'] = current_season_stats['Cumulative_Blocks'] / current_season_stats['Game_Number']

# Plot SPG and BPG progress over the season
st.write("אבדי-התפתחות SPG ו-BPG לאורך העונה")
fig = go.Figure()
fig.add_trace(go.Scatter(x=current_season_stats['GAME_DATE'], y=current_season_stats['SPG'], mode='lines+markers', name='SPG Progress', line=dict(color='orange')))
fig.add_trace(go.Scatter(x=current_season_stats['GAME_DATE'], y=current_season_stats['BPG'], mode='lines+markers', name='BPG Progress', line=dict(color='purple')))
fig.update_layout(title='SPG and BPG Progress Over the Season', xaxis_title='Game Date', yaxis_title='Per Game Stats')
st.plotly_chart(fig)

# Add a section for users to choose the window size for the rolling average
st.subheader("בחר את גודל החלון לממוצע נע")
window_size = st.slider("Window Size", min_value=1, max_value=20, value=5)

# Calculate rolling average for PPG, RPG, APG with the selected window size
current_season_stats['Rolling_PPG'] = current_season_stats['PTS'].rolling(window=window_size).mean()
current_season_stats['Rolling_RPG'] = current_season_stats['REB'].rolling(window=window_size).mean()
current_season_stats['Rolling_APG'] = current_season_stats['AST'].rolling(window=window_size).mean()

# Plot rolling average PPG, RPG, APG progress over the season
st.write(f"אבדי-ממוצע נע PPG, RPG, APG לאורך העונה ({window_size} משחקים)")
fig = go.Figure()
fig.add_trace(go.Scatter(x=current_season_stats['GAME_DATE'], y=current_season_stats['Rolling_PPG'], mode='lines+markers', name='Rolling PPG', line=dict(color='green')))
fig.add_trace(go.Scatter(x=current_season_stats['GAME_DATE'], y=current_season_stats['Rolling_RPG'], mode='lines+markers', name='Rolling RPG', line=dict(color='blue')))
fig.add_trace(go.Scatter(x=current_season_stats['GAME_DATE'], y=current_season_stats['Rolling_APG'], mode='lines+markers', name='Rolling APG', line=dict(color='red')))
fig.update_layout(title=f'Rolling Average PPG, RPG, APG Progress Over the Season ({window_size} Games)', xaxis_title='Game Date', yaxis_title='Per Game Stats')
st.plotly_chart(fig)

# Calculate rolling average FG% and 3P% with the selected window size
current_season_stats['Rolling_FG_PCT'] = current_season_stats['FG_PCT'].rolling(window=window_size).mean()
current_season_stats['Rolling_FG3_PCT'] = current_season_stats['FG3_PCT'].rolling(window=window_size).mean()

# Plot rolling average FG% and 3P% progress over the season
st.write(f"אבדי-ממוצע נע FG% ו-3P% לאורך העונה ({window_size} משחקים)")
fig = go.Figure()
fig.add_trace(go.Scatter(x=current_season_stats['GAME_DATE'], y=current_season_stats['Rolling_FG_PCT'], mode='lines+markers', name='Rolling FG%', line=dict(color='magenta')))
fig.add_trace(go.Scatter(x=current_season_stats['GAME_DATE'], y=current_season_stats['Rolling_FG3_PCT'], mode='lines+markers', name='Rolling 3P%', line=dict(color='cyan')))
fig.update_layout(title=f'Rolling Average FG% and 3P% Progress Over the Season ({window_size} Games)', xaxis_title='Game Date', yaxis_title='Percentage')
st.plotly_chart(fig)

# Calculate rolling average SPG and BPG with the selected window size
current_season_stats['Rolling_SPG'] = current_season_stats['STL'].rolling(window=window_size).mean()
current_season_stats['Rolling_BPG'] = current_season_stats['BLK'].rolling(window=window_size).mean()

# Plot rolling average SPG and BPG progress over the season
st.write(f"אבדי-ממוצע נע SPG ו-BPG לאורך העונה ({window_size} משחקים)")
fig = go.Figure()
fig.add_trace(go.Scatter(x=current_season_stats['GAME_DATE'], y=current_season_stats['Rolling_SPG'], mode='lines+markers', name='Rolling SPG', line=dict(color='orange')))
fig.add_trace(go.Scatter(x=current_season_stats['GAME_DATE'], y=current_season_stats['Rolling_BPG'], mode='lines+markers', name='Rolling BPG', line=dict(color='purple')))
fig.update_layout(title=f'Rolling Average SPG and BPG Progress Over the Season ({window_size} Games)', xaxis_title='Game Date', yaxis_title='Per Game Stats')
st.plotly_chart(fig)
