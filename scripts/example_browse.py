import os
from pathlib import Path
from playwright.sync_api import sync_playwright


def main():
    headless = os.getenv("HEADLESS", "true").lower() in {"1", "true", "yes", "y"}
    browser_name = os.getenv("BROWSER", "chromium").lower()
    slow_mo = int(os.getenv("SLOW_MO", "0"))

    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser_type = getattr(p, browser_name)
        browser = browser_type.launch(headless=headless, slow_mo=slow_mo)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        url = os.getenv("URL", "https://example.com")
        page.goto(url)
        title = page.title()
        print(f"Opened {url} — Title: {title}")

        screenshot_path = artifacts_dir / "example.png"
        page.screenshot(path=str(screenshot_path))
        print(f"Saved screenshot to {screenshot_path}")

        browser.close()


if __name__ == "__main__":
    main()

