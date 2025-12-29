import os
import sys
import json
import requests
import argparse
import glob
import subprocess
from datetime import datetime

# Dodanie ../lib do ścieżki Pythona
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from lib.base_utils import get_platform_paths, load_db, save_all
from buffer_message import BufferMessage # Import lokalny z tego samego folderu

# --- CONFIG ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SENT_PATTERN = os.path.join(SCRIPT_DIR, 'raw_data_dumps','linkedIn-response.sent*.json')
QUEUE_PATTERN = os.path.join(SCRIPT_DIR, 'raw_data_dumps','linkedIn-response.queue*.json')

BASE_DATA_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..', 'data'))
PATHS = get_platform_paths("linkedin", BASE_DATA_DIR)

def download_data():
    """
    This requires headless browser to handle. 
    I might do it when I get tired of using dev tools but for now it is what it is.
    """
    pass

def download_image(url, media_dir, post_id, index):
    if not url: return None
    ext = ".jpg"
    if ".png" in url.lower(): ext = ".png"
    elif ".gif" in url.lower(): ext = ".gif"
    
    filename = f"{post_id}_{index}{ext}"
    local_path = os.path.join(media_dir, filename)
    if os.path.exists(local_path): return local_path

    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            with open(local_path, 'wb') as f:
                f.write(resp.content)
            return local_path
    except: return None
    return None

