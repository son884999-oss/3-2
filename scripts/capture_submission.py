"""배포된 Balance AI를 자동 조작해 제출용 스크린샷을 만든다."""

from datetime import date
from pathlib import Path
import shutil
import tempfile
import time

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


FRONTEND_URL = "https://3-2-son884999-oss-projects.vercel.app"
API_URL = "https://balance-ai-api.onrender.com"
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "screenshots"


def choose_unused_date() -> str:
    response = requests.get(f"{API_URL}/api/data", timeout=90)
    response.raise_for_status()
    used = {row["date"] for row in response.json()}
    for candidate in ("2025-01-15", "2025-02-15", "2025-03-15", "2025-04-15"):
        if candidate not in used:
            return candidate
    raise RuntimeError("캡처용 날짜 후보가 모두 사용 중입니다.")


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

        chat_input = driver.find_element(By.ID, "chatInput")
        chat_input.send_keys("최근 7일 수면과 운동 균형을 분석하고 개선 목표를 알려줘")
        driver.find_element(By.ID, "chatForm").submit()
        wait.until(lambda d: not d.find_elements(By.ID, "loadingMessage"))
        wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, ".message.assistant")) >= 2)
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
        wait.until(lambda d: "show" in d.find_element(By.ID, "toast").get_attribute("class"))
        toast_text = driver.find_element(By.ID, "toast").text
        if "추가했습니다" not in toast_text:
            raise RuntimeError(f"CRUD 저장 실패: {toast_text}")
        wait.until(lambda d: capture_date in d.find_element(By.ID, "recordRows").text)
        driver.save_screenshot(str(OUTPUT_DIR / "02-data-crud.png"))

        driver.find_element(By.CSS_SELECTOR, '[data-tab="history"]').click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".conversation")))
        driver.save_screenshot(str(OUTPUT_DIR / "03-conversation-history.png"))

        driver.execute_script("document.querySelector('.conversation').click()")
        wait.until(EC.visibility_of_element_located((By.ID, "messages")))
        wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, ".message")) >= 2)
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
