import streamlit as st
from nba_api.stats.endpoints import playercareerstats, playergamelog
from nba_api.stats.static import players
from nba_api.stats.endpoints import boxscoreadvancedv2
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

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
import os
if not os.path.exists(filename):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"Reactions for the game on {last_game_date}\n\n")

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

# Add a reaction to the last game stats with stars, option to comment, and identify by name and picture
st.subheader("React to Last Game Stats")
name = st.text_input("Enter your name")
picture = st.camera_input("Take a picture")
if picture:
    st.image(picture, caption=f"{name}'s picture", use_container_width=True)
    st.success("Photo uploaded successfully!")
    st.progress(100)
else:
    st.progress(0)

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
        
        if picture:
            st.image(picture, caption=f"{name}'s picture", use_container_width=True)
        
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

        # Calculate and display the average rating
        if reactions:
            average_rating = sum([r['rating'] for r in reactions]) / len(reactions)
            st.markdown(f"**Average Rating:** {'🌟' * int(average_rating)} {average_rating:.2f} stars")
        else:
            st.markdown("No reactions yet.")


# Summarize stats
summary_stats = career_stats[['SEASON_ID', 'GP', 'PTS', 'REB', 'AST', 'STL', 'BLK']]
st.write("Career Summary Stats")
st.dataframe(summary_stats)

# Get game logs for the current season
current_season = '2024-25'  # Update this to the current season
gamelog = playergamelog.PlayerGameLog(player_id=player_id, season=current_season)
gamelog_stats = gamelog.get_data_frames()[0]

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