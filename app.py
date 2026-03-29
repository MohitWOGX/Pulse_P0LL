from flask import Flask, render_template, request, redirect, url_for, flash, make_response
import sqlite3
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'pollapp-secret-change-in-production'
DATABASE = '/tmp/polls.db'   # IMPORTANT for Vercel
@app.before_request
def initialize_database():
    init_db()

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS polls (
                id TEXT PRIMARY KEY,
                question TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS options (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                poll_id TEXT NOT NULL,
                text TEXT NOT NULL,
                votes INTEGER DEFAULT 0,
                FOREIGN KEY (poll_id) REFERENCES polls(id)
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                poll_id TEXT NOT NULL,
                option_id INTEGER NOT NULL,
                voter_token TEXT NOT NULL,
                voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(poll_id, voter_token)
            )
        ''')
        conn.commit()


def get_voter_token(response=None):
    """Get or create a persistent voter token via cookie."""
    token = request.cookies.get('voter_token')
    if not token:
        token = str(uuid.uuid4())
    return token


@app.route('/')
def index():
    with get_db() as conn:
        polls = conn.execute('''
            SELECT p.*, COUNT(o.id) as option_count,
                   COALESCE(SUM(o.votes), 0) as total_votes
            FROM polls p
            LEFT JOIN options o ON o.poll_id = p.id
            GROUP BY p.id
            ORDER BY p.created_at DESC
        ''').fetchall()
    return render_template('index.html', polls=polls)


@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        question = request.form.get('question', '').strip()
        options  = [o.strip() for o in request.form.getlist('option') if o.strip()]

        if not question:
            flash('A question is required.', 'error')
            return render_template('create.html')
        if len(options) < 2:
            flash('Please provide at least 2 options.', 'error')
            return render_template('create.html')
        if len(options) > 8:
            flash('Maximum 8 options allowed.', 'error')
            return render_template('create.html')

        poll_id = str(uuid.uuid4())[:8]
        with get_db() as conn:
            conn.execute('INSERT INTO polls (id, question) VALUES (?, ?)', (poll_id, question))
            for opt in options:
                conn.execute('INSERT INTO options (poll_id, text) VALUES (?, ?)', (poll_id, opt))
            conn.commit()

        flash('Poll created! Share the link below.', 'success')
        return redirect(url_for('poll', poll_id=poll_id))

    return render_template('create.html')


@app.route('/poll/<poll_id>', methods=['GET', 'POST'])
def poll(poll_id):
    voter_token = get_voter_token()

    with get_db() as conn:
        p = conn.execute('SELECT * FROM polls WHERE id=?', (poll_id,)).fetchone()
        if not p:
            flash('Poll not found.', 'error')
            return redirect(url_for('index'))

        options = conn.execute(
            'SELECT * FROM options WHERE poll_id=? ORDER BY id', (poll_id,)
        ).fetchall()

        already_voted = conn.execute(
            'SELECT option_id FROM votes WHERE poll_id=? AND voter_token=?',
            (poll_id, voter_token)
        ).fetchone()

        total_votes = sum(o['votes'] for o in options)

    if request.method == 'POST':
        if already_voted:
            flash("You've already voted on this poll.", 'error')
            return redirect(url_for('poll', poll_id=poll_id))

        option_id = request.form.get('option_id')
        if not option_id:
            flash('Please select an option.', 'error')
            return render_template('poll.html', poll=p, options=options,
                                   already_voted=already_voted, total_votes=total_votes,
                                   voted_option_id=None)

        with get_db() as conn:
            conn.execute(
                'INSERT INTO votes (poll_id, option_id, voter_token) VALUES (?, ?, ?)',
                (poll_id, int(option_id), voter_token)
            )
            conn.execute(
                'UPDATE options SET votes = votes + 1 WHERE id=? AND poll_id=?',
                (int(option_id), poll_id)
            )
            conn.commit()

        resp = make_response(redirect(url_for('results', poll_id=poll_id)))
        resp.set_cookie('voter_token', voter_token, max_age=60*60*24*365)
        return resp

    voted_option_id = already_voted['option_id'] if already_voted else None
    show_results = already_voted is not None

    resp = make_response(render_template('poll.html', poll=p, options=options,
                                          already_voted=already_voted,
                                          total_votes=total_votes,
                                          voted_option_id=voted_option_id,
                                          show_results=show_results))
    resp.set_cookie('voter_token', voter_token, max_age=60*60*24*365)
    return resp


@app.route('/poll/<poll_id>/results')
def results(poll_id):
    voter_token = get_voter_token()
    with get_db() as conn:
        p = conn.execute('SELECT * FROM polls WHERE id=?', (poll_id,)).fetchone()
        if not p:
            flash('Poll not found.', 'error')
            return redirect(url_for('index'))

        options = conn.execute(
            'SELECT * FROM options WHERE poll_id=? ORDER BY votes DESC', (poll_id,)
        ).fetchall()

        my_vote = conn.execute(
            'SELECT option_id FROM votes WHERE poll_id=? AND voter_token=?',
            (poll_id, voter_token)
        ).fetchone()

        total_votes = sum(o['votes'] for o in options)

    resp = make_response(render_template('results.html', poll=p, options=options,
                                          total_votes=total_votes,
                                          my_vote_id=my_vote['option_id'] if my_vote else None))
    resp.set_cookie('voter_token', voter_token, max_age=60*60*24*365)
    return resp


@app.route('/poll/<poll_id>/delete', methods=['POST'])
def delete_poll(poll_id):
    with get_db() as conn:
        conn.execute('DELETE FROM votes WHERE poll_id=?', (poll_id,))
        conn.execute('DELETE FROM options WHERE poll_id=?', (poll_id,))
        conn.execute('DELETE FROM polls WHERE id=?', (poll_id,))
        conn.commit()
    flash('Poll deleted.', 'success')
    return redirect(url_for('index'))


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
