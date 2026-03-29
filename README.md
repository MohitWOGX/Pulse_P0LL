# 🗳️ Pulse — Poll / Voting App

A bold, shareable polling app built with Flask and SQLite. Create a poll, share the link, watch votes come in.

## Features
- ✏️ Create polls with a question and 2–8 options (dynamic form)
- 🗳️ Vote once per browser (cookie-based deduplication)
- 📊 Animated results bar chart on the results page
- 🔗 Shareable poll URL with one-click copy
- 🏆 "Leading" winner callout on results
- 🔍 See your own vote highlighted in results
- 🗑️ Delete polls
- All polls listed on homepage with vote counts

## Setup & Run

```bash
pip install -r requirements.txt
python app.py
# → http://localhost:5000
```

The `polls.db` SQLite database is created automatically.

## Project Structure

```
pollapp/
├── app.py                # Flask routes + SQLite logic
├── requirements.txt
├── polls.db              # Auto-created
├── templates/
│   ├── base.html         # Layout, navbar, flash
│   ├── index.html        # All polls homepage
│   ├── create.html       # Create new poll form
│   ├── poll.html         # Vote page
│   └── results.html      # Results with bar chart
└── static/
    ├── css/style.css     # Neon brutalist design
    └── js/app.js         # Dynamic options, bars, copy
```

## Routes

| Route                   | Method    | Description               |
|-------------------------|-----------|---------------------------|
| `/`                     | GET       | Homepage — all polls      |
| `/create`               | GET, POST | Create poll               |
| `/poll/<id>`            | GET, POST | View & vote on poll       |
| `/poll/<id>/results`    | GET       | Results with bar chart    |
| `/poll/<id>/delete`     | POST      | Delete poll               |

## How Vote Deduplication Works
Each browser gets a `voter_token` UUID stored in a cookie (1-year expiry). Votes are stored with `UNIQUE(poll_id, voter_token)` in the database, preventing double-voting per browser. This is lightweight and shareable-friendly — no accounts needed.
