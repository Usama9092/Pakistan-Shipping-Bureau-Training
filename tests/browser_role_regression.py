"""Playwright role regression runner for staging.
Set PSB_BASE_URL and PSB_ROLE_MATRIX_JSON to a JSON list of test accounts with role/name.
Secrets remain in environment variables referenced by matrix entries.
"""
import os, json
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright=None

def main():
    base=os.getenv('PSB_BASE_URL','').rstrip('/')
    matrix=json.loads(os.getenv('PSB_ROLE_MATRIX_JSON','[]'))
    if not base or not matrix: raise SystemExit('Set PSB_BASE_URL and PSB_ROLE_MATRIX_JSON')
    if sync_playwright is None: raise SystemExit('Install playwright')
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        for item in matrix:
            page=browser.new_page()
            page.goto(base,wait_until='domcontentloaded')
            page.get_by_label('Login ID / Email').fill(os.environ[item['login_env']])
            page.get_by_label('Password').fill(os.environ[item['password_env']])
            page.get_by_role('button',name='Sign in').click()
            page.wait_for_timeout(1200)
            assert page.get_by_text('Sign out',exact=True).count() >= 1, item['role']
            assert page.locator('[data-testid="stSidebar"]').count() == 1, item['role']
            page.close()
        browser.close()
    print(f'BROWSER ROLE REGRESSION: PASS ({len(matrix)} roles)')
if __name__=='__main__': main()
