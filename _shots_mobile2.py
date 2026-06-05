import os, time
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8090"
OUT = os.path.join(os.path.dirname(__file__), "_pptx_shots")

with sync_playwright() as pw:
    browser = pw.chromium.launch(channel="chrome", headless=True)
    ctx = browser.new_context(viewport={"width":390,"height":844}, device_scale_factor=2, is_mobile=True)
    page = ctx.new_page()
    page.goto(BASE, wait_until="networkidle", timeout=60000)
    time.sleep(7)
    page.mouse.click(195, 315); time.sleep(0.6)
    page.keyboard.type("ali.valiyev", delay=40); time.sleep(0.4)
    page.mouse.click(195, 383); time.sleep(0.6)
    page.keyboard.type("AliValiyev@01", delay=40); time.sleep(0.4)
    page.screenshot(path=os.path.join(OUT,"M2_login_filled.png"))
    page.mouse.click(195, 460); time.sleep(8)
    page.screenshot(path=os.path.join(OUT,"M3_after.png"))
    print("after url", page.url)
    # bottom nav explore: tap around bottom tabs
    for i,(x,y,nm) in enumerate([(78,815,"home"),(156,815,"courses"),(234,815,"payments"),(312,815,"profile")]):
        page.mouse.click(x,y); time.sleep(3)
        page.screenshot(path=os.path.join(OUT,f"M_tab_{i}_{nm}.png"))
    browser.close()
print("DONE")
