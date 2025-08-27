Playwright (Python) quick start

Setup
- Create venv: `python3 -m venv .venv`
- Activate: `. .venv/bin/activate`
- Install libs: `pip install playwright pytest`
- Install browsers: `playwright install`

Run an example script
- Headless run: `. .venv/bin/activate && python scripts/example_browse.py`
- Headed run: `. .venv/bin/activate && HEADLESS=false python scripts/example_browse.py`
- Choose browser: `BROWSER=firefox python scripts/example_browse.py` (chromium|firefox|webkit)
- Change URL: `URL=https://playwright.dev python scripts/example_browse.py`

Record actions (codegen)
- Launch recorder: `. .venv/bin/activate && playwright codegen https://example.com`
- It opens a browser, records clicks/types, and outputs Python.

Notes
- Screenshots are saved to `artifacts/`.
- For slower visual runs: `SLOW_MO=250 python scripts/example_browse.py`.

Outage lookup (lịch cúp điện)
- Run lookup: `. .venv/bin/activate && python scripts/lich_cup_dien.py --code PB05080064649`
- Headed mode: `python scripts/lich_cup_dien.py --code <MAKH> --headed`
- Trigger phrase (for agent): say "lịch cúp điện <MAKH>" and the agent will run the script per `agent_workflows.yaml`.

Zalo Web check (persistent Firefox)
- One-time login: `. .venv/bin/activate && python scripts/zalo_check.py login --headed`
  - A Firefox window opens with Zalo Web. Scan the QR to log in.
  - Close the window after login. Session is saved under `.auth/zalo-firefox`.
- Verify/list chats: `python scripts/zalo_check.py check --headed`
  - Prints `LOGIN_STATE` and lists some chat names if logged in.
