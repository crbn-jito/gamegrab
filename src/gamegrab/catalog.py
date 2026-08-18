from pathlib import Path
import json
from typing import List, Optional, Dict

class Catalog:
    def __init__(self, path: Path):
        self.path = path

    def init_catalog(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump({"next_id": 1, "entries": []}, f, indent=2)

    def _load(self):
        if not self.path.exists():
            self.init_catalog()
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def add(self, title: str, url: str, sha256: Optional[str] = None) -> Dict:
        data = self._load()
        entry = {"id": data["next_id"], "title": title, "url": url}
        if sha256:
            entry["sha256"] = sha256
        data["entries"].append(entry)
        data["next_id"] += 1
        self._save(data)
        return entry

    def list(self) -> List[Dict]:
        data = self._load()
        return data["entries"]

    def get(self, id: int) -> Optional[Dict]:
        entries = self.list()
        for e in entries:
            if e["id"] == id:
                return e
        return None
