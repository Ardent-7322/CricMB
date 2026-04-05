import pandas as pd
import os
from sqlalchemy import create_engine

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
#DB_URL = os.environ.get("DATABASE_URL") --> deployed
DB_URL = os.environ.get("DATABASE_URL")
def load_data():
    ipl = pd.read_csv(os.path.join(DATA_DIR, 'IPL.csv'), low_memory=False)
    players = pd.read_csv(os.path.join(DATA_DIR, '2024_players_details.csv'))
    return ipl, players

def load_from_db():
    engine = create_engine(DB_URL)
    print("Loading ipl_data from database...")
    ipl = pd.read_sql("SELECT * FROM ipl_data", engine)
    print("Loading players from database...")
    players = pd.read_sql("SELECT * FROM players", engine)
    print("Done loading from database!")
    return ipl, players

def clean_data(ipl, players):
    ipl['batter'] = ipl['batter'].str.strip().str.lower()
    ipl['bowler'] = ipl['bowler'].str.strip().str.lower()
    players['battingName'] = players['battingName'].str.strip().str.lower()
    players['Name'] = players['Name'].str.strip().str.lower()

    valid_batters = players['battingName'].dropna().tolist()
    valid_batters += players['Name'].dropna().tolist()
    valid_batters = list(set(valid_batters))

    ipl = ipl[ipl['batter'].isin(valid_batters)].copy()

    if 'match_type' in ipl.columns:
        ipl = ipl[ipl['match_type'] == 'T20'].copy()

    ipl['season'] = ipl['season'].astype(str).str[:4].astype(int)

    if 'bowler_style' not in ipl.columns:
        bowler_style = players[['Name', 'bowlingStyles']].copy()
        bowler_style.rename(columns={'Name': 'bowler', 'bowlingStyles': 'bowler_style'}, inplace=True)
        ipl = ipl.merge(bowler_style, on='bowler', how='left')

    pace_codes = ['rf', 'rfm', 'rm', 'rmf', 'lf', 'lfm', 'lm', 'lmf']
    spin_codes = ['ob', 'lb', 'sla', 'slo', 'na']
    ipl['is_pace'] = ipl['bowler_style'].str.lower().isin(pace_codes)
    ipl['is_spin'] = ipl['bowler_style'].str.lower().isin(spin_codes)

    def get_phase(over):
        if over <= 6:
            return 'powerplay'
        elif over <= 15:
            return 'middle'
        else:
            return 'death'
    ipl['phase'] = ipl['over'].apply(get_phase)

    ipl['is_boundary'] = ipl['runs_batter'].isin([4, 6])
    ipl['is_dot'] = ipl['runs_batter'] == 0

    return ipl, players

def get_name_map(players):
    name_map = {}
    for _, row in players.iterrows():
        short = str(row['Name']).strip().lower()
        long = str(row['longName']).strip()
        batting = str(row['battingName']).strip().lower()
        name_map[short] = long
        name_map[batting] = long
    return name_map
