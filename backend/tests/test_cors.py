from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_vercel_preview_origin_is_allowed():
    origin = "https://3-2-git-main-son884999-oss-projects.vercel.app"
    response = client.options(
        "/api/data",
        headers={"Origin": origin, "Access-Control-Request-Method": "GET"},
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin


def test_unrelated_vercel_team_is_rejected():
    response = client.options(
        "/api/data",
        headers={
            "Origin": "https://3-2-git-main-other-team.vercel.app",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 400
