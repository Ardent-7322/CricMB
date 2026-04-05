from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import pandas as pd
from sqlalchemy import create_engine, text

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

DB_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DB_URL)

ACTIVE_TEAMS = [
    'Mumbai Indians', 'Chennai Super Kings', 'Kolkata Knight Riders',
    'Royal Challengers Bengaluru', 'Rajasthan Royals', 'Delhi Capitals',
    'Sunrisers Hyderabad', 'Punjab Kings', 'Lucknow Super Giants', 'Gujarat Titans',
]

PACE_CODES = ['rf', 'rfm', 'rm', 'rmf', 'lf', 'lfm', 'lm', 'lmf']
SPIN_CODES = ['ob', 'lb', 'sla', 'slo', 'na']


def get_name_map():
    with engine.connect() as conn:
        players = pd.read_sql('SELECT "Name", "longName", "battingName" FROM players', conn)
    name_map = {}
    for _, row in players.iterrows():
        short = str(row['Name']).strip().lower()
        long = str(row['longName']).strip()
        batting = str(row['battingName']).strip().lower()
        name_map[short] = long
        name_map[batting] = long
    return name_map

name_map = get_name_map()


# ── Batter ────────────────────────────────────────────────────

def query_batter(batter_name, season=None):
    if season and season != 'all':
        q = text("SELECT phase, valid_ball, runs_batter, bowler_style, is_boundary, is_dot, match_id, innings FROM ipl_data WHERE batter = :batter AND season = :season")
        params = {'batter': batter_name, 'season': int(season)}
    else:
        q = text("SELECT phase, valid_ball, runs_batter, bowler_style, is_boundary, is_dot, match_id, innings FROM ipl_data WHERE batter = :batter")
        params = {'batter': batter_name}
    with engine.connect() as conn:
        df = pd.read_sql(q, conn, params=params)
    return df


def calc_batter_stats(df, batter_name):
    if df.empty:
        return None
    legal = df[df['valid_ball'] == 1]
    pp    = legal[legal['phase'] == 'powerplay']
    mid   = legal[legal['phase'] == 'middle']
    death = legal[legal['phase'] == 'death']

    pp_sr    = round(pp['runs_batter'].sum()    / len(pp)    * 100, 1) if len(pp)    > 0 else 0
    mid_sr   = round(mid['runs_batter'].sum()   / len(mid)   * 100, 1) if len(mid)   > 0 else 0
    death_sr = round(death['runs_batter'].sum() / len(death) * 100, 1) if len(death) > 0 else 0
    dot_pct  = round(df['is_dot'].sum()         / len(legal) * 100, 1) if len(legal) > 0 else 0

    pace = legal[legal['bowler_style'].str.lower().isin(PACE_CODES)]
    spin = legal[legal['bowler_style'].str.lower().isin(SPIN_CODES)]
    pace_sr = round(pace['runs_batter'].sum() / len(pace) * 100, 1) if len(pace) > 0 else 0
    spin_sr = round(spin['runs_batter'].sum() / len(spin) * 100, 1) if len(spin) > 0 else 0

    death_boundaries = death['is_boundary'].sum()
    death_bpb = round(len(death) / death_boundaries, 2) if death_boundaries > 0 else 0

    return {
        'name':        batter_name,
        'powerplay_sr': float(pp_sr),
        'middle_sr':    float(mid_sr),
        'death_sr':     float(death_sr),
        'dot_pct':      float(dot_pct),
        'pace_sr':      float(pace_sr),
        'spin_sr':      float(spin_sr),
        'death_bpb':    float(death_bpb),
        'total_runs':   int(df['runs_batter'].sum()),
        'balls_faced':  int(len(legal)),
        'innings':      int(df.groupby(['match_id', 'innings']).ngroups)
    }


