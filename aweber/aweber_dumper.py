import os
import sys
import argparse
import json
from datetime import datetime
from dotenv import load_dotenv

# Add ../lib to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from lib.base_utils import get_platform_paths, clean_html_content, load_db, save_all
from lib.oauth_session import setup_oauth_session
from lib.message_model import BaseMessage

# --- 1. CONFIG & PATHS ---
load_dotenv()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DATA_DIR = os.path.join(SCRIPT_DIR, os.getenv('DATA_DIR', './../data'))
PATHS = get_platform_paths("aweber", BASE_DATA_DIR)
TOKEN_FILE = os.path.join(SCRIPT_DIR, 'aweber_token.json')

def main():
    parser = argparse.ArgumentParser(description="AWeber Exporter v2.8 (Ultra-Clean)")
    parser.add_argument('--full', action='store_true')
    parser.add_argument('--from-date', help="YYYY-MM-DD")
    args = parser.parse_args()

    # --- 2. DB SETUP ---
    if args.full and os.path.exists(PATHS['db']):
        os.rename(PATHS['db'], f"{PATHS['db']}.bak")
    
    # Load existing data from local DB file (if exists)
    last_sync, list_name, messages = load_db(PATHS['db'], BaseMessage)
    start_filter = args.from_date if args.from_date else last_sync

    # --- 3. OAUTH SESSION ---
    aweber = setup_oauth_session(
        client_id=os.getenv('AWEBER_CLIENT_ID'),
        client_secret=os.getenv('AWEBER_CLIENT_SECRET'),
        token_file=TOKEN_FILE,
        auth_url="https://auth.aweber.com/oauth2/authorize",
        token_url="https://auth.aweber.com/oauth2/token",
        redirect_uri=os.getenv('AWEBER_REDIRECT_URI', 'https://localhost'),
        scopes=['account.read', 'list.read', 'email.read']
    )

    # --- 4. API LOGIC ---
    print(f"🔍 Syncing AWeber...")
    acc_data = aweber.get("https://api.aweber.com/1.0/accounts").json()
    account = acc_data['entries'][0]
    list_data = aweber.get(account['lists_collection_link']).json()
    target_list = list_data['entries'][0]
    list_name = target_list['name']

    # Clean drafts/scheduled, keep only certain 'sent'
    if not args.full:
        messages = {mid: m for mid, m in messages.items() if m.status == 'sent'}

    for status in ['draft', 'scheduled', 'sent']:
        print(f"📥 Checking {status}...")
        bc_url = target_list.get(f"{status}_broadcasts_link") or f"https://api.aweber.com/1.0/accounts/{account['id']}/lists/{target_list['id']}/broadcasts"
        
        url = bc_url
        params = {'status': status} if 'broadcasts' in url and status != 'draft' else {}
        
        while url:
            resp = aweber.get(url, params=params if url == bc_url else None)
            if resp.status_code != 200: break
            
            page = resp.json()
            for entry in page.get('entries', []):
                mid = str(entry.get('id') or entry.get('broadcast_id') or entry.get('draft_id'))
                mdate = entry.get('sent_at') or entry.get('scheduled_for') or entry.get('created_at') or "1970-01-01"
                
                if not args.full:
                    if status == 'sent' and mdate < start_filter: continue
                    if mid in messages and messages[mid].status == 'sent': continue

                print(f"   + Processing: {entry.get('subject', 'No Subject')[:40]}...")
                d_resp = aweber.get(entry['self_link'])
                if d_resp.status_code != 200: continue
                
                d = d_resp.json()
                cleaned = clean_html_content(d.get('body_html'))
                
                messages[mid] = BaseMessage(
                    id=mid, date=mdate, status=d.get('status') or status,
                    content=cleaned['body'], subject=d.get('subject'),
                    preview=cleaned['preview'], source='aweber', subchannel='newsletter'
                )
            url = page.get('next_collection_link')

    # --- 5. SAVE ---
    last_sync = datetime.now().isoformat()
    save_all(messages, PATHS, last_sync, list_name, title="AWeber Archive")
    print("✅ Done!")

if __name__ == "__main__":
    main()