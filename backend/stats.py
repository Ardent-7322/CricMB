import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(__file__))
from data_loader import load_data, clean_data

def get_batter_stats(ipl, batter_name, season=None):
    batter_name = batter_name.strip().lower()
    df = ipl[ipl['batter'] == batter_name].copy()

    if df.empty:
        return None

    if season and season != 'all':
        df = df[df['season'] == int(season)]
        if df.empty:
            return None

    legal = df[df['valid_ball'] == 1]
    pp = legal[legal['phase'] == 'powerplay']
    mid = legal[legal['phase'] == 'middle']
    death = legal[legal['phase'] == 'death']

    pp_sr = round(pp['runs_batter'].sum() / len(pp) * 100, 1) if len(pp) > 0 else 0
    mid_sr = round(mid['runs_batter'].sum() / len(mid) * 100, 1) if len(mid) > 0 else 0
    death_sr = round(death['runs_batter'].sum() / len(death) * 100, 1) if len(death) > 0 else 0
    dot_pct = round(df['is_dot'].sum() / len(legal) * 100, 1) if len(legal) > 0 else 0

    pace = legal[legal['is_pace'] == True]
    spin = legal[legal['is_spin'] == True]
    pace_sr = round(pace['runs_batter'].sum() / len(pace) * 100, 1) if len(pace) > 0 else 0
    spin_sr = round(spin['runs_batter'].sum() / len(spin) * 100, 1) if len(spin) > 0 else 0

    death_boundaries = death['is_boundary'].sum()
    death_bpb = round(len(death) / death_boundaries, 2) if death_boundaries > 0 else 0

    return {
        'name': batter_name,
        'powerplay_sr': float(pp_sr),
        'middle_sr': float(mid_sr),
        'death_sr': float(death_sr),
        'dot_pct': float(dot_pct),
        'pace_sr': float(pace_sr),
        'spin_sr': float(spin_sr),
        'death_bpb': float(death_bpb),
        'total_runs': int(df['runs_batter'].sum()),
        'balls_faced': int(len(legal)),
        'innings': int(df.groupby(['match_id', 'innings']).ngroups)
    }
def compute_global_percentiles(ipl_clean):
    all_batters = ipl_clean['batter'].unique().tolist()
    all_stats = []
    for name in all_batters:
        stats = get_batter_stats(ipl_clean, name)
        if stats:
            all_stats.append(stats)
    return all_stats

def add_percentiles(results, all_stats):
    if not results:
        return results

    metrics = ['powerplay_sr', 'death_sr', 'pace_sr', 'spin_sr', 'total_runs']
    inverse_metrics = ['dot_pct', 'death_bpb']

    for metric in metrics:
        all_values = sorted([s[metric] for s in all_stats])
        n = len(all_values)
        for r in results:
            rank = sum(1 for v in all_values if v <= r[metric])
            r[f'{metric}_pct'] = round(rank / n * 100, 1)

    for metric in inverse_metrics:
        all_values = sorted([s[metric] for s in all_stats])
        n = len(all_values)
        for r in results:
            rank = sum(1 for v in all_values if v >= r[metric])
            r[f'{metric}_pct'] = round(rank / n * 100, 1)

    return results

def get_multiple_batters(df, batter_names, season=None):
    results = []
    for name in batter_names:
        stats = get_batter_stats(df, name, season)
        if stats:
            results.append(stats)
        else:
            print(f"Player not found: {name}")
    return results

if __name__ == '__main__':
    ipl, players = load_data()
    ipl_clean, players = clean_data(ipl, players)
    test_players = ['v kohli', 'kl rahul', 'ms dhoni']
    results = get_multiple_batters(ipl_clean, test_players)
    for r in results:
        print(r)