def get_all_batter_stats(season=None):
    if season and season != 'all':
        q = text("SELECT batter, phase, valid_ball, runs_batter, bowler_style, is_boundary, is_dot, match_id, innings FROM ipl_data WHERE valid_ball = 1 AND season = :season")
        params = {'season': int(season)}
    else:
        q = text("SELECT batter, phase, valid_ball, runs_batter, bowler_style, is_boundary, is_dot, match_id, innings FROM ipl_data WHERE valid_ball = 1")
        params = {}
    with engine.connect() as conn:
        df = pd.read_sql(q, conn, params=params)
    results = []
    for batter in df['batter'].unique():
        bdf   = df[df['batter'] == batter]
        stats = calc_batter_stats(bdf, batter)
        if stats:
            results.append(stats)
    return results


def add_percentiles(results, all_stats):
    if not results or not all_stats:
        return results
    metrics = ['powerplay_sr', 'death_sr', 'pace_sr', 'spin_sr', 'total_runs']
    inverse = ['dot_pct', 'death_bpb']
    for metric in metrics:
        all_values = sorted([s[metric] for s in all_stats])
        n = len(all_values)
        for r in results:
            rank = sum(1 for v in all_values if v <= r[metric])
            r[f'{metric}_pct'] = round(rank / n * 100, 1)
    for metric in inverse:
        all_values = sorted([s[metric] for s in all_stats])
        n = len(all_values)
        for r in results:
            rank = sum(1 for v in all_values if v >= r[metric])
            r[f'{metric}_pct'] = round(rank / n * 100, 1)
    return results


# ── Bowler ────────────────────────────────────────────────────

def query_bowler(bowler_name, season=None):
    if season and season != 'all':
        q = text("SELECT phase, valid_ball, runs_bowler, runs_total, bowler_wicket, batter, match_id, innings FROM ipl_data WHERE bowler = :bowler AND season = :season")
        params = {'bowler': bowler_name, 'season': int(season)}
    else:
        q = text("SELECT phase, valid_ball, runs_bowler, runs_total, bowler_wicket, batter, match_id, innings FROM ipl_data WHERE bowler = :bowler")
        params = {'bowler': bowler_name}
    with engine.connect() as conn:
        df = pd.read_sql(q, conn, params=params)
    return df


def calc_bowler_stats(df, bowler_name):
    if df.empty:
        return None
    legal = df[df['valid_ball'] == 1]
    if len(legal) == 0:
        return None

    total_runs  = legal['runs_bowler'].sum()
    total_overs = len(legal) / 6
    economy     = round(total_runs / total_overs, 2) if total_overs > 0 else 0
    dots        = (legal['runs_total'] == 0).sum()
    dot_pct     = round(dots / len(legal) * 100, 1)
    wickets     = legal['bowler_wicket'].sum()
    bowling_sr  = round(len(legal) / wickets, 1) if wickets > 0 else 0

    death       = legal[legal['phase'] == 'death']
    death_econ  = round(death['runs_bowler'].sum() / (len(death) / 6), 2) if len(death) > 0 else 0

    with engine.connect() as conn:
        players = pd.read_sql('SELECT "battingName", "battingStyles" FROM players', conn)
    players['battingName'] = players['battingName'].str.strip().str.lower()
    rhb_list = set(players[players['battingStyles'] == 'rhb']['battingName'].tolist())
    lhb_list = set(players[players['battingStyles'] == 'lhb']['battingName'].tolist())

    rhb = legal[legal['batter'].isin(rhb_list)]
    lhb = legal[legal['batter'].isin(lhb_list)]
    wkts_vs_rhb = round(rhb['bowler_wicket'].sum() / len(rhb) * 100, 2) if len(rhb) > 0 else 0
    wkts_vs_lhb = round(lhb['bowler_wicket'].sum() / len(lhb) * 100, 2) if len(lhb) > 0 else 0

    return {
        'name':          bowler_name,
        'economy':       float(economy),
        'dot_pct':       float(dot_pct),
        'bowling_sr':    float(bowling_sr),
        'wickets':       int(wickets),
        'death_economy': float(death_econ),
        'wkts_vs_rhb':  float(wkts_vs_rhb),
        'wkts_vs_lhb':  float(wkts_vs_lhb),
        'balls_bowled':  int(len(legal)),
        'innings':       int(df.groupby(['match_id', 'innings']).ngroups)
    }


