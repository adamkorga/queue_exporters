import os
import time
import sys
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv
from requests_oauthlib import OAuth2Session
from bs4 import BeautifulSoup

# --- 1. CONFIG ---
load_dotenv()

CLIENT_ID = os.getenv('AWEBER_CLIENT_ID')
CLIENT_SECRET = os.getenv('AWEBER_CLIENT_SECRET')
REDIRECT_URI = os.getenv('AWEBER_REDIRECT_URI', 'https://localhost')

TOKEN_URL = "https://auth.aweber.com/oauth2/token"
AUTH_URL = "https://auth.aweber.com/oauth2/authorize"
API_BASE = "https://api.aweber.com/1.0"
SCOPES = ['account.read', 'list.read', 'email.read'] 

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(SCRIPT_DIR, 'aweber_token.json')
DATA_DIR = os.path.join(SCRIPT_DIR, os.getenv('DATA_DIR', './../data'))
DB_FILE = os.path.join(DATA_DIR, 'aweber_db.json')
MD_OUTPUT = os.path.join(DATA_DIR, 'aweber_export_llm.md')

os.makedirs(DATA_DIR, exist_ok=True)

# --- 2. HELPERS ---
def clean_html(html_content):
    if not html_content: return {"preview": "", "body": ""}
    soup = BeautifulSoup(html_content, 'html.parser')
    preview_text = ""
    meta_pre = soup.find('meta', attrs={'name': 'x-preheader'})
    if meta_pre and meta_pre.get('content'):
        preview_text = meta_pre.get('content').strip()
    for script in soup(["script", "style"]): script.extract()
    body_text = soup.get_text(separator='\n\n', strip=True)
    return {"preview": preview_text, "body": body_text}

def token_updater(token):
    """Callback dla OAuth2Session do automatycznego zapisu odświeżonego tokena."""
    with open(TOKEN_FILE, 'w') as f:
        json.dump(token, f)
    print("🔄 Token refreshed and saved to cache.")

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    return {"last_sync": "1970-01-01T00:00:00Z", "list_name": "Unknown", "messages": {}}

def save_md(db):
    # Generating Markdown (Full Detail)
    sorted_msgs = sorted(db['messages'].values(), key=lambda x: x['date'], reverse=True)
    
    print(f"📄 Writing {len(sorted_msgs)} messages to {MD_OUTPUT}...")
    with open(MD_OUTPUT, 'w', encoding='utf-8') as f:
        f.write(f"# AWeber Archive: {db.get('list_name', 'Adam Korga')}\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"Total messages: {len(sorted_msgs)}\n\n")

        for i, m in enumerate(sorted_msgs, 1):
            f.write(f"---\n")
            f.write(f"## {i}. {m['subject']}\n")
            f.write(f"- **Date:** {m['date']}\n")
            f.write(f"- **Status:** {m['status'].upper()}\n")
            
            # Display preview if exists
            if m.get('preview'):
                f.write(f"- **Preview:** *{m['preview']}*\n")
            
            f.write(f"\n### Content\n")
            # Adding indentation or quoting if you want the LLM to better see the structure
            f.write(f"{m['content']}\n\n")

    print("🎉 Markdown archive updated.")

# --- 3. MAIN ---
def main():
    parser = argparse.ArgumentParser(description="AWeber Auto-Refresh Dumper v2.1")
    parser.add_argument('--full', action='store_true')
    parser.add_argument('--from-date', help="YYYY-MM-DD")
    parser.add_argument('--to-date', help="YYYY-MM-DD")
    args = parser.parse_args()

    db = load_db()

    if args.full:
        print("⚠️  FULL mode: Backing up and clearing local database...")
        if os.path.exists(DB_FILE):
            os.rename(DB_FILE, f"{DB_FILE}.bak") # simple backup
        db['messages'] = {} 
        start_filter = "1970-01-01" # Ignoring dates, taking everything
    else:
        start_filter = args.from_date if args.from_date else db.get('last_sync')
    
    # Load token from file if exists
    token = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            token = json.load(f)

    # Initialize session with auto-refresh
    extra = {'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET}
    aweber = OAuth2Session(
        CLIENT_ID, 
        token=token, 
        auto_refresh_url=TOKEN_URL,
        auto_refresh_kwargs=extra,
        token_updater=token_updater,
        redirect_uri=REDIRECT_URI,
        scope=SCOPES
    )

    # If no token, we need to do this ONE LAST TIME manually
    if not token:
        authorization_url, _ = aweber.authorization_url(AUTH_URL)
        print(f"🔐 Initial Authorization Required:\n{authorization_url}")
        res = input("Paste redirect URL: ").strip()
        token = aweber.fetch_token(TOKEN_URL, client_secret=CLIENT_SECRET, authorization_response=res)
        token_updater(token)

    # Fetching logic (Simplified loop with handling for 401/403 errors)
    print("🔍 Fetching data...")
    acc_data = aweber.get(f"{API_BASE}/accounts").json()
    account = acc_data['entries'][0]
    list_data = aweber.get(account['lists_collection_link']).json()
    target_list = list_data['entries'][0]
    db['list_name'] = target_list['name']

    # Cleaning dynamic statuses
    db['messages'] = {mid: m for mid, m in db['messages'].items() if m['status'] == 'sent'}

    # Fetching: draft, scheduled, sent
    # TODO: draft messages aren't fetched correctly yet
    for status in ['draft', 'scheduled', 'sent']:
        print(f"📥 Checking {status}...")
        # Drafts are often in a different link in the API (as you noticed in the AWeber example)
        bc_url = target_list.get(f"{status}_broadcasts_link") or f"{API_BASE}/accounts/{account['id']}/lists/{target_list['id']}/broadcasts"
        
        # Loop through collection pages
        url = bc_url
        params = {'status': status} if 'broadcasts' in url and status != 'draft' else {}
        
        while url:
            resp = aweber.get(url, params=params if url == bc_url else None)
            if resp.status_code in [401, 403]:
                print(f"   ⚠️ Skipping {status}: Unauthorized (Labs Scope Issue).")
                break
            if resp.status_code != 200: break
            
            page = resp.json()
            for entry in page.get('entries', []):
                mid = str(entry.get('id') or entry.get('broadcast_id') or entry.get('draft_id'))
                mdate = entry.get('sent_at') or entry.get('scheduled_for') or entry.get('created_at') or "1970-01-01"
                
                if not args.full:
                    if status == 'sent' and not args.full and start_filter and mdate < start_filter:
                        continue
                    if mid in db['messages'] and db['messages'][mid]['status'] == 'sent':
                        continue

                print(f"   + Processing: {entry.get('subject', 'No Subject')[:40]}...")
                d = aweber.get(entry['self_link']).json()
                cleaned = clean_html(d.get('body_html'))
                db['messages'][mid] = {
                    'id': mid, 'subject': d.get('subject'), 'date': mdate,
                    'status': d.get('status') or status,
                    'preview': cleaned['preview'], 'content': cleaned['body']
                }
            url = page.get('next_collection_link')
            params = None

    # Saving DB and MD
    db['last_sync'] = datetime.now().isoformat() if not args.from_date else db['last_sync']
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)
    
    save_md(db)
    
    print("✅ Done!")

if __name__ == "__main__":
    main()