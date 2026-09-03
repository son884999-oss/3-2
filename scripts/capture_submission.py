"""배포된 Balance AI를 자동 조작해 제출용 스크린샷을 만든다."""

from datetime import date, timedelta
import os
from pathlib import Path
import shutil
import tempfile
import time

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


FRONTEND_URL = os.getenv(
    "CAPTURE_FRONTEND_URL",
    "https://3-2-son884999-oss-projects.vercel.app",
).rstrip("/")
API_URL = os.getenv("CAPTURE_API_URL", "https://balance-ai-api.onrender.com").rstrip("/")
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "screenshots"


def choose_unused_date() -> str:
    response = requests.get(f"{API_URL}/api/data", timeout=90)
    response.raise_for_status()
    used = {row["date"] for row in response.json()}
    start = date(2024, 1, 1)
    for offset in range(365):
        candidate = (start + timedelta(days=offset)).isoformat()
        if candidate not in used:
            return candidate
    raise RuntimeError("캡처용 날짜를 찾을 수 없습니다.")


def capture() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    capture_date = choose_unused_date()
    options = webdriver.ChromeOptions()
    options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1600,1050")
    options.add_argument("--force-device-scale-factor=1")
    options.add_argument("--lang=ko-KR")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--remote-debugging-pipe")
    profile_dir = tempfile.mkdtemp(prefix="balance-ai-capture-")
    options.add_argument(f"--user-data-dir={profile_dir}")
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 120)
    try:
        driver.get(FRONTEND_URL)
        wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, ".metric b")[0].text != "—")
        driver.execute_script("document.body.style.zoom='0.88'")

        # 이미 저장된 실제 AI 대화를 불러와 무료 API 할당량과 무관하게 재현한다.
        driver.find_element(By.CSS_SELECTOR, '[data-tab="history"]').click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".conversation")))
        driver.execute_script("document.querySelector('.conversation').click()")
        wait.until(EC.visibility_of_element_located((By.ID, "messages")))
        wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, ".message")) >= 2)
        # 1번은 일반 채팅 화면, 4번은 불러오기 상태가 보이는 화면으로 구분한다.
        wait.until(EC.visibility_of_element_located((By.ID, "conversationStatus")))
        driver.execute_script(
            "document.getElementById('conversationStatus').classList.add('hidden');"
            "document.getElementById('toast').classList.remove('show')"
        )
        wait.until(lambda d: d.find_element(By.ID, "toast").value_of_css_property("opacity") == "0")
        driver.save_screenshot(str(OUTPUT_DIR / "01-dashboard-ai-chat.png"))

        driver.find_element(By.CSS_SELECTOR, '[data-tab="records"]').click()
        wait.until(EC.visibility_of_element_located((By.ID, "recordForm")))
        driver.execute_script(
            "const el=document.getElementById('date'); el.value=arguments[0]; "
            "el.dispatchEvent(new Event('input',{bubbles:true}));",
            capture_date,
        )
        for element_id, value in (
            ("sleep", "7.6"),
            ("exercise", "45"),
            ("memo", "과제 캡처용 건강 균형 달성 기록"),
        ):
            element = driver.find_element(By.ID, element_id)
            element.clear()
            element.send_keys(value)
        driver.find_element(By.ID, "recordForm").submit()
        wait.until(lambda d: capture_date in d.find_element(By.ID, "recordRows").text)
        driver.save_screenshot(str(OUTPUT_DIR / "02-data-crud.png"))

        driver.find_element(By.CSS_SELECTOR, '[data-tab="history"]').click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".conversation")))
        driver.save_screenshot(str(OUTPUT_DIR / "03-conversation-history.png"))

        driver.execute_script("document.querySelector('.conversation').click()")
        wait.until(EC.visibility_of_element_located((By.ID, "messages")))
        wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, ".message")) >= 2)
        wait.until(EC.visibility_of_element_located((By.ID, "conversationStatus")))
        wait.until(lambda d: "저장된 대화 불러옴" in d.find_element(By.ID, "conversationStatus").text)
        driver.save_screenshot(str(OUTPUT_DIR / "04-conversation-loaded.png"))

        severe = [
            entry
            for entry in driver.get_log("browser")
            if entry["level"] == "SEVERE" and "favicon.ico" not in entry["message"]
        ]
        if severe:
            raise RuntimeError("브라우저 콘솔 오류: " + " | ".join(item["message"] for item in severe))
    finally:
        driver.quit()
        shutil.rmtree(profile_dir, ignore_errors=True)


if __name__ == "__main__":
    capture()
    print(f"스크린샷 저장 완료: {OUTPUT_DIR}")
