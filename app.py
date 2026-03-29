from flask import Flask, render_template, request, redirect, url_for, flash, make_response
from supabase import create_client
import uuid

app = Flask(__name__)
app.secret_key = 'pollapp-secret-change-in-production'

SUPABASE_URL = "https://blknuzqewqbkmibhuciy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJsa251enFld3Fia21pYmh1Y2l5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3OTkzNjUsImV4cCI6MjA5MDM3NTM2NX0.pqcmN79Gp753XCtVG4KHQDuBSgEpbTq6Tj-dUCS4bo0"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_voter_token():
    token = request.cookies.get('voter_token')
    if not token:
        token = str(uuid.uuid4())
    return token


@app.route('/')
def index():
    polls = supabase.table("polls").select("*").execute().data
    return render_template('index.html', polls=polls)


@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        question = request.form.get('question', '').strip()
        options = [o.strip() for o in request.form.getlist('option') if o.strip()]

        if not question:
            flash('A question is required.', 'error')
            return render_template('create.html')

        if len(options) < 2:
            flash('Please provide at least 2 options.', 'error')
            return render_template('create.html')

        poll_id = str(uuid.uuid4())[:8]

        # Insert poll
        supabase.table("polls").insert({
            "id": poll_id,
            "question": question
        }).execute()

        # Insert options
        for opt in options:
            supabase.table("options").insert({
                "poll_id": poll_id,
                "text": opt,
                "votes": 0
            }).execute()

        flash('Poll created!', 'success')
        return redirect(url_for('poll', poll_id=poll_id))

    return render_template('create.html')


@app.route('/poll/<poll_id>', methods=['GET', 'POST'])
def poll(poll_id):
    voter_token = get_voter_token()

    # Get poll
    poll = supabase.table("polls").select("*").eq("id", poll_id).execute().data
    if not poll:
        flash('Poll not found.', 'error')
        return redirect(url_for('index'))

    poll = poll[0]

    # Get options
    options = supabase.table("options").select("*").eq("poll_id", poll_id).execute().data

    # Check if already voted
    vote = supabase.table("votes").select("*") \
        .eq("poll_id", poll_id) \
        .eq("voter_token", voter_token) \
        .execute().data

    already_voted = len(vote) > 0

    total_votes = sum(o['votes'] for o in options)

    if request.method == 'POST':
        if already_voted:
            flash("You've already voted.", 'error')
            return redirect(url_for('poll', poll_id=poll_id))

        option_id = request.form.get('option_id')
        if not option_id:
            flash('Select an option.', 'error')
            return redirect(url_for('poll', poll_id=poll_id))

        option_id = int(option_id)

        # Insert vote
        supabase.table("votes").insert({
            "poll_id": poll_id,
            "option_id": option_id,
            "voter_token": voter_token
        }).execute()

        # Get current votes
        opt = supabase.table("options").select("*").eq("id", option_id).execute().data[0]

        # Update votes
        supabase.table("options").update({
            "votes": opt["votes"] + 1
        }).eq("id", option_id).execute()

        resp = make_response(redirect(url_for('results', poll_id=poll_id)))
        resp.set_cookie('voter_token', voter_token, max_age=60*60*24*365)
        return resp

    resp = make_response(render_template(
        'poll.html',
        poll=poll,
        options=options,
        already_voted=already_voted,
        total_votes=total_votes
    ))

    resp.set_cookie('voter_token', voter_token, max_age=60*60*24*365)
    return resp


@app.route('/poll/<poll_id>/results')
def results(poll_id):
    voter_token = get_voter_token()

    poll = supabase.table("polls").select("*").eq("id", poll_id).execute().data
    if not poll:
        flash('Poll not found.', 'error')
        return redirect(url_for('index'))

    poll = poll[0]

    options = supabase.table("options") \
        .select("*") \
        .eq("poll_id", poll_id) \
        .order("votes", desc=True) \
        .execute().data

    vote = supabase.table("votes").select("*") \
        .eq("poll_id", poll_id) \
        .eq("voter_token", voter_token) \
        .execute().data

    my_vote_id = vote[0]['option_id'] if vote else None
    total_votes = sum(o['votes'] for o in options)

    resp = make_response(render_template(
        'results.html',
        poll=poll,
        options=options,
        total_votes=total_votes,
        my_vote_id=my_vote_id
    ))

    resp.set_cookie('voter_token', voter_token, max_age=60*60*24*365)
    return resp


@app.route('/poll/<poll_id>/delete', methods=['POST'])
def delete_poll(poll_id):
    supabase.table("votes").delete().eq("poll_id", poll_id).execute()
    supabase.table("options").delete().eq("poll_id", poll_id).execute()
    supabase.table("polls").delete().eq("id", poll_id).execute()

    flash('Poll deleted.', 'success')
    return redirect(url_for('index'))

app = app
