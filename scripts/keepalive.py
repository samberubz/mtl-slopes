from playwright.sync_api import sync_playwright

URLS = [
    "https://samberubz-pow.streamlit.app",   # <- your real app URL
]

def wake(url: str) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            try:
                page.get_by_text("Yes, get this app back up!").click(timeout=8000)
                print(f"[woke] {url}")
                page.wait_for_timeout(15000)  # let it actually boot
            except Exception:
                print(f"[awake] {url}")
        finally:
            browser.close()

if __name__ == "__main__":
    for u in URLS:
        wake(u)
