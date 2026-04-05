# CricmB

IPL player comparison tool built on ball-by-ball match data. The idea came from a simple frustration — overall stats like career average or total runs don't tell you much about how a player actually performs in different situations.

CricmB converts raw ball-by-ball data into percentile scores across specific skill areas, so comparing two players is visual and immediate rather than a manual exercise in reading stat tables.

**Live:** https://cricmb.onrender.com


## How it works

Every player gets a percentile score for each skill - calculated against all IPL players in the dataset. A score of 80 means the player performs better than 80% of IPL players in that area.

This makes comparison straightforward. You're not reading raw numbers, you're seeing relative strength across skills on a single chart.


## Skills tracked

**Batters**
- Total runs
- Strike rate
- Dot ball percentage
- Boundary hitting rate
- Performance vs spin
- Performance vs pace
- Powerplay scoring
- Death overs scoring

**Bowlers**
- Economy rate
- Dot ball percentage
- Wickets taken
- Bowling strike rate
- Death overs economy
- Performance vs right-hand batters
- Performance vs left-hand batters


## Visualization

Performance is displayed as a radar (spider) chart. Each axis is one skill area. Two players plotted on the same chart makes strengths and gaps immediately visible without reading any numbers.

![Batter Comparison](docs/Batter_comparison.png)

![Bowler Comparison](docs/Bowler_comparison.png)


## Tech stack

Python, Streamlit, PostgreSQL, Pandas, Plotly

Ball-by-ball IPL dataset - also used as the test database for [AskDB](https://github.com/Ardent-7322/AskDB-AI-Query-Assistant), a natural language query tool that connects directly to this PostgreSQL database.


## Running locally

```bash
git clone https://github.com/Ardent-7322/CricMB
cd CricMB
pip install -r requirements.txt
streamlit run app.py
```

Needs a PostgreSQL connection with the IPL dataset loaded. Connection details go in `.env`.
