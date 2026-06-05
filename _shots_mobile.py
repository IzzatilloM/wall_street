import os, time
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8090"
OUT = os.path.join(os.path.dirname(__file__), "_pptx_shots")
os.makedirs(OUT, exist_ok=True)

with sync_playwright() as pw:
    browser = pw.chromium.launch(channel="chrome", headless=True)
    ctx = browser.new_context(viewport={"width":390,"height":844}, device_scale_factor=2, is_mobile=True)
    page = ctx.new_page()
    page.goto(BASE, wait_until="networkidle", timeout=60000)
    time.sleep(6)  # Flutter boot
    page.screenshot(path=os.path.join(OUT,"M1_login.png"))
    print("M1 url", page.url)

    # try login as a student
    try:
        # Flutter renders to canvas; try to type into the page via tab/keyboard
        page.mouse.click(195, 360)
        time.sleep(1)
        page.keyboard.type("ali.valiyev")
        time.sleep(0.5)
        page.keyboard.press("Tab")
        page.keyboard.type("AliValiyev@01")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(OUT,"M2_login_filled.png"))
        page.keyboard.press("Enter")
        time.sleep(6)
        page.screenshot(path=os.path.join(OUT,"M3_after.png"))
        print("after url", page.url)
    except Exception as e:
        print("ERR", repr(e)[:200])
    browser.close()
print("DONE")