def get_all_bowler_stats(season=None):
    if season and season != 'all':
        q = text("SELECT bowler, phase, valid_ball, runs_bowler, runs_total, bowler_wicket, batter, match_id, innings FROM ipl_data WHERE valid_ball = 1 AND season = :season")
        params = {'season': int(season)}
    else:
        q = text("SELECT bowler, phase, valid_ball, runs_bowler, runs_total, bowler_wicket, batter, match_id, innings FROM ipl_data WHERE valid_ball = 1")
        params = {}
    with engine.connect() as conn:
        df = pd.read_sql(q, conn, params=params)

    with engine.connect() as conn:
        players_df = pd.read_sql(text('SELECT "battingName", "battingStyles" FROM players'), conn)
    players_df['battingName'] = players_df['battingName'].str.strip().str.lower()
    rhb_list = set(players_df[players_df['battingStyles'] == 'rhb']['battingName'].tolist())
    lhb_list = set(players_df[players_df['battingStyles'] == 'lhb']['battingName'].tolist())

    results = []
    for bowler in df['bowler'].unique():
        bdf   = df[df['bowler'] == bowler]
        legal = bdf[bdf['valid_ball'] == 1]
        if len(legal) == 0:
            continue
        total_runs  = legal['runs_bowler'].sum()
        total_overs = len(legal) / 6
        economy     = round(total_runs / total_overs, 2) if total_overs > 0 else 0
        dots        = (legal['runs_total'] == 0).sum()
        dot_pct     = round(dots / len(legal) * 100, 1)
        wickets     = legal['bowler_wicket'].sum()
        if wickets == 0:
            continue
        bowling_sr   = round(len(legal) / wickets, 1)
        death        = legal[legal['phase'] == 'death']
        death_econ   = round(death['runs_bowler'].sum() / (len(death) / 6), 2) if len(death) > 0 else 0
        rhb          = legal[legal['batter'].isin(rhb_list)]
        lhb          = legal[legal['batter'].isin(lhb_list)]
        wkts_vs_rhb  = round(rhb['bowler_wicket'].sum() / len(rhb) * 100, 2) if len(rhb) > 0 else 0
        wkts_vs_lhb  = round(lhb['bowler_wicket'].sum() / len(lhb) * 100, 2) if len(lhb) > 0 else 0
        results.append({
            'name':          bowler,
            'economy':       float(economy),
            'dot_pct':       float(dot_pct),
            'bowling_sr':    float(bowling_sr),
            'wickets':       int(wickets),
            'death_economy': float(death_econ),
            'wkts_vs_rhb':  float(wkts_vs_rhb),
            'wkts_vs_lhb':  float(wkts_vs_lhb),
        })
    return results


def add_bowler_percentiles(results, all_stats):
    if not results or not all_stats:
        return results
    high = ['dot_pct', 'wickets', 'wkts_vs_rhb', 'wkts_vs_lhb']
    low  = ['economy', 'bowling_sr', 'death_economy']
    for metric in high:
        all_values = sorted([s[metric] for s in all_stats])
        n = len(all_values)
        for r in results:
            rank = sum(1 for v in all_values if v <= r[metric])
            r[f'{metric}_pct'] = round(rank / n * 100, 1)
    for metric in low:
        all_values = sorted([s[metric] for s in all_stats])
        n = len(all_values)
        for r in results:
            rank = sum(1 for v in all_values if v >= r[metric])
            r[f'{metric}_pct'] = round(rank / n * 100, 1)
    return results


# ── Team ──────────────────────────────────────────────────────

