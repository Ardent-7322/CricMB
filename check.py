import pandas as pd
players = pd.read_csv('data/2024_players_details.csv')
print(players[['Name', 'longName', 'battingName']].head(10).to_string())