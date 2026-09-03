from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import allowed_origins
from .routers import chat, conversations, data

app = FastAPI(title="Balance AI 건강관리 API", version="1.0.0", description="수면·운동 시계열 데이터 기반 맞춤 건강 코칭 API")
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins(), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(data.router); app.include_router(conversations.router); app.include_router(chat.router)

@app.get("/", tags=["system"])
def health_check(): return {"status": "ok", "service": "Balance AI"}

