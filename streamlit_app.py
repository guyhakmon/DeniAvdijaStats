import streamlit as st
from nba_api.stats.endpoints import playercareerstats, playergamelog
from nba_api.stats.static import players
import matplotlib.pyplot as plt
import pandas as pd

# Streamlit app title
st.title("Deni Avdija's NBA Stats")

# Find player ID for Deni Avdija
player_dict = players.find_players_by_full_name("Deni Avdija")
player_id = player_dict[0]['id']

# Get career stats for Deni Avdija
career = playercareerstats.PlayerCareerStats(player_id=player_id)
career_stats = career.get_data_frames()[0]

# Summarize stats
summary_stats = career_stats[['SEASON_ID', 'PTS', 'REB', 'AST', 'STL', 'BLK']]
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
fig, ax = plt.subplots()
ax.plot(current_season_stats['GAME_DATE'], current_season_stats['PPG'], marker='o', linestyle='-', color='g', label='PPG Progress')
ax.plot(current_season_stats['GAME_DATE'], current_season_stats['RPG'], marker='o', linestyle='-', color='b', label='RPG Progress')
ax.plot(current_season_stats['GAME_DATE'], current_season_stats['APG'], marker='o', linestyle='-', color='r', label='APG Progress')
ax.set_xlabel('Game Date')
ax.set_ylabel('Per Game Stats')
ax.set_title('PPG, RPG, APG Progress Over the Season')
ax.legend()
ax.grid(True)
ax.tick_params(axis='x', rotation=45)
st.pyplot(fig)

# Plot FG% and 3P% progress over the season
st.write("FG% and 3P% Progress Over the Season")
fig, ax = plt.subplots()
ax.plot(current_season_stats['GAME_DATE'], current_season_stats['Cumulative_FG_PCT'], marker='o', linestyle='-', color='m', label='FG% Progress')
ax.plot(current_season_stats['GAME_DATE'], current_season_stats['Cumulative_FG3_PCT'], marker='o', linestyle='-', color='c', label='3P% Progress')
ax.set_xlabel('Game Date')
ax.set_ylabel('Percentage')
ax.set_title('FG% and 3P% Progress Over the Season')
ax.legend()
ax.grid(True)
ax.tick_params(axis='x', rotation=45)
st.pyplot(fig)

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
fig, ax = plt.subplots()
ax.plot(current_season_stats['GAME_DATE'], current_season_stats['2FG_PPG'], marker='o', linestyle='-', color='g', label='Points from 2FG Per Game')
ax.plot(current_season_stats['GAME_DATE'], current_season_stats['3FG_PPG'], marker='o', linestyle='-', color='r', label='Points from 3FG Per Game')
ax.plot(current_season_stats['GAME_DATE'], current_season_stats['FT_PPG'], marker='o', linestyle='-', color='b', label='Points from FT Per Game')
ax.set_xlabel('Game Date')
ax.set_ylabel('Points Per Game')
ax.set_title('Points Distribution from 2FG, 3FG, and FT Over the Season')
ax.legend()
ax.grid(True)
ax.tick_params(axis='x', rotation=45)
st.pyplot(fig)


