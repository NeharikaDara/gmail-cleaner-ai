from flask import Flask, redirect, url_for, session, request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os

app = Flask(__name__)
app.secret_key = "any_random_secret"  # can be anything

# Load environment variables (you'll set these on Render later)
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")





SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

# Google OAuth config
CLIENT_CONFIG = {
    "web": {
        "client_id": CLIENT_ID,
        "project_id": "gmail-cleaner-ai",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": CLIENT_SECRET,
        "redirect_uris": ["http://localhost:5000/callback"],
        "javascript_origins": ["http://localhost:5000"]
    }
}




@app.route("/")
def home():
    return "<h2>Welcome to Gmail Cleaner AI</h2><br><a href='/login'>Login with Google</a>"


@app.route("/login")
def login():
    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri="http://localhost:5000/callback"
    )
    auth_url, _ = flow.authorization_url(prompt='consent')
    return redirect(auth_url)  # ✅ that's it!



@app.route("/callback")
def callback():
    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri="http://localhost:5000/callback"
    )
    flow.fetch_token(authorization_response=request.url)

    credentials = flow.credentials
    session['creds'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    return redirect("/clean")



@app.route("/clean")
def clean():
    creds_dict = session.get("creds")
    creds = Credentials(**creds_dict)
    service = build('gmail', 'v1', credentials=creds)

    # Query: Delete promotional emails older than 30 days
    query = "label:promotions older_than:30d"
    results = service.users().messages().list(userId='me', q=query).execute()
    messages = results.get('messages', [])

    count = 0
    for msg in messages:
        service.users().messages().delete(userId='me', id=msg['id']).execute()
        count += 1

    return f"<h3>✅ Deleted {count} unwanted Gmail messages!</h3><br><a href='/'>Back to Home</a>"


if __name__ == '__main__':
    app.run(debug=True)


