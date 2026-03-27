from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import sys, os
sys.path.append(os.path.dirname(__file__))
from data_loader import load_data, clean_data, get_name_map
from stats import get_multiple_batters, compute_global_percentiles, add_percentiles
from bowler_stats import get_multiple_bowlers, compute_global_bowler_percentiles, add_bowler_percentiles

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

ipl, players = load_data()
ipl_clean, players = clean_data(ipl, players)
name_map = get_name_map(players)

print("Computing batter percentiles...")
global_batter_stats = compute_global_percentiles(ipl_clean)
print(f"Done! {len(global_batter_stats)} batters indexed.")

print("Computing bowler percentiles...")
global_bowler_stats = compute_global_bowler_percentiles(ipl_clean)
print(f"Done! {len(global_bowler_stats)} bowlers indexed.")

all_players = sorted(ipl_clean['batter'].unique().tolist())
all_bowlers = sorted(ipl_clean['bowler'].unique().tolist())
all_seasons = sorted(ipl_clean['season'].dropna().unique().tolist())

@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/api/players', methods=['GET'])
def search_players():
    query = request.args.get('q', '').strip().lower()
    if not query or len(query) < 2:
        return jsonify([])
    matched = [p for p in all_players if query in p][:10]
    return jsonify([{'id': p, 'display': name_map.get(p, p.title())} for p in matched])

@app.route('/api/bowlers', methods=['GET'])
def search_bowlers():
    query = request.args.get('q', '').strip().lower()
    if not query or len(query) < 2:
        return jsonify([])
    matched = [b for b in all_bowlers if query in b][:10]
    return jsonify([{'id': b, 'display': name_map.get(b, b.title())} for b in matched])

@app.route('/api/compare', methods=['GET'])
def compare_players():
    names = request.args.getlist('players')
    season = request.args.get('season', 'all')

    if not names:
        return jsonify({'error': 'No players provided'}), 400
    if len(names) > 5:
        return jsonify({'error': 'Maximum 5 players allowed'}), 400

    results = get_multiple_batters(ipl_clean, names, season)
    if not results:
        return jsonify({'error': 'No players found'}), 404

    for r in results:
        r['display_name'] = name_map.get(r['name'], r['name'].title())

    results = add_percentiles(results, global_batter_stats)
    return jsonify(results)

@app.route('/api/compare_bowlers', methods=['GET'])
def compare_bowlers():
    names = request.args.getlist('bowlers')
    season = request.args.get('season', 'all')

    if not names:
        return jsonify({'error': 'No bowlers provided'}), 400
    if len(names) > 5:
        return jsonify({'error': 'Maximum 5 bowlers allowed'}), 400

    results = get_multiple_bowlers(ipl_clean, names, season)
    if not results:
        return jsonify({'error': 'No bowlers found'}), 404

    for r in results:
        r['display_name'] = name_map.get(r['name'], r['name'].title())

    results = add_bowler_percentiles(results, global_bowler_stats)
    return jsonify(results)

@app.route('/api/seasons', methods=['GET'])
def get_seasons():
    return jsonify([int(s) for s in all_seasons])

if __name__ == '__main__':
    app.run(debug=True)