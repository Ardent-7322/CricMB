import pandas as pd

ipl = pd.read_csv('data/IPL.csv', low_memory=False)
ipl = ipl[ipl['event_name'].str.contains('Indian Premier League', case=False, na=False)]

print("match_won_by:", ipl['match_won_by'].unique())
print("win_outcome:", ipl['win_outcome'].unique()[:10])
print("toss_decision:", ipl['toss_decision'].unique())
print("result_type:", ipl['result_type'].unique())
print("team_runs sample:", ipl[['batting_team', 'team_runs', 'team_wicket', 'innings']].drop_duplicates().head(10))