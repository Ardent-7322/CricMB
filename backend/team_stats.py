import pandas as pd
import sys, os
sys.path.append(os.path.dirname(__file__))
from db_loader import load_from_db

TEAM_NAME_MAP = {
    "Royal Challengers Bangalore": "Royal Challengers Bengaluru",
    "Delhi Daredevils": "Delhi Capitals",
    "Kings XI Punjab": "Punjab Kings"
}

ACTIVE_TEAMS = [
    'Mumbai Indians',
    'Chennai Super Kings',
    'Kolkata Knight Riders',
    'Royal Challengers Bengaluru',
    'Rajasthan Royals',
    'Delhi Capitals',
    'Sunrisers Hyderabad',
    'Punjab Kings',
    'Lucknow Super Giants',
    'Gujarat Titans',
]

HOME_GROUNDS = {
    'Mumbai Indians': ['wankhede', 'mumbai'],
    'Chennai Super Kings': ['chidambaram', 'chepauk', 'chennai'],
    'Kolkata Knight Riders': ['eden gardens', 'kolkata'],
    'Royal Challengers Bengaluru': ['chinnaswamy', 'bangalore', 'bengaluru'],
    'Rajasthan Royals': ['sawai mansingh', 'jaipur'],
    'Delhi Capitals': ['feroz shah kotla', 'arun jaitley', 'delhi'],
    'Sunrisers Hyderabad': ['rajiv gandhi', 'uppal', 'hyderabad'],
    'Punjab Kings': ['mohali', 'punjab', 'pca', 'dharamsala'],
    'Lucknow Super Giants': ['ekana', 'lucknow'],
    'Gujarat Titans': ['narendra modi', 'ahmedabad', 'gujarat'],
}

def standardize_team_names(df):
    for col in ['batting_team', 'bowling_team', 'match_won_by']:
        if col in df.columns:
            df[col] = df[col].replace(TEAM_NAME_MAP)
    return df

def get_match_level(ipl):
    final = ipl.sort_values('ball_no').groupby(
        ['match_id', 'innings', 'batting_team', 'bowling_team']
    ).last().reset_index()
    return final[['match_id', 'innings', 'batting_team', 'bowling_team',
                  'team_runs', 'team_wicket', 'match_won_by',
                  'season', 'venue', 'result_type']]

def get_team_stats(ipl, team_name, season=None):
    if team_name not in ACTIVE_TEAMS:
        return None

    df = ipl.copy()
    if season and season != 'all':
        df = df[df['season'] == int(season)]

    if df.empty:
        return None

    match_data = get_match_level(df)

    team_match_ids = match_data[
        (match_data['batting_team'] == team_name) |
        (match_data['bowling_team'] == team_name)
    ]['match_id'].unique()

    if len(team_match_ids) == 0:
        return None

    valid = match_data[
        (match_data['match_id'].isin(team_match_ids)) &
        (match_data['result_type'].isna())
    ]
    valid_ids = valid['match_id'].unique()
    total_matches = len(valid_ids)

    if total_matches == 0:
        return None

    # Win %
    wins = match_data[
        (match_data['match_id'].isin(valid_ids)) &
        (match_data['match_won_by'] == team_name)
    ]['match_id'].nunique()
    win_pct = round(wins / total_matches * 100, 1)

    # Avg 1st innings score
    inn1 = match_data[
        (match_data['batting_team'] == team_name) &
        (match_data['innings'] == 1) &
        (match_data['match_id'].isin(valid_ids))
    ]
    avg_1st = round(inn1['team_runs'].mean(), 1) if len(inn1) > 0 else 0

    # Avg 2nd innings score
    inn2 = match_data[
        (match_data['batting_team'] == team_name) &
        (match_data['innings'] == 2) &
        (match_data['match_id'].isin(valid_ids))
    ]
    avg_2nd = round(inn2['team_runs'].mean(), 1) if len(inn2) > 0 else 0

    # Home win % using keyword matching
    home_keywords = HOME_GROUNDS.get(team_name, [])
    if home_keywords:
        home_ids = match_data[
            (match_data['match_id'].isin(valid_ids)) &
            (match_data['venue'].str.lower().apply(
                lambda v: any(kw in str(v).lower() for kw in home_keywords)
            ))
        ]['match_id'].unique()
        home_wins = match_data[
            (match_data['match_id'].isin(home_ids)) &
            (match_data['match_won_by'] == team_name)
        ]['match_id'].nunique()
        home_win_pct = round(home_wins / len(home_ids) * 100, 1) if len(home_ids) > 0 else 0
    else:
        home_win_pct = 0

    # Powerplay avg (end of over 6)
    pp = df[
        (df['batting_team'] == team_name) &
        (df['over'] == 6)
    ]
    pp_avg = round(pp.groupby('match_id')['team_runs'].last().mean(), 1) if len(pp) > 0 else 0

    # Death overs average runs (overs 16-20)
    death_df = df[
        (df['batting_team'] == team_name) &
        (df['over'] >= 16) &
        (df['over'] <= 20)
    ]
    if len(death_df) > 0:
        runs = death_df.groupby('match_id')['runs_total'].sum()
        balls = death_df.groupby('match_id')['valid_ball'].sum()
        overs = balls / 6
        rr = runs / overs
        death_runs_avg = round(rr.mean(), 1)
    else:
        death_runs_avg = 0

    # Sixes per match
    sixes = df[
        (df['batting_team'] == team_name) &
        (df['runs_batter'] == 6)
    ].shape[0]
    sixes_per_match = round(sixes / total_matches, 1) if total_matches > 0 else 0

    return {
        'name': team_name,
        'win_pct': float(win_pct),
        'avg_1st_innings': float(avg_1st),
        'avg_2nd_innings': float(avg_2nd),
        'home_win_pct': float(home_win_pct),
        'pp_avg': float(pp_avg),
        'death_runs_avg': float(death_runs_avg),
        'sixes_per_match': float(sixes_per_match),
        'total_matches': int(total_matches),
        'wins': int(wins)
    }

def get_multiple_teams(ipl, team_names, season=None):
    results = []
    for name in team_names:
        stats = get_team_stats(ipl, name, season)
        if stats:
            results.append(stats)
        else:
            print(f"Team not found or inactive: {name}")
    return results

def add_team_percentiles(results, all_stats):
    if not results:
        return results
    metrics = ['win_pct', 'avg_1st_innings', 'avg_2nd_innings',
               'home_win_pct', 'pp_avg', 'death_runs_avg', 'sixes_per_match']
    for metric in metrics:
        all_values = sorted([s[metric] for s in all_stats])
        n = len(all_values)
        for r in results:
            rank = sum(1 for v in all_values if v <= r[metric])
            r[f'{metric}_pct'] = round(rank / n * 100, 1)
    return results

def compute_global_team_percentiles(ipl):
    ipl = standardize_team_names(ipl)
    all_stats = []
    for team in ACTIVE_TEAMS:
        stats = get_team_stats(ipl, team)
        if stats and stats['total_matches'] > 5:
            all_stats.append(stats)
    print(f"Indexed {len(all_stats)} teams")
    return all_stats

if __name__ == '__main__':
    ipl, players = load_data()
    ipl, players = clean_data(ipl, players)
    ipl = standardize_team_names(ipl)
    for team in ACTIVE_TEAMS:
        stats = get_team_stats(ipl, team)
        print(stats)