import json, time
from pathlib import Path
from config import INDEX_FILE

def load_index():
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_index(idx):
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(idx, f, indent=2, ensure_ascii=False)

def add_files_for_link(mega_link, files):
    """
    files: list of dicts { 'local_path': str, 'size': int, 'name': str, 'mega_id': str (optional), 'mega_key': str (optional) }
    """
    idx = load_index()
    entry = {
        "link": mega_link,
        "added_at": int(time.time()),
        "files": files
    }
    idx.setdefault("links", []).append(entry)
    save_index(idx)
