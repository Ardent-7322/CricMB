import pandas as pd

matches = pd.read_csv('data/Match_Info.csv')
print(matches[['match_number', 'team1', 'team2', 'venue']].head(10).to_string())