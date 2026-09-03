from fastapi import APIRouter, Depends, HTTPException
from ..models import ChatRequest
from ..repository import FirestoreRepository
from ..services import ask_ai, summarize
from .data import repo

router = APIRouter(prefix="/api/chat", tags=["AI chat"])

@router.post("")
def chat(payload: ChatRequest, repository: FirestoreRepository = Depends(repo)):
    conversation = repository.get_conversation(payload.conversation_id) if payload.conversation_id else None
    messages = conversation.get("messages", []) if conversation else []
    messages.append({"role": "user", "content": payload.message})
    summary = summarize(repository.list_data())
    try: answer = ask_ai(messages, summary)
    except Exception as exc: raise HTTPException(502, f"AI 응답 생성에 실패했습니다: {exc}") from exc
    messages.append({"role": "assistant", "content": answer})
    saved = repository.create_conversation({"title": conversation.get("title") if conversation else payload.message[:36], "messages": messages}, payload.conversation_id if conversation else None)
    return {"answer": answer, "conversation_id": saved["id"], "summary_used": summary}

