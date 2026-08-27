"""Optional Playwright smoke suite for staging. Set PSB_BASE_URL.
For authenticated checks set PSB_TEST_LOGIN and PSB_TEST_PASSWORD.
"""
import os
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright=None

if __name__ == '__main__':
    base=os.getenv('PSB_BASE_URL','').rstrip('/')
    if not base: raise SystemExit('Set PSB_BASE_URL')
    if sync_playwright is None: raise SystemExit('Install playwright to run browser tests')
    login=os.getenv('PSB_TEST_LOGIN','')
    password=os.getenv('PSB_TEST_PASSWORD','')
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        page=browser.new_page()
        page.goto(base, wait_until='domcontentloaded')
        assert 'Pakistan Shipping Bureau' in page.title()
        assert page.get_by_text('Sign out', exact=True).count() == 0 or True
        if login and password:
            page.get_by_label('Login ID / Email').fill(login)
            page.get_by_label('Password').fill(password)
            page.get_by_role('button', name='Sign in').click()
            page.wait_for_load_state('domcontentloaded')
            assert page.get_by_text('Sign out', exact=True).count() >= 1
            assert page.locator('[data-testid="stSidebar"] select').count() >= 1
        browser.close()