def parse_gql_file(filepath, status_fallback):
    if not os.path.exists(filepath):
        print(f"ℹ️ File not found: {os.path.basename(filepath)}")
        return {}
    
    print(f"📖 Loading file: {os.path.basename(filepath)}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            raw = json.load(f)
        except json.JSONDecodeError:
            print(f"❌ Error decoding JSON in {filepath}")
            return {}

    messages = {}
    edges = raw.get('data', {}).get('posts', {}).get('edges', [])
    
    for edge in edges:
        node = edge.get('node', {})
        mid = node.get('id')
        mdate = node.get('sentAt') or node.get('dueAt') or node.get('createdAt')
        text = node.get('text', "")
        
        print(f"   + Processing message: {mid[:10]}...")
        
        # Media & Metrics
        media_list = []
        for i, asset in enumerate(node.get('assets', [])):
            source_url = asset.get('source')
            if source_url:
                print(f"      ↓ Downloading image for message {mid[:10]} (asset {i})...")
                loc = download_image(source_url, PATHS['media'], mid, i)
                if loc: media_list.append({"type": "image", "url": loc})
        
        metrics = {m['type']: m['value'] for m in node.get('metrics', []) if m.get('value') is not None}
        
        link_att = None
        la = node.get('metadata', {}).get('linkAttachment')
        if la: link_att = {"url": la.get('url'), "title": la.get('title'), "text": la.get('text')}

        messages[mid] = BufferMessage(
            id=mid, date=mdate, status=node.get('status') or status_fallback,
            content=text, 
            subject=None,
            preview=None,
            metrics=metrics, link_attachment=link_att, media=media_list,
            source="buffer", subchannel="linkedin"
        )
        
    return messages

def compress_pdf(input_path, output_path):
    """Wywołuje Ghostscripta do kompresji pliku PDF."""
    print(f"🗜️  Compressing PDF using Ghostscript...")
    cmd = [
        "gs", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4",
        "-dPDFSETTINGS=/screen", "-dNOPAUSE", "-dQUIET", "-dBATCH",
        f"-sOutputFile={output_path}", input_path
    ]
    try:
        subprocess.run(cmd, check=True)
        # Usuwamy plik tymczasowy po udanej kompresji
        if input_path != output_path and os.path.exists(input_path):
            os.remove(input_path)
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Ghostscript failed: {e}")
    except FileNotFoundError:
        print("⚠️  Ghostscript (gs) not found in system. Compression skipped.")

def generate_pdf_archive(messages, output_path, title):
    """Generuje PDF z obsługą Unicode i automatyczną kompresją."""
    try:
        from fpdf import FPDF
        from fpdf.enums import XPos, YPos
    except ImportError:
        print("⚠️ fpdf2 not installed. Skipping PDF generation. (pip install fpdf2)")
        return

    # Tworzymy najpierw plik tymczasowy ("surowy")
    temp_pdf = output_path.replace(".pdf", ".raw.pdf")
    print(f"🎨 Rendering raw PDF: {os.path.basename(temp_pdf)}...")
    
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    font_variants = {
        "": "NotoSans-Regular.ttf",
        "B": "NotoSans-Bold.ttf",
        "I": "NotoSans-Italic.ttf",
        "BI": "NotoSans-BoldItalic.ttf"
    }
    
    loaded_styles = []
    has_unicode_font = False

    for search_dir in ["/usr/share/fonts/truetype/noto/", "/usr/share/fonts/noto/", SCRIPT_DIR, "./"]:
        reg_path = os.path.join(search_dir, font_variants[""])
        if os.path.exists(reg_path):
            for style, filename in font_variants.items():
                f_path = os.path.join(search_dir, filename)
                if os.path.exists(f_path):
                    pdf.add_font("NotoSans", style, f_path)
                    loaded_styles.append(style)
            has_unicode_font = True
            break

    def set_safe_font(style, size):
        if has_unicode_font:
            target_style = style if style in loaded_styles else ""
            pdf.set_font("NotoSans", target_style, size)
        else:
            pdf.set_font("Helvetica", style, size)

    pdf.add_page()
    set_safe_font("B", 16)
    pdf.cell(0, 10, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    set_safe_font("I", 10)
    pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(10)

    sorted_msgs = sorted(messages.values(), key=lambda x: x.date, reverse=True)

    for i, msg in enumerate(sorted_msgs, 1):
        set_safe_font("B", 12)
        pdf.cell(0, 10, f"{i}. Post from {msg.date} ({msg.status.upper()})", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        set_safe_font("", 10)
        
        # Uwaga: fpdf2 wyrzuci ostrzeżenia o brakujących glifach (emoji), 
        # ale wygeneruje tekst z kropkami/znakami zapytania zamiast nich.
        clean_text = msg.content if has_unicode_font else msg.content.encode('cp1250', 'replace').decode('cp1250')
        pdf.multi_cell(0, 5, clean_text)
        pdf.ln(2)
        
        for item in msg.media:
            if item['type'] == 'image' and os.path.exists(item['url']):
                try:
                    pdf.image(item['url'], x=10, w=150)
                    pdf.ln(5)
                except Exception as e:
                    set_safe_font("I", 8)
                    pdf.cell(0, 5, f"[Image error: {str(e)}]", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.ln(10)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

    pdf.output(temp_pdf)
    
    # Kompresja końcowa
    compress_pdf(temp_pdf, output_path)

def main():
    parser = argparse.ArgumentParser(description="Buffer/LinkedIn Local Parser")
    parser.add_argument('--full', action='store_true')
    parser.add_argument('--pdf', action='store_true', help="Generate compressed PDF archive")
    args = parser.parse_args()

    if args.full and os.path.exists(PATHS['db']):
        os.rename(PATHS['db'], f"{PATHS['db']}.bak")

    # 1. Ładowanie bazy za pomocą base_utils
    last_sync, list_name, messages = load_db(PATHS['db'], BufferMessage)
    
    # 2. Inkrementacja: zachowujemy tylko wysłane przed parsowaniem nowych zrzutów
    if not args.full:
        messages = {mid: m for mid, m in messages.items() if m.status == 'sent'}

    print("📥 Scanning for GQL dumps...")
    sent_files = sorted(glob.glob(SENT_PATTERN))
    queue_files = sorted(glob.glob(QUEUE_PATTERN))

    if not sent_files and not queue_files:
        print("⚠️ No input files found matching patterns.")
        if not messages: return

    for f in sent_files:
        messages.update(parse_gql_file(f, "sent"))
    for f in queue_files:
        messages.update(parse_gql_file(f, "scheduled"))

    # 3. Zapis wszystkiego (JSON + MD) jednym wywołaniem
    last_sync = datetime.now().isoformat()
    save_all(
        messages, 
        PATHS, 
        last_sync, 
        list_name="LinkedIn (Buffer)", 
        title="LinkedIn Archive"
    )
    
    # 4. Generacja i kompresja PDF
    if args.pdf:
        pdf_path = PATHS['export'].replace(".md", ".pdf")
        generate_pdf_archive(messages, pdf_path, "LinkedIn Archive (Adam Korga)")
    
    print(f"✅ Sync complete. Total messages in archive: {len(messages)}")

if __name__ == "__main__":
    main()