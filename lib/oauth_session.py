from requests_oauthlib import OAuth2Session
import json
import os

# --- OAUTH2 SESSION MANAGEMENT ---
def setup_oauth_session(client_id, client_secret, token_file, auth_url, token_url, redirect_uri, scopes):
    """
    Manages the full OAuth2 session lifecycle: loading, authorization, and auto-refresh.
    """
    
    def token_updater(token):
        with open(token_file, 'w') as f:
            json.dump(token, f)
        print(f"🔄 Token refreshed and saved to {os.path.basename(token_file)}")

    token = None
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            token = json.load(f)

    # Parameters for auto-refresh (required by some OAuth2 implementations)
    extra = {'client_id': client_id, 'client_secret': client_secret}
    
    session = OAuth2Session(
        client_id, 
        token=token, 
        auto_refresh_url=token_url,
        auto_refresh_kwargs=extra,
        token_updater=token_updater,
        redirect_uri=redirect_uri,
        scope=scopes
    )

    # Initial authorization if no token or token is completely invalid
    if not token:
        authorization_url, _ = session.authorization_url(auth_url)
        print(f"🔐 Initial Authorization Required:\n{authorization_url}")
        res = input("Paste redirect URL: ").strip()
        token = session.fetch_token(token_url, client_secret=client_secret, authorization_response=res)
        token_updater(token)
        
    return session