import pandas as pd
import sys, os
sys.path.append(os.path.dirname(__file__))
from data_loader import load_data, clean_data

def get_bowler_stats(ipl, bowler_name, season=None):
    bowler_name = bowler_name.strip().lower()
    df = ipl[ipl['bowler'] == bowler_name].copy()

    if df.empty:
        return None

    if season and season != 'all':
        df = df[df['season'] == int(season)]
        if df.empty:
            return None

    legal = df[df['valid_ball'] == 1]

    if len(legal) == 0:
        return None

    # 1. Overall economy (runs per over)
    total_runs = legal['runs_bowler'].sum()
    total_overs = len(legal) / 6
    economy = round(total_runs / total_overs, 2) if total_overs > 0 else 0

    # 2. Dot ball %
    dots = (legal['runs_total'] == 0).sum()
    dot_pct = round(dots / len(legal) * 100, 1)

    # 3. Bowling strike rate (balls per wicket)
    wickets = legal['bowler_wicket'].sum()
    bowling_sr = round(len(legal) / wickets, 1) if wickets > 0 else 0

    # 4. Total wickets
    total_wickets = int(wickets)

    # 5. Death economy (overs 16-20)
    death = legal[legal['phase'] == 'death']
    death_runs = death['runs_bowler'].sum()
    death_overs = len(death) / 6
    death_economy = round(death_runs / death_overs, 2) if death_overs > 0 else 0

    # 6. Wicket % vs RHB
    rhb = legal[legal['batter'].isin(get_rhb_list(ipl))]
    rhb_wickets = rhb['bowler_wicket'].sum()
    wkts_vs_rhb = round(rhb_wickets / len(rhb) * 100, 2) if len(rhb) > 0 else 0

    # 7. Wicket % vs LHB
    lhb = legal[legal['batter'].isin(get_lhb_list(ipl))]
    lhb_wickets = lhb['bowler_wicket'].sum()
    wkts_vs_lhb = round(lhb_wickets / len(lhb) * 100, 2) if len(lhb) > 0 else 0

    return {
        'name': bowler_name,
        'economy': float(economy),
        'dot_pct': float(dot_pct),
        'bowling_sr': float(bowling_sr),
        'wickets': total_wickets,
        'death_economy': float(death_economy),
        'wkts_vs_rhb': float(wkts_vs_rhb),
        'wkts_vs_lhb': float(wkts_vs_lhb),
        'balls_bowled': int(len(legal)),
        'innings': int(df.groupby(['match_id', 'innings']).ngroups)
    }

# Cache these lists
_rhb_list = None
_lhb_list = None

def get_rhb_list(ipl):
    global _rhb_list
    if _rhb_list is None:
        try:
            import pandas as pd
            players = pd.read_csv(os.path.join(os.path.dirname(__file__), '..', 'data', '2024_players_details.csv'))
            players['battingName'] = players['battingName'].str.strip().str.lower()
            players['Name'] = players['Name'].str.strip().str.lower()
            rhb = players[players['battingStyles'] == 'rhb']
            _rhb_list = set(rhb['battingName'].dropna().tolist() + rhb['Name'].dropna().tolist())
        except:
            _rhb_list = set()
    return _rhb_list

def get_lhb_list(ipl):
    global _lhb_list
    if _lhb_list is None:
        try:
            import pandas as pd
            players = pd.read_csv(os.path.join(os.path.dirname(__file__), '..', 'data', '2024_players_details.csv'))
            players['battingName'] = players['battingName'].str.strip().str.lower()
            players['Name'] = players['Name'].str.strip().str.lower()
            lhb = players[players['battingStyles'] == 'lhb']
            _lhb_list = set(lhb['battingName'].dropna().tolist() + lhb['Name'].dropna().tolist())
        except:
            _lhb_list = set()
    return _lhb_list

def add_bowler_percentiles(results, all_stats):
    if not results:
        return results

    # Higher is better
    high_metrics = ['dot_pct', 'wickets', 'wkts_vs_rhb', 'wkts_vs_lhb']
    # Lower is better
    low_metrics = ['economy', 'bowling_sr', 'death_economy']

    for metric in high_metrics:
        all_values = sorted([s[metric] for s in all_stats])
        n = len(all_values)
        for r in results:
            rank = sum(1 for v in all_values if v <= r[metric])
            r[f'{metric}_pct'] = round(rank / n * 100, 1)

    for metric in low_metrics:
        all_values = sorted([s[metric] for s in all_stats])
        n = len(all_values)
        for r in results:
            rank = sum(1 for v in all_values if v >= r[metric])
            r[f'{metric}_pct'] = round(rank / n * 100, 1)

    return results

def compute_global_bowler_percentiles(ipl_clean):
    all_bowlers = ipl_clean['bowler'].unique().tolist()
    all_stats = []
    for name in all_bowlers:
        stats = get_bowler_stats(ipl_clean, name)
        if stats and stats['wickets'] > 0:
            all_stats.append(stats)
    print(f"Indexed {len(all_stats)} bowlers")
    return all_stats

def get_multiple_bowlers(df, bowler_names, season=None):
    results = []
    for name in bowler_names:
        stats = get_bowler_stats(df, name, season)
        if stats:
            results.append(stats)
        else:
            print(f"Bowler not found: {name}")
    return results

if __name__ == '__main__':
    ipl, players = load_data()
    ipl_clean, players = clean_data(ipl, players)
    test_bowlers = ['jj bumrah', 'yt pathan', 'b kumar']
    for name in test_bowlers:
        stats = get_bowler_stats(ipl_clean, name)
        if stats:
            print(stats)
        else:
            print(f"Not found: {name}")

