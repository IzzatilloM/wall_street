import os, time
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000"
OUT = os.path.join(os.path.dirname(__file__), "_pptx_shots")
os.makedirs(OUT, exist_ok=True)

PAGES = [
    ("01_login",        "/accounts/login/",            False),
    ("02_register",     "/accounts/register/",         False),
    ("03_dashboard",    "/dashboard/",                 True),
    ("04_students",     "/students/",                  True),
    ("05_student_detail","/students/54/",              True),
    ("06_courses",      "/courses/",                   True),
    ("07_enrollments",  "/enrollments/",               True),
    ("08_attendance",   "/attendance/",                True),
    ("09_coin_award",   "/attendance/student/41/",     True),
    ("10_payments",     "/payments/",                  True),
    ("11_payment_create","/payments/create/",          True),
    ("12_payment_detail","/payments/112/",             True),
    ("13_reports",      "/reports/",                   True),
    ("14_salary",       "/salary/",                    True),
    ("15_calendar",     "/calendar/",                  True),
    ("16_instructors",  "/instructors/",               True),
    ("17_settings",     "/settings/",                  True),
]

def shot(page, name):
    p = os.path.join(OUT, name + ".png")
    page.screenshot(path=p, full_page=True)
    print("OK", name)

with sync_playwright() as pw:
    browser = pw.chromium.launch(channel="chrome", headless=True)
    ctx = browser.new_context(viewport={"width":1440,"height":900}, device_scale_factor=2)
    page = ctx.new_page()

    # login
    page.goto(BASE + "/accounts/login/", wait_until="networkidle")
    shot(page, "01_login")
    page.fill("input[name=username]", "Musaev_I")
    page.fill("input[name=password]", "izzatillo_2004")
    page.click("button[type=submit]")
    page.wait_for_load_state("networkidle")
    time.sleep(1)
    print("after login url:", page.url)

    for name, url, _auth in PAGES:
        if name == "01_login":
            continue
        try:
            page.goto(BASE + url, wait_until="networkidle", timeout=30000)
            time.sleep(0.8)
            shot(page, name)
        except Exception as e:
            print("ERR", name, repr(e)[:200])

    # Transfer modal screenshot on courses page
    try:
        page.goto(BASE + "/courses/", wait_until="networkidle")
        time.sleep(0.6)
        # open first transfer modal if exists
        opened = page.evaluate("""() => {
            const btn = [...document.querySelectorAll('[onclick]')].find(b => /transferModal/.test(b.getAttribute('onclick')||''));
            if(!btn) return null;
            const m = (btn.getAttribute('onclick').match(/transferModal[\\w]+/)||[])[0];
            if(window.openModal){ openModal(m); }
            return m;
        }""")
        time.sleep(0.6)
        if opened:
            shot(page, "06b_transfer_modal")
        else:
            print("no transfer modal (no students in courses)")
    except Exception as e:
        print("ERR transfer", repr(e)[:200])

    # Create course modal
    try:
        page.goto(BASE + "/courses/", wait_until="networkidle")
        time.sleep(0.5)
        page.evaluate("() => window.openModal && openModal('createCourseModal')")
        time.sleep(0.5)
        shot(page, "06c_create_course_modal")
    except Exception as e:
        print("ERR create course", repr(e)[:200])

    browser.close()
print("DONE")
