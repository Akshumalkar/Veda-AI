import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

CACHE_DIR = Path(__file__).resolve().parent.parent.parent / ".cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def compute_cache_key(question_bytes: bytes, answer_bytes: bytes) -> str:
    h1 = hashlib.sha256(question_bytes).hexdigest()
    h2 = hashlib.sha256(answer_bytes).hexdigest()
    return f"{h1[:16]}_{h2[:16]}"


def get_cached_result(cache_key: str) -> Optional[Dict[str, Any]]:
    cache_file = CACHE_DIR / f"{cache_key}.json"
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def set_cached_result(cache_key: str, data: Dict[str, Any]) -> None:
    cache_file = CACHE_DIR / f"{cache_key}.json"
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Warning: Failed to save cache: {e}")
