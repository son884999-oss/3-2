import csv
import io
import random
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Response, status
from ..models import HealthRecord, HealthRecordIn
from ..repository import FirestoreRepository
from ..services import summarize

router = APIRouter(prefix="/api/data", tags=["health data"])
def repo() -> FirestoreRepository: return FirestoreRepository()

@router.get("/summary")
def get_summary(repository: FirestoreRepository = Depends(repo)): return summarize(repository.list_data())

@router.get("/export.csv")
def export_csv(repository: FirestoreRepository = Depends(repo)):
    output = io.StringIO(); writer = csv.writer(output); writer.writerow(["date", "sleep_hours", "exercise_minutes", "memo"])
    for row in repository.list_data(): writer.writerow([row["date"], row["value"]["sleep_hours"], row["value"]["exercise_minutes"], row.get("memo", "")])
    return Response("\ufeff" + output.getvalue(), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": "attachment; filename=health-data.csv"})

@router.post("/seed", status_code=201)
def seed_demo_data(repository: FirestoreRepository = Depends(repo)):
    rng = random.Random(20260903); start = date.today() - timedelta(days=119); created = 0
    memos = ["컨디션 좋음", "야근", "산책", "근력 운동", "휴식", "스트레칭"]
    for index in range(120):
        day = start + timedelta(days=index); day_text = day.isoformat()
        if repository.data_date_exists(day_text): continue
        sleep = round(max(4.5, min(9.5, 6.5 + index * .006 + (.45 if day.weekday() >= 5 else 0) + rng.uniform(-1.1, 1.1))), 1)
        exercise = max(0, min(120, round(24 + index * .08 + (18 if day.weekday() >= 5 else 0) + rng.uniform(-22, 25))))
        repository.create_data({"date": day_text, "value": {"sleep_hours": sleep, "exercise_minutes": exercise}, "memo": rng.choice(memos)}); created += 1
    return {"created": created, "message": f"가상 건강 기록 {created}건을 추가했습니다."}

@router.post("", response_model=HealthRecord, status_code=201)
def create_data(payload: HealthRecordIn, repository: FirestoreRepository = Depends(repo)):
    if repository.data_date_exists(payload.date.isoformat()): raise HTTPException(409, "해당 날짜의 기록이 이미 있습니다.")
    return repository.create_data(payload.model_dump())

@router.get("", response_model=list[HealthRecord])
def list_data(repository: FirestoreRepository = Depends(repo)): return repository.list_data()

@router.put("/{record_id}", response_model=HealthRecord)
def update_data(record_id: str, payload: HealthRecordIn, repository: FirestoreRepository = Depends(repo)):
    result = repository.update_data(record_id, payload.model_dump())
    if not result: raise HTTPException(404, "건강 기록을 찾을 수 없습니다.")
    return result

@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_data(record_id: str, repository: FirestoreRepository = Depends(repo)):
    if not repository.delete_data(record_id): raise HTTPException(404, "건강 기록을 찾을 수 없습니다.")

