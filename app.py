from flask import Flask, redirect, url_for, session, render_template, request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong random secret for production

# Allows non-HTTPS for local testing
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Your credentials file path
CLIENT_SECRETS_FILE = "credentials.json"

# Gmail full access scope (allows delete)
SCOPES = ['https://mail.google.com/']



@app.route('/')
def index():
    return render_template('index.html')


@app.route('/authorize')
def authorize():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri='http://localhost:5000/oauth2callback'
    )
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes=False,  # force new token scope
        prompt='consent'               # always ask user again
    )
    session['state'] = state
    return redirect(authorization_url)


@app.route('/oauth2callback')
def oauth2callback():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri='http://localhost:5000/oauth2callback'
    )
    flow.fetch_token(authorization_response=request.url)

    credentials = flow.credentials
    print("🚨 Scopes granted:", credentials.scopes)  # DEBUG: see granted scopes

    service = build('gmail', 'v1', credentials=credentials)

    # Gmail search query: promotions older than 30 days
    query = 'category:promotions older_than:30d'
    result = service.users().messages().list(userId='me', q=query).execute()
    messages = result.get('messages', [])

    if not messages:
        return '✅ No promotional emails older than 30 days found.'

    # Delete each message
    for msg in messages:
        service.users().messages().delete(userId='me', id=msg['id']).execute()

    return f'✅ Gmail cleaned: {len(messages)} promotional emails older than 30 days deleted.'


if __name__ == '__main__':
    app.run(debug=True)
