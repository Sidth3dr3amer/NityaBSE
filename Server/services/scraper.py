from playwright.sync_api import sync_playwright

BANKEX_URL = "https://www.bseindia.com/sensex/code/53/"

def scrape_bankex_announcements():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("Opening BSE Bankex page...")
        page.goto(BANKEX_URL, timeout=60000)

        # Wait for Angular announcements list to load
        page.wait_for_selector("div.cannn ul.ullist li a", timeout=60000)

        print("\nLatest Bankex Announcements:\n")

        announcements = page.query_selector_all("div.cannn ul.ullist li a")

        for idx, a in enumerate(announcements, start=1):
            text = a.inner_text().strip()
            href = a.get_attribute("href")

            # Extract newsid from URL
            newsid = None
            if href and "newsid=" in href:
                newsid = href.split("newsid=")[1]

            print(f"{idx}.")
            print(f"   Text   : {text}")
            print(f"   URL    : https://www.bseindia.com{href}")
            print(f"   NewsID : {newsid}")
            print("-" * 80)

        browser.close()

if __name__ == "__main__":
    scrape_bankex_announcements()
