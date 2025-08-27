import argparse
from pathlib import Path
from typing import List

from playwright.sync_api import sync_playwright, TimeoutError


USER_DATA_DIR = Path(".auth/zalo-firefox")
ZALO_URL = "https://chat.zalo.me/"


def ensure_dirs():
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)


def detect_login_and_list(page) -> (bool, List[str]):
    page.goto(ZALO_URL, wait_until="load")
    page.wait_for_timeout(3000)
    # If redirected to id.zalo.me (login portal), consider logged out
    if "id.zalo.me" in page.url:
        return False, []
    # Heuristic: page contains conversations list when logged in
    names: List[str] = []
    # Try a few selectors likely to match conversation names
    selectors = [
        '[role="listitem"] [dir] span',
        '[data-qa="conversation-item"]',
        '.conversation-item .name',
        '.conv-item .title',
        'a[href^="/conversation"]',
    ]
    for sel in selectors:
        try:
            els = page.locator(sel)
            count = els.count()
            for i in range(min(30, count)):
                txt = els.nth(i).inner_text().strip()
                if txt and txt not in names:
                    names.append(txt)
            if names:
                break
        except Exception:
            pass
    return True, names


def login_flow(headless: bool):
    ensure_dirs()
    with sync_playwright() as p:
        ctx = p.firefox.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR), headless=headless, viewport={"width": 1400, "height": 900}
        )
        page = ctx.new_page()
        page.goto(ZALO_URL)
        print("Opened Zalo. If you see the QR, please scan to log in.")
        print("This window can remain open; close it after login.")
        # Keep the browser open until user closes it manually
        ctx.on("close", lambda: None)
        # Wait until user interrupts
        try:
            while True:
                page.wait_for_timeout(10_000)
        except KeyboardInterrupt:
            pass
        ctx.close()


def check_flow(headless: bool):
    ensure_dirs()
    with sync_playwright() as p:
        ctx = p.firefox.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR), headless=headless, viewport={"width": 1400, "height": 900}
        )
        page = ctx.new_page()
        logged_in, names = detect_login_and_list(page)
        page.screenshot(path="artifacts/zalo_check.png", full_page=True)
        print("Screenshot: artifacts/zalo_check.png")
        if not logged_in:
            print("LOGIN_STATE: LOGGED_OUT (in this Playwright profile)")
        else:
            print("LOGIN_STATE: LOGGED_IN")
            print("Some chats:", names[:10])
        ctx.close()


def main():
    ap = argparse.ArgumentParser(description="Zalo Web login check using persistent Firefox profile")
    ap.add_argument("mode", choices=["login", "check"], help="login: open window to login; check: verify and list chats")
    ap.add_argument("--headed", action="store_true", help="Run with browser window visible")
    args = ap.parse_args()

    if args.mode == "login":
        login_flow(headless=not args.headed)
    else:
        check_flow(headless=not args.headed)


if __name__ == "__main__":
    main()

