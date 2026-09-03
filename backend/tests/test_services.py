from app.services import build_system_prompt, summarize


def records(count=14):
    return [{"date": f"2026-08-{i + 1:02d}", "value": {"sleep_hours": 6 + i * 0.1, "exercise_minutes": 20 + i}, "memo": ""} for i in range(count)]


def test_empty_summary():
    result = summarize([])
    assert result["count"] == 0
    assert result["period"] is None


def test_health_summary_metrics_and_trend():
    result = summarize(records())
    assert result["count"] == 14
    assert result["period"] == "2026-08-01 ~ 2026-08-14"
    assert result["metrics"]["sleep_hours"]["average"] == 6.65
    assert result["trend"]["sleep"].startswith("증가")
    assert "권장 기준" in result["insight"]


def test_prompt_contains_context():
    prompt = build_system_prompt(summarize(records()))
    assert "사용자 건강 데이터 요약" in prompt
    assert "14개" in prompt
    assert "의료 진단" in prompt

