import argparse
import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from playwright.sync_api import sync_playwright


URL = "https://www.cskh.evnspc.vn/TraCuu/LichNgungGiamCungCapDien"


def parse_results(text: str) -> Dict[str, Any]:
    # Focus on the section between the announcement header and the next main section
    start_idx = None
    for marker in ["THÔNG BÁO LỊCH CẮT ĐIỆN", "THONG BAO LICH CAT DIEN"]:
        i = text.upper().find(marker)
        if i != -1:
            start_idx = i
            break
    if start_idx is None:
        # If not found, just use entire body
        section = text
    else:
        end_idx = -1
        for end_marker in ["TRA CỨU LỊCH MẤT ĐIỆN", "CÁC DỊCH VỤ TRA CỨU", "TRA CUU LICH MAT DIEN"]:
            j = text.upper().find(end_marker, start_idx + 1)
            if j != -1:
                end_idx = j
                break
        section = text[start_idx:end_idx] if end_idx != -1 else text[start_idx:]

    lines = [ln.strip() for ln in section.splitlines() if ln.strip()]
    customer = None
    address = None
    entries: List[Dict[str, str]] = []

    for idx, ln in enumerate(lines):
        if ln.upper().startswith("KHÁCH HÀNG:") or ln.upper().startswith("KHACH HANG:"):
            customer = ln.split(":", 1)[1].strip()
        if ln.upper().startswith("ĐỊA CHỈ:") or ln.upper().startswith("DIA CHI:"):
            address = ln.split(":", 1)[1].strip()

    # Scan for schedule blocks by the "MÃ LỊCH:" marker
    i = 0
    while i < len(lines):
        if lines[i].upper().startswith("MÃ LỊCH:") or lines[i].upper().startswith("MA LICH:"):
            code = lines[i].split(":", 1)[1].strip()
            # Next expected lines: THỜI GIAN, LÝ DO
            thoi_gian = None
            ly_do = None
            j = i + 1
            while j < len(lines) and (thoi_gian is None or ly_do is None):
                u = lines[j].upper()
                if u.startswith("THỜI GIAN:") or u.startswith("THOI GIAN:"):
                    thoi_gian = lines[j].split(":", 1)[1].strip()
                elif u.startswith("LÝ DO NGỪNG CUNG CẤP ĐIỆN:") or u.startswith("LY DO NGUNG CUNG CAP DIEN:"):
                    ly_do = lines[j].split(":", 1)[1].strip()
                j += 1
            entries.append({
                "ma_lich": code,
                "thoi_gian": thoi_gian or "",
                "ly_do": ly_do or "",
            })
            i = j
        else:
            i += 1

    return {"customer": customer, "address": address, "entries": entries}


def lookup_outages(ma_khach_hang: str, headless: bool = True, slow_mo: int = 0) -> Dict[str, Any]:
    artifacts = Path("artifacts")
    artifacts.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, slow_mo=slow_mo)
        context = browser.new_context(viewport={"width": 1400, "height": 1000})
        page = context.new_page()
        page.goto(URL)
        page.wait_for_load_state("networkidle")
        page.fill("#idMaKhachHang", ma_khach_hang)
        page.click("#btnTraCuuMaKH")
        # Wait for the announcement header to show up
        page.get_by_text("THÔNG BÁO LỊCH CẮT ĐIỆN", exact=False).wait_for(timeout=10000)
        page.wait_for_timeout(500)
        after_path = artifacts / f"evn_after_search_{ma_khach_hang}_{ts}.png"
        page.screenshot(path=str(after_path), full_page=True)
        text = page.inner_text("body")
        result = parse_results(text)
        result["screenshot"] = str(after_path)
        browser.close()
        return result


def main():
    parser = argparse.ArgumentParser(description="Tra cứu lịch ngừng giảm cung cấp điện theo Mã khách hàng.")
    parser.add_argument("--code", "-c", dest="code", help="Mã khách hàng", default=os.getenv("MAKH"))
    parser.add_argument("--headed", action="store_true", help="Chạy hiện cửa sổ trình duyệt")
    parser.add_argument("--slow-mo", type=int, default=int(os.getenv("SLOW_MO", "0")), help="Delay ms giữa các thao tác")
    args = parser.parse_args()

    if not args.code:
        raise SystemExit("Vui lòng cung cấp --code <Mã khách hàng> hoặc đặt biến môi trường MAKH")

    data = lookup_outages(args.code, headless=not args.headed, slow_mo=args.slow_mo)

    print(f"KHÁCH HÀNG: {data.get('customer') or '-'}")
    print(f"ĐỊA CHỈ: {data.get('address') or '-'}")
    if not data.get("entries"):
        print("Không có lịch cúp điện.")
    else:
        for e in data["entries"]:
            print(f"- Mã lịch: {e['ma_lich']} — {e['thoi_gian']} — Lý do: {e['ly_do']}")
    print(f"Screenshot: {data.get('screenshot')}")


if __name__ == "__main__":
    main()