def calc_team_stats(team_name, season=None):
    if season and season != 'all':
        q = text("""
            SELECT batting_team, bowling_team, match_id, innings,
                   phase, valid_ball, runs_batter, runs_total, venue,
                   match_won_by
            FROM ipl_data
            WHERE season = :season
              AND (batting_team = :team OR bowling_team = :team)
        """)
        params = {'season': int(season), 'team': team_name}
    else:
        q = text("""
            SELECT batting_team, bowling_team, match_id, innings,
                   phase, valid_ball, runs_batter, runs_total, venue,
                   match_won_by
            FROM ipl_data
            WHERE batting_team = :team OR bowling_team = :team
        """)
        params = {'team': team_name}

    with engine.connect() as conn:
        df = pd.read_sql(q, conn, params=params)

    if df.empty:
        return None

    matches    = df['match_id'].nunique()
    wins_df    = df[df['match_won_by'] == team_name]
    wins       = wins_df['match_id'].nunique()
    win_pct    = round(wins / matches * 100, 1) if matches > 0 else 0

    # Home win % — venue contains team city
    team_city  = team_name.split()[-1]
    home_df    = df[df['venue'].str.contains(team_city, case=False, na=False)]
    home_matches = home_df['match_id'].nunique()
    home_wins    = home_df[home_df['match_won_by'] == team_name]['match_id'].nunique()
    home_win_pct = round(home_wins / home_matches * 100, 1) if home_matches > 0 else 0

    # Batting stats
    batting = df[df['batting_team'] == team_name]
    legal   = batting[batting['valid_ball'] == 1]

    inn1         = legal[legal['innings'] == 1]
    inn2         = legal[legal['innings'] == 2]
    inn1_matches = inn1['match_id'].nunique()
    inn2_matches = inn2['match_id'].nunique()
    avg_1st      = round(inn1['runs_total'].sum() / inn1_matches, 1) if inn1_matches > 0 else 0
    avg_2nd      = round(inn2['runs_total'].sum() / inn2_matches, 1) if inn2_matches > 0 else 0

    pp           = legal[legal['phase'] == 'powerplay']
    pp_matches   = pp['match_id'].nunique()
    pp_avg       = round(pp['runs_total'].sum() / pp_matches, 1) if pp_matches > 0 else 0

    death        = legal[legal['phase'] == 'death']
    death_matches = death['match_id'].nunique()
    death_runs_avg = round(death['runs_total'].sum() / death_matches, 1) if death_matches > 0 else 0

    sixes          = (legal['runs_batter'] == 6).sum()
    sixes_per_match = round(sixes / matches, 1) if matches > 0 else 0

    return {
        'name':             team_name,
        'wins':             int(wins),
        'total_matches':    int(matches),
        'win_pct':          float(win_pct),
        'avg_1st_innings':  float(avg_1st),
        'avg_2nd_innings':  float(avg_2nd),
        'home_win_pct':     float(home_win_pct),
        'pp_avg':           float(pp_avg),
        'death_runs_avg':   float(death_runs_avg),
        'sixes_per_match':  float(sixes_per_match),
    }


def get_all_team_stats(season=None):
    results = []
    for team in ACTIVE_TEAMS:
        stats = calc_team_stats(team, season)
        if stats:
            results.append(stats)
    return results


def add_team_percentiles(results, all_stats):
    if not results or not all_stats:
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


# ── Routes ────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('../frontend', 'home.html')

@app.route('/index.html')
def batters_page():
    return send_from_directory('../frontend', 'index.html')

@app.route('/api/players', methods=['GET'])
def search_players():
    query = request.args.get('q', '').strip().lower()
    if not query or len(query) < 2:
        return jsonify([])
    with engine.connect() as conn:
        result = conn.execute(text("SELECT DISTINCT batter FROM ipl_data WHERE batter LIKE :q LIMIT 10"), {'q': f'%{query}%'})
        matched = [row[0] for row in result]
    return jsonify([{'id': p, 'display': name_map.get(p, p.title())} for p in matched])

@app.route('/api/bowlers', methods=['GET'])
def search_bowlers():
    query = request.args.get('q', '').strip().lower()
    if not query or len(query) < 2:
        return jsonify([])
    with engine.connect() as conn:
        result = conn.execute(text("SELECT DISTINCT bowler FROM ipl_data WHERE bowler LIKE :q LIMIT 10"), {'q': f'%{query}%'})
        matched = [row[0] for row in result]
    return jsonify([{'id': b, 'display': name_map.get(b, b.title())} for b in matched])

