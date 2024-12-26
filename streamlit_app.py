import streamlit as st
# Set the page configuration

from nba_api.stats.endpoints import playercareerstats, playergamelog, PlayerNextNGames
from nba_api.stats.static import players
import plotly.graph_objects as go
import pandas as pd
from pytube import Search
import json
from datetime import datetime
from sklearn.linear_model import LinearRegression
import numpy as np
import os
import requests
from nba_api.stats.endpoints import teamgamelog
from nba_api.stats.static import teams
import sqlite3

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
    body {
        background-color: #f0f2f6;
        color: #333;
        font-family: 'Arial', sans-serif;
        background-image: url('https://wallpaperaccess.com/full/1122017.jpg');
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
        background-position: center;
    }
    .stApp {
        background-color: rgba(240, 242, 246, 0.9);
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        transition: background-color 0.5s ease;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 12px;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .stDataFrame {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 10px;
        background-color: white;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    .stMarkdown {
        font-family: 'Arial', sans-serif;
    }
    .stApp::before {
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 50px;
        height: 100%;
        background: linear-gradient(to bottom, red, black);
        z-index: -1;
        transition: background 0.01s ease;
    }
    .stApp::after {
        content: "";
        position: fixed;
        top: 0;
        right: 0;
        width: 50px;
        height: 100%;
        background: linear-gradient(to bottom, red, black);
        z-index: -1;
        transition: background 0.1s ease;
    }
    .stTitle {
        color: red;
    }
    .stSubheader {
        color: red;
    }
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

# Define the path for the SQLite database file
db_path = os.path.join(os.getcwd(), 'deni_avdija_stats.db')

# Check if the database file already exists
db_exists = os.path.exists(db_path)

# Initialize SQLite database
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Create tables if they don't exist
if not db_exists:
    c.execute('''
    CREATE TABLE IF NOT EXISTS reactions (
        id INTEGER PRIMARY KEY,
        game_date TEXT,
        name TEXT,
        rating INTEGER,
        comment TEXT
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS guesses (
        id INTEGER PRIMARY KEY,
        game_date TEXT,
        name TEXT,
        points INTEGER,
        rebounds INTEGER,
        assists INTEGER,
        steals INTEGER,
        blocks INTEGER,
        fg_pct REAL,
        fg3_pct REAL
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS names (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS points (
        game_date TEXT,
        name TEXT,
        points INTEGER,
        PRIMARY KEY (game_date, name)
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS total_points (
        name TEXT PRIMARY KEY,
        total_points INTEGER
    )
    ''')
    conn.commit()

# Create a new reaction for each new game
game_date_str = last_game_date.replace(" ", "_")
c.execute("SELECT COUNT(*) FROM reactions WHERE game_date = ?", (game_date_str,))
if c.fetchone()[0] == 0:
    c.execute("INSERT INTO reactions (game_date) VALUES (?)", (game_date_str,))
    conn.commit()

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

# Display the guessers' points for this game
st.subheader("תוצאות האבדי-מנחשים של המשחק האחרון")

# Check if points have already been calculated and stored
points_filename = "points.json"
if os.path.exists(points_filename):
    with open(points_filename, "r", encoding="utf-8") as f:
        points_data = json.load(f)
else:
    points_data = {}

# Get the last game date
last_game_date_str = pd.to_datetime(last_game_stats['GAME_DATE']).strftime("%Y-%m-%d")

# Display points for each guesser for the last game
if last_game_date_str in points_data:
    for name, points in points_data[last_game_date_str].items():
        st.write(f"Name: {name}, Points Scored: {points}")
else:
    st.write("No points data available for the last game.")

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
c.execute("SELECT rating FROM reactions WHERE game_date = ?", (game_date_str,))
reactions = c.fetchall()
ratings = [r[0] for r in reactions if r[0] is not None]
filtered_ratings = [rating for rating in ratings if rating is not None]
if filtered_ratings:
    average_rating = sum(filtered_ratings) / len(filtered_ratings)
    st.markdown(f"**Average Rating:** {'🌟' * int(average_rating)} {average_rating:.2f} stars")
else:
    st.markdown("No reactions yet.")

# Display the last 5 reactions in a compact way
st.subheader("חמשת האבדי-תגובות האחרונות")
c.execute("SELECT name, rating, comment FROM reactions WHERE game_date = ? ORDER BY id DESC LIMIT 5", (game_date_str,))
reactions = c.fetchall()
for reaction in reactions:
    rating = reaction[1] if reaction[1] is not None else 0
    stars = '🌟' * rating
    st.markdown(f"**{reaction[0]}**: {stars} ({rating} stars) - {reaction[2]}")
    st.markdown("<hr style='border: 1px solid #ddd;'>", unsafe_allow_html=True)

# Add a reaction to the last game stats with stars, option to comment, and identify by name
st.subheader("תן אבדי-תגובה למשחקו האחרון של דני")
with st.expander("תן אבדי-תגובה למשחקו האחרון של דני", expanded=False):
    # Load existing names from the database
    c.execute("SELECT name FROM names")
    names = [row[0] for row in c.fetchall()]

    # Dropdown to select a name from the list
    selected_name = st.selectbox("Select your name", options=names, key="selectbox_name")

    # Option to add a new name
    new_name = st.text_input("Or add a new name", key="new_name_input")

    if new_name:
        if new_name not in names:
            names.append(new_name)
            c.execute("INSERT INTO names (name) VALUES (?)", (new_name,))
            conn.commit()
        selected_name = new_name

    name = selected_name

    st.markdown("דרג באמצעות האבדי-כוכבים את משחקו האחרון של דני")
    reaction = st.slider("Rate the game", 1, 5, 3)
    comment = st.text_area("השאר אבדי-תגובה על ביצועיו המרהיבים או לא של דני (אבדיה)")

    if st.button("Submit Reaction"):
        if not name:
            st.error("Please enter your name.")
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
            c.execute("INSERT INTO reactions (game_date, name, rating, comment) VALUES (?, ?, ?, ?)", (game_date_str, name, reaction, comment))
            conn.commit()
            
            st.success("האבדי-תגובה שלך למשחק נשמרה!")


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
next_game_date = next_game_details['GAME_DATE']
next_game_time = next_game_details['GAME_TIME']
home_team_name = next_game_details['HOME_TEAM_NAME']
visitor_team_name = next_game_details['VISITOR_TEAM_NAME']
home_team_abbr = next_game_details['HOME_TEAM_ABBREVIATION']
visitor_team_abbr = next_game_details['VISITOR_TEAM_ABBREVIATION']
home_team_nickname = next_game_details['HOME_TEAM_NICKNAME']
visitor_team_nickname = next_game_details['VISITOR_TEAM_NICKNAME']
home_wl = next_game_details['HOME_WL']
visitor_wl = next_game_details['VISITOR_WL']

st.markdown(f"""
    <div style="background-color: #f9f9f9; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);">
        <h3 style="text-align:center; color:#FF6347;">פרטי המשחק הבא של דני</h3>
        <p><strong>תאריך:</strong> {next_game_date}</p>
        <p><strong>שעה:</strong> {next_game_time}</p>
        <p><strong>קבוצה מארחת:</strong> {home_team_name} ({home_team_abbr})</p>
        <p><strong>קבוצה אורחת:</strong> {visitor_team_name} ({visitor_team_abbr})</p>
        <p><strong>מאזן קבוצה מארחת:</strong> {home_wl}</p>
        <p><strong>מאזן קבוצה אורחת:</strong> {visitor_wl}</p>
    </div>
""", unsafe_allow_html=True)

# Predict next game performance based on stats and opponent team
st.subheader("אבדי-חיזוי של ביצועיו של דני במשחק האבדי-בא")

# Get the opponent team ID
opponent_team_name = next_game_details['VISITOR_TEAM_NAME'] if next_game_details['HOME_TEAM_NAME'] == 'Washington Wizards' else next_game_details['HOME_TEAM_NAME']
opponent_team = teams.find_teams_by_full_name(opponent_team_name)[0]
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

# Ask if the user wants to guess the next game stats
with st.expander("נחש את ביצועיו של דני במשחק האבדי-בא", expanded=False):
    # Input fields for user guesses
    guessed_points = st.number_input("Guess Points", min_value=0, max_value=100, value=predicted_points)
    guessed_rebounds = st.number_input("Guess Rebounds", min_value=0, max_value=50, value=predicted_rebounds)
    guessed_assists = st.number_input("Guess Assists", min_value=0, max_value=50, value=predicted_assists)
    guessed_steals = st.number_input("Guess Steals", min_value=0, max_value=20, value=predicted_steals)
    guessed_blocks = st.number_input("Guess Blocks", min_value=0, max_value=20, value=predicted_blocks)
    guessed_fg_pct = st.number_input("Guess Field Goal Percentage", min_value=0.0, max_value=100.0, value=predicted_fg_pct)
    guessed_fg3_pct = st.number_input("Guess Three-Point Percentage", min_value=0.0, max_value=100.0, value=predicted_fg3_pct)

    # Dropdown to select a name from the list
    selected_name = st.selectbox("Select your name", options=names)

    # Option to add a new name
    new_name = st.text_input("Or add a new name")

    if new_name:
        if new_name not in names:
            names.append(new_name)
            c.execute("INSERT INTO names (name) VALUES (?)", (new_name,))
            conn.commit()
        selected_name = new_name

    name = selected_name

    if st.button("Submit Guess"):
        if not name:
            st.error("Please enter your name.")
        else:
            st.write("Your guess has been submitted!")
            st.markdown(f"**Guessed Points:** {guessed_points}")
            st.markdown(f"**Guessed Rebounds:** {guessed_rebounds}")
            st.markdown(f"**Guessed Assists:** {guessed_assists}")
            st.markdown(f"**Guessed Steals:** {guessed_steals}")
            st.markdown(f"**Guessed Blocks:** {guessed_blocks}")
            st.markdown(f"**Guessed Field Goal Percentage:** {guessed_fg_pct:.2f}%")
            st.markdown(f"**Guessed Three-Point Percentage:** {guessed_fg3_pct:.2f}%")
            
            # Save the guess with the name of the guesser and the date of the next game
            c.execute("INSERT INTO guesses (game_date, name, points, rebounds, assists, steals, blocks, fg_pct, fg3_pct) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (next_game_date, name, guessed_points, guessed_rebounds, guessed_assists, guessed_steals, guessed_blocks, guessed_fg_pct, guessed_fg3_pct))
            conn.commit()
            
            st.success("Your guess has been saved!")
        
# Display Last 5 Guesses
st.subheader("חמשת האבדי-ניחושים האחרונים")
c.execute("SELECT name, points, rebounds, assists, steals, blocks, fg_pct, fg3_pct FROM guesses WHERE game_date = ? ORDER BY id DESC LIMIT 5", (next_game_date,))
guesses = c.fetchall()
# Print the number of guesses
st.write(f"Total number of guesses: {len(guesses)}")
# Display each guess
for guess in guesses:
    st.write(f"**{guess[0]}**: PTS: {guess[1]}, REB: {guess[2]}, AST: {guess[3]}, STL: {guess[4]}, BLK: {guess[5]}, FG%: {guess[6]:.2f}, 3P%: {guess[7]:.2f}")
    st.markdown("---")

# Function to calculate points based on the accuracy of the guess
def calculate_points(guess, actual):
    points = 0
    points += max(0, 10 - abs(guess["points"] - actual["points"]))
    points += max(0, 10 - abs(guess["rebounds"] - actual["rebounds"]))
    points += max(0, 10 - abs(guess["assists"] - actual["assists"]))
    return points

# Read the actual stats from a file or an API
actual_stats = {
    "points": 20,
    "rebounds": 10,
    "assists": 5
}

# Get the current game date
current_game_date = datetime.now().strftime("%Y-%m-%d")

# Calculate points if not already calculated for the current game
c.execute("SELECT name, points, rebounds, assists FROM guesses WHERE game_date = ?", (current_game_date,))
guesses = c.fetchall()
for guess in guesses:
    name = guess[0]
    guess_dict = {
        "points": guess[1] if guess[1] is not None else 0,
        "rebounds": guess[2] if guess[2] is not None else 0,
        "assists": guess[3] if guess[3] is not None else 0
    }
    points = calculate_points(guess_dict, actual_stats)
    c.execute("INSERT INTO points (game_date, name, points) VALUES (?, ?, ?) ON CONFLICT(game_date, name) DO UPDATE SET points = ?", (current_game_date, name, points, points))
    conn.commit()

# Aggregate total points for each guesser
c.execute("SELECT name, SUM(points) FROM points GROUP BY name")
total_points = c.fetchall()
for name, total in total_points:
    c.execute("INSERT INTO total_points (name, total_points) VALUES (?, ?) ON CONFLICT(name) DO UPDATE SET total_points = ?", (name, total, total))
    conn.commit()

# Display the total points for each guesser
st.subheader("אבדי-נקודות סופיות לכל מנחש")
c.execute("SELECT name, total_points FROM total_points")
total_points = c.fetchall()
for name, total in total_points:
    st.write(f"שם: {name}, סך הכל נקודות: {total}")

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


# Calculate rolling average for PPG, RPG, APG with a window of 5 games
current_season_stats['Rolling_PPG'] = current_season_stats['PTS'].rolling(window=5).mean()
current_season_stats['Rolling_RPG'] = current_season_stats['REB'].rolling(window=5).mean()
current_season_stats['Rolling_APG'] = current_season_stats['AST'].rolling(window=5).mean()

# Plot rolling average PPG, RPG, APG progress over the season
st.write("אבדי-ממוצע נע PPG, RPG, APG לאורך העונה (5 משחקים)")
fig = go.Figure()
fig.add_trace(go.Scatter(x=current_season_stats['GAME_DATE'], y=current_season_stats['Rolling_PPG'], mode='lines+markers', name='Rolling PPG', line=dict(color='green')))
fig.add_trace(go.Scatter(x=current_season_stats['GAME_DATE'], y=current_season_stats['Rolling_RPG'], mode='lines+markers', name='Rolling RPG', line=dict(color='blue')))
fig.add_trace(go.Scatter(x=current_season_stats['GAME_DATE'], y=current_season_stats['Rolling_APG'], mode='lines+markers', name='Rolling APG', line=dict(color='red')))
fig.update_layout(title='Rolling Average PPG, RPG, APG Progress Over the Season (5 Games)', xaxis_title='Game Date', yaxis_title='Per Game Stats')
st.plotly_chart(fig)

# Calculate rolling average FG% and 3P% with a window of 5 games
current_season_stats['Rolling_FG_PCT'] = current_season_stats['FG_PCT'].rolling(window=5).mean()
current_season_stats['Rolling_FG3_PCT'] = current_season_stats['FG3_PCT'].rolling(window=5).mean()

# Plot rolling average FG% and 3P% progress over the season
st.write("אבדי-ממוצע נע FG% ו-3P% לאורך העונה (5 משחקים)")
fig = go.Figure()
fig.add_trace(go.Scatter(x=current_season_stats['GAME_DATE'], y=current_season_stats['Rolling_FG_PCT'], mode='lines+markers', name='Rolling FG%', line=dict(color='magenta')))
fig.add_trace(go.Scatter(x=current_season_stats['GAME_DATE'], y=current_season_stats['Rolling_FG3_PCT'], mode='lines+markers', name='Rolling 3P%', line=dict(color='cyan')))
fig.update_layout(title='Rolling Average FG% and 3P% Progress Over the Season (5 Games)', xaxis_title='Game Date', yaxis_title='Percentage')
st.plotly_chart(fig)

# Calculate rolling average SPG and BPG with a window of 5 games
current_season_stats['Rolling_SPG'] = current_season_stats['STL'].rolling(window=5).mean()
current_season_stats['Rolling_BPG'] = current_season_stats['BLK'].rolling(window=5).mean()

# Plot rolling average SPG and BPG progress over the season
st.write("אבדי-ממוצע נע SPG ו-BPG לאורך העונה (5 משחקים)")
fig = go.Figure()
fig.add_trace(go.Scatter(x=current_season_stats['GAME_DATE'], y=current_season_stats['Rolling_SPG'], mode='lines+markers', name='Rolling SPG', line=dict(color='orange')))
fig.add_trace(go.Scatter(x=current_season_stats['GAME_DATE'], y=current_season_stats['Rolling_BPG'], mode='lines+markers', name='Rolling BPG', line=dict(color='purple')))
fig.update_layout(title='Rolling Average SPG and BPG Progress Over the Season (5 Games)', xaxis_title='Game Date', yaxis_title='Per Game Stats')
st.plotly_chart(fig)

# Close the database connection
conn.close()

