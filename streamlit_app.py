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

# Get advanced box score stats for the current season
boxscore_advanced = boxscoreadvancedv2.BoxScoreAdvancedV2(player_id=player_id, season=current_season)
boxscore_advanced_stats = boxscore_advanced.get_data_frames()[0]
# Summarize advanced stats
advanced_stats = boxscore_advanced_stats[['GAME_ID', 'GAME_DATE', 'OFF_RATING', 'DEF_RATING', 'NET_RATING', 'USG_PCT', 'TS_PCT']]
advanced_stats['GAME_DATE'] = pd.to_datetime(advanced_stats['GAME_DATE'])

# Plot Offensive Rating, Defensive Rating, and Net Rating over the season
st.write("Offensive Rating, Defensive Rating, and Net Rating Over the Season")
fig = go.Figure()
fig.add_trace(go.Scatter(x=advanced_stats['GAME_DATE'], y=advanced_stats['OFF_RATING'], mode='lines+markers', name='Offensive Rating', line=dict(color='green')))
fig.add_trace(go.Scatter(x=advanced_stats['GAME_DATE'], y=advanced_stats['DEF_RATING'], mode='lines+markers', name='Defensive Rating', line=dict(color='red')))
fig.add_trace(go.Scatter(x=advanced_stats['GAME_DATE'], y=advanced_stats['NET_RATING'], mode='lines+markers', name='Net Rating', line=dict(color='blue')))
fig.update_layout(title='Offensive, Defensive, and Net Rating Over the Season', xaxis_title='Game Date', yaxis_title='Rating')
st.plotly_chart(fig)

# Plot Usage Percentage and True Shooting Percentage over the season
st.write("Usage Percentage and True Shooting Percentage Over the Season")
fig = go.Figure()
fig.add_trace(go.Scatter(x=advanced_stats['GAME_DATE'], y=advanced_stats['USG_PCT'], mode='lines+markers', name='Usage Percentage', line=dict(color='purple')))
fig.add_trace(go.Scatter(x=advanced_stats['GAME_DATE'], y=advanced_stats['TS_PCT'], mode='lines+markers', name='True Shooting Percentage', line=dict(color='orange')))
fig.update_layout(title='Usage Percentage and True Shooting Percentage Over the Season', xaxis_title='Game Date', yaxis_title='Percentage')
st.plotly_chart(fig)

# Calculate opponent field goal attempts (Opp FGA) from advanced box score stats
advanced_stats['Opp_FGA'] = boxscore_advanced_stats['OPP_FGA']

# Calculate cumulative Opp FGA after each game
advanced_stats['Cumulative_Opp_FGA'] = advanced_stats['Opp_FGA'].cumsum()
# Calculate Opp FGA per game (Opp FGA PG) after each game
advanced_stats['Opp_FGA_PG'] = advanced_stats['Cumulative_Opp_FGA'] / range(1, len(advanced_stats) + 1)

# Plot Opp FGA progress over the season
st.write("Opponent Field Goal Attempts (Opp FGA) Progress Over the Season")
fig = go.Figure()
fig.add_trace(go.Scatter(x=advanced_stats['GAME_DATE'], y=advanced_stats['Opp_FGA_PG'], mode='lines+markers', name='Opp FGA Progress', line=dict(color='brown')))
fig.update_layout(title='Opponent Field Goal Attempts (Opp FGA) Progress Over the Season', xaxis_title='Game Date', yaxis_title='Opp FGA Per Game')
st.plotly_chart(fig)