@app.route('/api/compare', methods=['GET'])
def compare_players():
    names  = request.args.getlist('players')
    season = request.args.get('season', 'all')
    if not names:
        return jsonify({'error': 'No players provided'}), 400
    if len(names) > 5:
        return jsonify({'error': 'Maximum 5 players allowed'}), 400

    all_stats = get_all_batter_stats(season)
    results   = []
    for name in names:
        df    = query_batter(name, season)
        stats = calc_batter_stats(df, name)
        if stats:
            stats['display_name'] = name_map.get(name, name.title())
            results.append(stats)

    if not results:
        return jsonify({'error': 'No players found'}), 404

    results = add_percentiles(results, all_stats)
    return jsonify(results)

@app.route('/api/compare_bowlers', methods=['GET'])
def compare_bowlers():
    names  = request.args.getlist('bowlers')
    season = request.args.get('season', 'all')
    if not names:
        return jsonify({'error': 'No bowlers provided'}), 400
    if len(names) > 5:
        return jsonify({'error': 'Maximum 5 bowlers allowed'}), 400

    all_stats = get_all_bowler_stats(season)
    results   = []
    for name in names:
        df    = query_bowler(name, season)
        stats = calc_bowler_stats(df, name)
        if stats:
            stats['display_name'] = name_map.get(name, name.title())
            results.append(stats)

    if not results:
        return jsonify({'error': 'No bowlers found'}), 404

    results = add_bowler_percentiles(results, all_stats)
    return jsonify(results)

@app.route('/api/teams', methods=['GET'])
def get_teams():
    return jsonify(ACTIVE_TEAMS)

@app.route('/api/compare_teams', methods=['GET'])
def compare_teams():
    names  = request.args.getlist('teams')
    season = request.args.get('season', 'all')
    if not names:
        return jsonify({'error': 'No teams provided'}), 400
    if len(names) > 5:
        return jsonify({'error': 'Maximum 5 teams allowed'}), 400

    all_stats = get_all_team_stats(season)
    results   = []
    for name in names:
        stats = calc_team_stats(name, season)
        if stats:
            results.append(stats)

    if not results:
        return jsonify({'error': 'No teams found'}), 404

    results = add_team_percentiles(results, all_stats)
    return jsonify(results)

@app.route('/api/seasons', methods=['GET'])
def get_seasons():
    with engine.connect() as conn:
        df = pd.read_sql("SELECT DISTINCT season FROM ipl_data ORDER BY season", conn)
    return jsonify([int(s) for s in df['season'].tolist()])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)




# #__________________local version____________________

# from flask import Flask, jsonify, request, send_from_directory
# from flask_cors import CORS
# import sys, os
# sys.path.append(os.path.dirname(__file__))
# from data_loader import load_from_db, clean_data, get_name_map
# from stats import get_multiple_batters, add_percentiles
# from bowler_stats import get_multiple_bowlers, add_bowler_percentiles
# from team_stats import (
#     standardize_team_names, get_multiple_teams,
#     add_team_percentiles, ACTIVE_TEAMS
# )

# app = Flask(__name__, static_folder='../frontend', static_url_path='')
# CORS(app)

# ipl, players = load_from_db()
# ipl_clean, players = clean_data(ipl, players)
# ipl_clean = standardize_team_names(ipl_clean)
# name_map = get_name_map(players)

# all_players = sorted(ipl_clean['batter'].unique().tolist())
# all_bowlers = sorted(ipl_clean['bowler'].unique().tolist())
# all_seasons = sorted(ipl_clean['season'].dropna().unique().tolist())

# # Lazy cache
# _global_batter_stats = None
# _global_bowler_stats = None

# def get_global_batter_stats():
#     global _global_batter_stats
#     if _global_batter_stats is None:
#         from stats import compute_global_percentiles
#         print("Computing batter percentiles...")
#         _global_batter_stats = compute_global_percentiles(ipl_clean)
#         print(f"Done! {len(_global_batter_stats)} batters indexed.")
#     return _global_batter_stats

