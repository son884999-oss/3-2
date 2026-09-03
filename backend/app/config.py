import json
import os
from functools import lru_cache
from pathlib import Path

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials, firestore

load_dotenv()


def allowed_origins() -> list[str]:
    raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500")
    return [item.strip().rstrip("/") for item in raw.split(",") if item.strip()]


@lru_cache
def get_db():
    if not firebase_admin._apps:
        raw = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
        path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
        if raw:
            cred = credentials.Certificate(json.loads(raw))
        elif path:
            cred = credentials.Certificate(str(Path(path).expanduser()))
        else:
            raise RuntimeError("Firebase 서비스 계정 환경 변수가 설정되지 않았습니다.")
        firebase_admin.initialize_app(cred)
    return firestore.client()

