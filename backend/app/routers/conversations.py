from fastapi import APIRouter, Depends, HTTPException, status
from ..models import ConversationIn
from ..repository import FirestoreRepository
from .data import repo

router = APIRouter(prefix="/api/conversations", tags=["conversations"])

@router.post("", status_code=201)
def create_conversation(payload: ConversationIn, repository: FirestoreRepository = Depends(repo)): return repository.create_conversation(payload.model_dump())

@router.get("")
def list_conversations(repository: FirestoreRepository = Depends(repo)): return repository.list_conversations()

@router.get("/{conversation_id}")
def get_conversation(conversation_id: str, repository: FirestoreRepository = Depends(repo)):
    result = repository.get_conversation(conversation_id)
    if not result: raise HTTPException(404, "대화 기록을 찾을 수 없습니다.")
    return result

@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(conversation_id: str, repository: FirestoreRepository = Depends(repo)):
    if not repository.delete_conversation(conversation_id): raise HTTPException(404, "대화 기록을 찾을 수 없습니다.")