# def get_global_bowler_stats():
#     global _global_bowler_stats
#     if _global_bowler_stats is None:
#         from bowler_stats import compute_global_bowler_percentiles
#         print("Computing bowler percentiles...")
#         _global_bowler_stats = compute_global_bowler_percentiles(ipl_clean)
#         print(f"Done! {len(_global_bowler_stats)} bowlers indexed.")
#     return _global_bowler_stats

# @app.route('/')
# def index():
#     return send_from_directory('../frontend', 'home.html')

# @app.route('/index.html')
# def batters():
#     return send_from_directory('../frontend', 'index.html')

# @app.route('/api/players', methods=['GET'])
# def search_players():
#     query = request.args.get('q', '').strip().lower()
#     if not query or len(query) < 2:
#         return jsonify([])
#     matched = [p for p in all_players if query in p][:10]
#     return jsonify([{'id': p, 'display': name_map.get(p, p.title())} for p in matched])

# @app.route('/api/bowlers', methods=['GET'])
# def search_bowlers():
#     query = request.args.get('q', '').strip().lower()
#     if not query or len(query) < 2:
#         return jsonify([])
#     matched = [b for b in all_bowlers if query in b][:10]
#     return jsonify([{'id': b, 'display': name_map.get(b, b.title())} for b in matched])

# @app.route('/api/compare', methods=['GET'])
# def compare_players():
#     names = request.args.getlist('players')
#     season = request.args.get('season', 'all')

#     if not names:
#         return jsonify({'error': 'No players provided'}), 400
#     if len(names) > 5:
#         return jsonify({'error': 'Maximum 5 players allowed'}), 400

#     results = get_multiple_batters(ipl_clean, names, season)
#     if not results:
#         return jsonify({'error': 'No players found'}), 404

#     for r in results:
#         r['display_name'] = name_map.get(r['name'], r['name'].title())

#     results = add_percentiles(results, get_global_batter_stats())
#     return jsonify(results)

# @app.route('/api/compare_bowlers', methods=['GET'])
# def compare_bowlers():
#     names = request.args.getlist('bowlers')
#     season = request.args.get('season', 'all')

#     if not names:
#         return jsonify({'error': 'No bowlers provided'}), 400
#     if len(names) > 5:
#         return jsonify({'error': 'Maximum 5 bowlers allowed'}), 400

#     results = get_multiple_bowlers(ipl_clean, names, season)
#     if not results:
#         return jsonify({'error': 'No bowlers found'}), 404

#     for r in results:
#         r['display_name'] = name_map.get(r['name'], r['name'].title())

#     results = add_bowler_percentiles(results, get_global_bowler_stats())
#     return jsonify(results)

# @app.route('/api/teams', methods=['GET'])
# def get_teams():
#     return jsonify(ACTIVE_TEAMS)

# @app.route('/api/compare_teams', methods=['GET'])
# def compare_teams():
#     names = request.args.getlist('teams')
#     season = request.args.get('season', 'all')

#     if not names:
#         return jsonify({'error': 'No teams provided'}), 400
#     if len(names) < 2:
#         return jsonify({'error': 'At least 2 teams required'}), 400
#     if len(names) > 5:
#         return jsonify({'error': 'Maximum 5 teams allowed'}), 400

#     season_stats = get_multiple_teams(ipl_clean, ACTIVE_TEAMS, season)
#     if not season_stats:
#         return jsonify({'error': 'No data for this season'}), 404

#     results = get_multiple_teams(ipl_clean, names, season)
#     if not results:
#         return jsonify({'error': 'No teams found'}), 404

#     results = add_team_percentiles(results, season_stats)
#     return jsonify(results)

# @app.route('/api/seasons', methods=['GET'])
# def get_seasons():
#     return jsonify([int(s) for s in all_seasons])

# if __name__ == '__main__':
#     port = int(os.environ.get('PORT', 5000))
#     app.run(host='0.0.0.0', port=port)
