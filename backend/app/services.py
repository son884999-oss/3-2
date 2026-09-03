import os
from statistics import mean
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()


def _direction(recent: float, previous: float, unit: str) -> str:
    change = recent - previous
    threshold = 0.15 if unit == "시간" else 3
    label = "증가" if change > threshold else "감소" if change < -threshold else "유지"
    return f"{label} ({change:+.1f}{unit})"


def summarize(records: list[dict]) -> dict:
    if not records:
        return {"period": None, "count": 0, "metrics": {}, "trend": {"sleep": "데이터 없음", "exercise": "데이터 없음"}, "insight": "건강 기록을 추가해 주세요."}
    ordered = sorted(records, key=lambda row: row["date"])
    sleeps = [float(row["value"]["sleep_hours"]) for row in ordered]
    exercises = [int(row["value"]["exercise_minutes"]) for row in ordered]
    split = min(7, max(1, len(ordered) // 2))
    prev_s, recent_s = sleeps[-split * 2:-split] or sleeps[:split], sleeps[-split:]
    prev_e, recent_e = exercises[-split * 2:-split] or exercises[:split], exercises[-split:]
    avg_sleep, avg_exercise = mean(sleeps), mean(exercises)
    healthy_days = sum(1 for s, e in zip(sleeps, exercises) if 7 <= s <= 9 and e >= 30)
    return {"period": f"{ordered[0]['date']} ~ {ordered[-1]['date']}", "count": len(ordered),
        "metrics": {"sleep_hours": {"average": round(avg_sleep, 2), "max": max(sleeps), "min": min(sleeps)}, "exercise_minutes": {"average": round(avg_exercise, 1), "max": max(exercises), "min": min(exercises), "total": sum(exercises)}, "healthy_days": healthy_days, "healthy_day_rate": round(healthy_days / len(ordered) * 100, 1)},
        "trend": {"sleep": _direction(mean(recent_s), mean(prev_s), "시간"), "exercise": _direction(mean(recent_e), mean(prev_e), "분")},
        "insight": f"평균 수면 {avg_sleep:.1f}시간, 평균 운동 {avg_exercise:.0f}분이며 권장 기준을 함께 충족한 날은 {healthy_days}일입니다."}


def build_system_prompt(summary: dict) -> str:
    return f"""당신은 사용자의 수면과 운동 기록을 이해하는 친절한 건강관리 AI 코치입니다.
[사용자 건강 데이터 요약]
- 기간: {summary['period']} / 기록: {summary['count']}개
- 지표: {summary['metrics']}
- 최근 7일 추세: {summary['trend']}
- 인사이트: {summary['insight']}
위 데이터에 근거해 수치를 인용하고 모르는 내용은 추측하지 마세요. 의료 진단을 내리지 말고 이상 증상은 의료진 상담을 권하세요. 한국어로 간결하고 실행 가능하게 답하세요."""


def ask_ai(messages: list[dict], summary: dict) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY가 설정되지 않았습니다.")

    # Firestore의 assistant 역할을 Gemini 대화 형식의 model 역할로 변환한다.
    contents = [
        types.Content(
            role="model" if message["role"] == "assistant" else "user",
            parts=[types.Part(text=message["content"])],
        )
        for message in messages[-12:]
    ]
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=build_system_prompt(summary),
            max_output_tokens=500,
        ),
    )
    if not response.text:
        raise RuntimeError("Gemini가 비어 있는 응답을 반환했습니다.")
    return response.text
