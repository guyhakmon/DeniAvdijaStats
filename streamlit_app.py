import streamlit as st
# Set the page configuration
st.set_page_config(page_title='Deni Avdija Stats Tracker')

from nba_api.stats.endpoints import playercareerstats, playergamelog
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

# Streamlit app title
st.title("Deni Avdija's NBA Stats")
# Add a photo of Deni Avdija
st.image("https://cdn.nba.com/headshots/nba/latest/1040x760/1630166.png", caption="Deni Avdija", use_container_width=True)

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

# Create a new reaction file for each new game
game_date_str = last_game_date.replace(" ", "_")
filename = f"reactions_{game_date_str}.txt"

# Check if the file already exists
if not os.path.exists(filename):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"Reactions for the game on {last_game_date}\n\n")

        # Get the next game details from the Portland Trail Blazers schedule
        schedule_url = "https://data.nba.net/prod/v1/2024/teams/1610612757/schedule.json"
        response = requests.get(schedule_url)
        schedule = response.json()

        # Find the next game
        today = datetime.now().date()
        next_game = None
        for game in schedule['league']['standard']:
            game_date = datetime.strptime(game['startDateEastern'], '%Y%m%d').date()
            if game_date > today:
                next_game = game
                break

        if next_game:
            next_game_date = datetime.strptime(next_game['startDateEastern'], '%Y%m%d').strftime('%B %d, %Y')
            next_game_opponent = next_game['vTeam']['triCode'] if next_game['hTeam']['teamId'] == '1610612757' else next_game['hTeam']['triCode']
            st.subheader("Next Game Details")
            st.markdown(f"**Date:** {next_game_date}")
            st.markdown(f"**Opponent:** {next_game_opponent}")
        else:
            st.subheader("Next Game Details")
            st.markdown("No upcoming games found.")

# Summarize current season stats
current_season_stats = gamelog_stats[['GAME_DATE', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'FG_PCT', 'FG3_PCT']]
current_season_stats['GAME_DATE'] = pd.to_datetime(current_season_stats['GAME_DATE'])

# Prepare the data for regression
features = ['PTS', 'REB', 'AST', 'STL', 'BLK', 'FG_PCT', 'FG3_PCT']
X = current_season_stats[features].values[:-1]  # Use all games except the last one for training
y = current_season_stats[features].values[1:]   # Use all games except the first one for target

# Calculate average stats for the current season
average_stats = current_season_stats.mean(numeric_only=True)[['PTS', 'REB', 'AST', 'STL', 'BLK', 'FG_PCT', 'FG3_PCT']]

# Create a DataFrame for the average stats
average_stats_df = pd.DataFrame(average_stats).transpose()
average_stats_df.columns = ['Points', 'Rebounds', 'Assists', 'Steals', 'Blocks', 'Field Goal %', 'Three-Point %']

# Display the average stats in a table
st.subheader("Average Stats for Current Season")
st.dataframe(average_stats_df)


# Train the linear regression model
model = LinearRegression()
model.fit(X, y)




# Predict next game performance based on stats
st.subheader("Predicted Performance for Next Game")
# Predict the next game's performance
last_game_features = current_season_stats[features].values[-1].reshape(1, -1)
predicted_stats = model.predict(last_game_features)[0]

# Round the predicted stats to the nearest integer where appropriate
predicted_points = round(predicted_stats[0])
predicted_rebounds = round(predicted_stats[1])
predicted_assists = round(predicted_stats[2])
predicted_steals = round(predicted_stats[3])
predicted_blocks = round(predicted_stats[4])
predicted_fg_pct = round(predicted_stats[5] * 100, 1)
predicted_fg3_pct = round(predicted_stats[6] * 100, 1)

# Display predicted stats
st.markdown(f"**Predicted Points:** {predicted_points}")
st.markdown(f"**Predicted Rebounds:** {predicted_rebounds}")
st.markdown(f"**Predicted Assists:** {predicted_assists}")
st.markdown(f"**Predicted Steals:** {predicted_steals}")
st.markdown(f"**Predicted Blocks:** {predicted_blocks}")
st.markdown(f"**Predicted Field Goal Percentage:** {predicted_fg_pct:.2f}%")
st.markdown(f"**Predicted Three-Point Percentage:** {predicted_fg3_pct:.2f}%")

# Add a section for users to guess Deni's next game stats
st.subheader("Guess Deni's Next Game Stats")

