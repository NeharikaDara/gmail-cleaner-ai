from flask import Flask, redirect, url_for, session, request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "fallback_secret")

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def build_client_config():
    base_url = os.getenv("BASE_URL", "http://localhost:10000")  # fallback if env not set
    return {
        "web": {
            "client_id": CLIENT_ID,
            "project_id": "gmail-cleaner-ai",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": CLIENT_SECRET,
            "redirect_uris": [f"{base_url}/callback"],
            "javascript_origins": [base_url]
        }
    }

@app.route("/")
def home():
    return "<h2>Welcome to Gmail Cleaner AI</h2><br><a href='/login'>Login with Google</a>"

@app.route("/login")
def login():
    flow = Flow.from_client_config(
        build_client_config(),
        scopes=SCOPES,
        redirect_uri=f"{os.getenv('BASE_URL')}/callback"
    )
    auth_url, _ = flow.authorization_url(prompt='consent')
    return redirect(auth_url)

@app.route("/callback")
def callback():
    flow = Flow.from_client_config(
        build_client_config(),
        scopes=SCOPES,
        redirect_uri=f"{os.getenv('BASE_URL')}/callback"
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

    query = "label:promotions older_than:30d"
    results = service.users().messages().list(userId='me', q=query).execute()
    messages = results.get('messages', [])

    count = 0
    for msg in messages:
        service.users().messages().delete(userId='me', id=msg['id']).execute()
        count += 1

    return f"<h3>✅ Deleted {count} unwanted Gmail messages!</h3><br><a href='/'>Back to Home</a>"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))




