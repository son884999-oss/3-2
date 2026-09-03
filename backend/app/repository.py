from datetime import date, datetime, timezone
from typing import Any

from google.cloud.firestore_v1.base_query import FieldFilter

from .config import get_db


def _serialize(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    return value


class FirestoreRepository:
    def __init__(self):
        self.db = get_db()

    def list_data(self) -> list[dict]:
        docs = self.db.collection("data").order_by("date").stream()
        return [{"id": doc.id, **_serialize(doc.to_dict())} for doc in docs]

    def create_data(self, payload: dict) -> dict:
        payload = _serialize(payload)
        ref = self.db.collection("data").document()
        ref.set({**payload, "created_at": datetime.now(timezone.utc)})
        return {"id": ref.id, **payload}

    def update_data(self, record_id: str, payload: dict) -> dict | None:
        ref = self.db.collection("data").document(record_id)
        if not ref.get().exists:
            return None
        payload = _serialize(payload)
        ref.update({**payload, "updated_at": datetime.now(timezone.utc)})
        return {"id": record_id, **payload}

    def delete_data(self, record_id: str) -> bool:
        ref = self.db.collection("data").document(record_id)
        if not ref.get().exists:
            return False
        ref.delete()
        return True

    def data_date_exists(self, value: str) -> bool:
        query = self.db.collection("data").where(filter=FieldFilter("date", "==", value)).limit(1)
        return next(query.stream(), None) is not None

    def create_conversation(self, payload: dict, conversation_id: str | None = None) -> dict:
        ref = self.db.collection("conversations").document(conversation_id) if conversation_id else self.db.collection("conversations").document()
        now = datetime.now(timezone.utc)
        current = ref.get()
        created_at = current.to_dict().get("created_at", now) if current.exists else now
        ref.set({**_serialize(payload), "created_at": created_at, "updated_at": now})
        return {"id": ref.id, **_serialize(payload), "created_at": _serialize(created_at), "updated_at": now.isoformat()}

    def list_conversations(self) -> list[dict]:
        docs = self.db.collection("conversations").order_by("updated_at", direction="DESCENDING").stream()
        return [{"id": doc.id, **_serialize(doc.to_dict())} for doc in docs]

    def get_conversation(self, conversation_id: str) -> dict | None:
        doc = self.db.collection("conversations").document(conversation_id).get()
        return {"id": doc.id, **_serialize(doc.to_dict())} if doc.exists else None

    def delete_conversation(self, conversation_id: str) -> bool:
        ref = self.db.collection("conversations").document(conversation_id)
        if not ref.get().exists:
            return False
        ref.delete()
        return True