# Input fields for user guesses
guessed_points = st.number_input("Guess Points", min_value=0, max_value=100, value=predicted_points)
guessed_rebounds = st.number_input("Guess Rebounds", min_value=0, max_value=50, value=predicted_rebounds)
guessed_assists = st.number_input("Guess Assists", min_value=0, max_value=50, value=predicted_assists)
guessed_steals = st.number_input("Guess Steals", min_value=0, max_value=20, value=predicted_steals)
guessed_blocks = st.number_input("Guess Blocks", min_value=0, max_value=20, value=predicted_blocks)
guessed_fg_pct = st.number_input("Guess Field Goal Percentage", min_value=0.0, max_value=100.0, value=predicted_fg_pct)
guessed_fg3_pct = st.number_input("Guess Three-Point Percentage", min_value=0.0, max_value=100.0, value=predicted_fg3_pct)

# Input field for user name
# Load existing names from a file or create an empty list if the file doesn't exist
names_filename = "names.json"
if os.path.exists(names_filename):
    with open(names_filename, "r", encoding="utf-8") as f:
        names = json.load(f)
else:
    names = []

# Dropdown to select a name from the list
selected_name = st.selectbox("Select your name", options=names)

# Option to add a new name
new_name = st.text_input("Or add a new name")

if new_name:
    if new_name not in names:
        names.append(new_name)
        with open(names_filename, "w", encoding="utf-8") as f:
            json.dump(names, f)
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
        guess_filename = f"guesses_{game_date_str}.txt"
        with open(guess_filename, "a", encoding="utf-8") as f:
            f.write(f"Name: {name}\n")
            f.write(f"Next Game Date: {next_game_date}\n")
            f.write(f"Guessed Points: {guessed_points}\n")
            f.write(f"Guessed Rebounds: {guessed_rebounds}\n")
            f.write(f"Guessed Assists: {guessed_assists}\n")
            f.write(f"Guessed Steals: {guessed_steals}\n")
            f.write(f"Guessed Blocks: {guessed_blocks}\n")
            f.write(f"Guessed Field Goal Percentage: {guessed_fg_pct:.2f}%\n")
            f.write(f"Guessed Three-Point Percentage: {guessed_fg3_pct:.2f}%\n")
            f.write("\n")
        
        st.success("Your guess has been saved!")
        
        # Display Last 5 Guesses
        st.subheader("Last 5 Guesses")

        # Read the guesses from the file
        guesses = []
        if os.path.exists(guess_filename):
            with open(guess_filename, "r", encoding="utf-8") as f:
                guess = {}
                for line in f:
                    if line.startswith("Name:"):
                        if guess:
                            guesses.append(guess)
                        guess = {"name": line.split(":")[1].strip()}
                    elif line.startswith("Guessed Points:"):
                        guess["points"] = int(line.split(":")[1].strip())
                    elif line.startswith("Guessed Rebounds:"):
                        guess["rebounds"] = int(line.split(":")[1].strip())
                    elif line.startswith("Guessed Assists:"):
                        guess["assists"] = int(line.split(":")[1].strip())
                    elif line.startswith("Guessed Steals:"):
                        guess["steals"] = int(line.split(":")[1].strip())
                    elif line.startswith("Guessed Blocks:"):
                        guess["blocks"] = int(line.split(":")[1].strip())
                    elif line.startswith("Guessed Field Goal Percentage:"):
                        guess["fg_pct"] = float(line.split(":")[1].strip().replace('%', ''))
                    elif line.startswith("Guessed Three-Point Percentage:"):
                        guess["fg3_pct"] = float(line.split(":")[1].strip().replace('%', ''))
                if guess:
                    guesses.append(guess)

        # Limit to the last 5 guesses
        guesses = guesses[-5:]

        # Display each guess
        for guess in guesses:
            st.markdown(f"**Name:** {guess['name']}")
            st.markdown(f"**Guessed Points:** {guess['points']}")
            st.markdown(f"**Guessed Rebounds:** {guess['rebounds']}")
            st.markdown(f"**Guessed Assists:** {guess['assists']}")
            st.markdown(f"**Guessed Steals:** {guess['steals']}")
            st.markdown(f"**Guessed Blocks:** {guess['blocks']}")
            st.markdown(f"**Guessed Field Goal Percentage:** {guess['fg_pct']:.2f}%")
            st.markdown(f"**Guessed Three-Point Percentage:** {guess['fg3_pct']:.2f}%")
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

        # Check if points have already been calculated and stored
        points_filename = "points.json"
        if os.path.exists(points_filename):
            with open(points_filename, "r", encoding="utf-8") as f:
                points_data = json.load(f)
        else:
            points_data = {}

        # Calculate points if not already calculated for the current game
        if current_game_date not in points_data:
            points_data[current_game_date] = {}

        for guess in guesses:
            name = guess["name"]
            if name not in points_data[current_game_date]:
                points_data[current_game_date][name] = calculate_points(guess, actual_stats)

        # Store the points data
        with open(points_filename, "w", encoding="utf-8") as f:
            json.dump(points_data, f)

        # Aggregate total points for each guesser
        total_points = {}
        for game_date, game_data in points_data.items():
            for name, points in game_data.items():
                if name not in total_points:
                    total_points[name] = 0
                total_points[name] += points

        # Store the total points data
        total_points_filename = "total_points.json"
        with open(total_points_filename, "w", encoding="utf-8") as f:
            json.dump(total_points, f)

        # Display the guesses with points
        for guess in guesses:
            name = guess["name"]
            points_scored = points_data[current_game_date].get(name, 0)
            st.write(f"Name: {name}, Points: {guess['points']}, Rebounds: {guess['rebounds']}, Assists: {guess['assists']}, Points Scored: {points_scored}")

        # Display the total points for each guesser
        st.subheader("Total Points for Each Guesser")
        for name, total in total_points.items():
            st.write(f"Name: {name}, Total Points: {total}")

