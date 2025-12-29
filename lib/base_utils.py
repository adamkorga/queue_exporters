import os
import json
from datetime import datetime
from bs4 import BeautifulSoup

# --- PATH & DIRECTORY MANAGEMENT ---

def get_platform_paths(platform_name, base_data_dir):
    """Tworzy ustandaryzowaną strukturę ścieżek dla platformy."""
    platform_dir = os.path.abspath(os.path.join(base_data_dir, platform_name))
    media_dir = os.path.join(platform_dir, "media")
    os.makedirs(media_dir, exist_ok=True)
    
    return {
        "base": platform_dir,
        "db": os.path.join(platform_dir, f"{platform_name}_db.json"),
        "export": os.path.join(platform_dir, f"{platform_name}_export_llm.md"),
        "media": media_dir
    }

# --- DB PERSISTENCE ---

def load_db(db_path, message_class):
    """Wczytuje JSON i zwraca metadane oraz słownik obiektów danej klasy."""
    if not os.path.exists(db_path):
        return "1970-01-01T00:00:00Z", "Unknown", {}

    with open(db_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    last_sync = data.get("last_sync", "1970-01-01T00:00:00Z")
    list_name = data.get("list_name", "Unknown")
    # Rekonstrukcja obiektów
    messages = {mid: message_class.from_dict(m) for mid, m in data.get("messages", {}).items()}
    
    return last_sync, list_name, messages

def save_all(message_objects_dict, paths, last_sync, list_name, title="Archive"):
    """Zapisuje bazę JSON oraz generuje Markdown w jednym kroku."""
    
    # 1. Zapis JSON (Serializacja obiektów)
    db_data = {
        "last_sync": last_sync,
        "list_name": list_name,
        "messages": {mid: m.to_dict() for mid, m in message_objects_dict.items()}
    }
    
    with open(paths['db'], 'w', encoding='utf-8') as f:
        json.dump(db_data, f, indent=2, ensure_ascii=False)
    
    # 2. Zapis Markdown (Rendering)
    sorted_msgs = sorted(message_objects_dict.values(), key=lambda x: x.date, reverse=True)
    
    print(f"📄 Writing {len(sorted_msgs)} items to {paths['export']}...")
    with open(paths['export'], 'w', encoding='utf-8') as f:
        f.write(f"# {title}: {list_name}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for i, msg in enumerate(sorted_msgs, 1):
            f.write(msg.to_markdown(i, media_base_path=paths.get('media')))
                
    print(f"✅ Persistence complete (JSON + MD).")

# --- HTML PROCESSING ---

def clean_html_content(html_content):
    if not html_content: return {"preview": "", "body": ""}
    soup = BeautifulSoup(html_content, 'html.parser')
    preview_text = ""
    meta_pre = soup.find('meta', attrs={'name': 'x-preheader'})
    if meta_pre and meta_pre.get('content'):
        preview_text = meta_pre.get('content').strip()
    for script in soup(["script", "style"]): script.extract()
    body_text = soup.get_text(separator='\n\n', strip=True)
    return {"preview": preview_text, "body": body_text}