# Display last game stats in a more visually appealing way
st.subheader("Last Game Stats")
last_game_date = pd.to_datetime(last_game_stats['GAME_DATE']).strftime('%B %d, %Y')
st.markdown(f"**Date:** {last_game_date}")
st.markdown(f"**Points:** {last_game_stats['PTS']}")
st.markdown(f"**Rebounds:** {last_game_stats['REB']}")
st.markdown(f"**Assists:** {last_game_stats['AST']}")
st.markdown(f"**Steals:** {last_game_stats['STL']}")
st.markdown(f"**Blocks:** {last_game_stats['BLK']}")
st.markdown(f"**Field Goal Percentage:** {last_game_stats['FG_PCT'] * 100:.2f}%")
st.markdown(f"**Three-Point Percentage:** {last_game_stats['FG3_PCT'] * 100:.2f}%")

# Display the guessers' points for this game
st.subheader("Guessers' Points for This Game")

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
        <h3 style="text-align:center; color:#FF6347;">Watch Deni Avdija's Highlights from {last_game_date}</h3>
        <a href="{video_url}" target="_blank">
            <img src="{video_thumbnail}" alt="Watch Deni Avdija's highlights from the game on {last_game_date}" style="width:80%; border-radius:10px;">
        </a>
    """, unsafe_allow_html=True)
else:
    st.markdown("Highlights not available yet.")

# Calculate and display the average rating
if os.path.exists(filename):
    reactions = []
    with open(filename, "r", encoding="utf-8") as f:
        reaction = {}
        for line in f:
            if line.startswith("Name:"):
                if reaction:
                    reactions.append(reaction)
                reaction = {"name": line.split(":")[1].strip()}
            elif line.startswith("Rating:"):
                reaction["rating"] = int(line.split(":")[1].strip().split()[0])
            elif line.startswith("Comment:"):
                reaction["comment"] = line.split(":")[1].strip()
        if reaction:
            reactions.append(reaction)

    if reactions:
        average_rating = sum([r['rating'] for r in reactions]) / len(reactions)
        st.markdown(f"**Average Rating:** {'🌟' * int(average_rating)} {average_rating:.2f} stars")
    else:
        st.markdown("No reactions yet.")
else:
    st.markdown("No reactions yet.")

# Add a reaction to the last game stats with stars, option to comment, and identify by name
st.subheader("React to The Last Game")
name = st.text_input("Enter your name")

reaction = st.slider("Rate Deni Avdija's performance in the last game (1-5 stars)", 1, 5, 3)
comment = st.text_area("Leave a comment about the performance")

if st.button("Submit Reaction"):
    if not name:
        st.error("Please enter your name.")
    else:
        if reaction == 5:
            st.write("🌟🌟🌟🌟🌟 Amazing! Deni Avdija had an outstanding game!")
        elif reaction == 4:
            st.write("🌟🌟🌟🌟 Good job! Deni Avdija performed well.")
        elif reaction == 3:
            st.write("🌟🌟🌟 Average performance. There's room for improvement.")
        elif reaction == 2:
            st.write("🌟🌟 Below average. It was a tough game.")
        else:
            st.write("🌟 Poor performance. Better luck next time!")
        
        if comment:
            st.write("**Your comment:**", comment)
        
        # Save the reaction and comment with the game date
        game_date_str = last_game_date.replace(" ", "_")
        filename = f"reactions_{game_date_str}.txt"
        with open(filename, "a", encoding="utf-8") as f:
            f.write(f"Name: {name}\nRating: {reaction} stars\nComment: {comment}\n\n")
        
        st.success("Your reaction has been saved!")

        # Display Last 5 Reactions and the average rating
        st.subheader("Last 5 Reactions and Average Rating")

        # Read the reactions from the file
        reactions = []
        with open(filename, "r", encoding="utf-8") as f:
            reaction = {}
            for line in f:
                if line.startswith("Name:"):
                    if reaction:
                        reactions.append(reaction)
                    reaction = {"name": line.split(":")[1].strip()}
                elif line.startswith("Rating:"):
                    reaction["rating"] = int(line.split(":")[1].strip().split()[0])
                elif line.startswith("Comment:"):
                    reaction["comment"] = line.split(":")[1].strip()
            if reaction:
                reactions.append(reaction)

        # Limit to the last 5 reactions
        reactions = reactions[-5:]
        # Display each reaction
        for reaction in reactions:
            if 'name' in reaction:
                st.markdown(f"**Name:** {reaction['name']}")
            if 'rating' in reaction:
                st.markdown(f"**Rating:** {'🌟' * reaction['rating']}")
            if 'comment' in reaction:
                st.markdown(f"**Comment:** {reaction['comment']}")
            st.markdown("---")

# Summarize stats
summary_stats = career_stats[['SEASON_ID', 'GP', 'PTS', 'REB', 'AST', 'STL', 'BLK']]
st.write("Career Summary Stats")
st.dataframe(summary_stats)

# Get game logs for the current season
current_season = '2024-25'  # Update this to the current season
gamelog = playergamelog.PlayerGameLog(player_id=player_id, season=current_season)
gamelog_stats = gamelog.get_data_frames()[0]

# Display the game log for the current season
st.subheader("Game Log for Current Season")
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
st.write("PPG, RPG, APG Progress Over the Season")
fig = go.Figure()
fig.add_trace(go.Scatter(x=current_season_stats['GAME_DATE'], y=current_season_stats['PPG'], mode='lines+markers', name='PPG Progress', line=dict(color='green')))
fig.add_trace(go.Scatter(x=current_season_stats['GAME_DATE'], y=current_season_stats['RPG'], mode='lines+markers', name='RPG Progress', line=dict(color='blue')))
fig.add_trace(go.Scatter(x=current_season_stats['GAME_DATE'], y=current_season_stats['APG'], mode='lines+markers', name='APG Progress', line=dict(color='red')))
fig.update_layout(title='PPG, RPG, APG Progress Over the Season', xaxis_title='Game Date', yaxis_title='Per Game Stats')
st.plotly_chart(fig)

# Plot FG% and 3P% progress over the season
st.write("FG% and 3P% Progress Over the Season")
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
st.write("Points Distribution from 2FG, 3FG, and FT Over the Season")
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
st.write("SPG and BPG Progress Over the Season")
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
st.write("Rolling Average PPG, RPG, APG Progress Over the Season (5 Games)")
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
st.write("Rolling Average FG% and 3P% Progress Over the Season (5 Games)")
fig = go.Figure()
fig.add_trace(go.Scatter(x=current_season_stats['GAME_DATE'], y=current_season_stats['Rolling_FG_PCT'], mode='lines+markers', name='Rolling FG%', line=dict(color='magenta')))
fig.add_trace(go.Scatter(x=current_season_stats['GAME_DATE'], y=current_season_stats['Rolling_FG3_PCT'], mode='lines+markers', name='Rolling 3P%', line=dict(color='cyan')))
fig.update_layout(title='Rolling Average FG% and 3P% Progress Over the Season (5 Games)', xaxis_title='Game Date', yaxis_title='Percentage')
st.plotly_chart(fig)

# Calculate rolling average SPG and BPG with a window of 5 games
current_season_stats['Rolling_SPG'] = current_season_stats['STL'].rolling(window=5).mean()
current_season_stats['Rolling_BPG'] = current_season_stats['BLK'].rolling(window=5).mean()

# Plot rolling average SPG and BPG progress over the season
st.write("Rolling Average SPG and BPG Progress Over the Season (5 Games)")
fig = go.Figure()
fig.add_trace(go.Scatter(x=current_season_stats['GAME_DATE'], y=current_season_stats['Rolling_SPG'], mode='lines+markers', name='Rolling SPG', line=dict(color='orange')))
fig.add_trace(go.Scatter(x=current_season_stats['GAME_DATE'], y=current_season_stats['Rolling_BPG'], mode='lines+markers', name='Rolling BPG', line=dict(color='purple')))
fig.update_layout(title='Rolling Average SPG and BPG Progress Over the Season (5 Games)', xaxis_title='Game Date', yaxis_title='Per Game Stats')
st.plotly_chart(fig)

