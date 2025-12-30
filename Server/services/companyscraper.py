from playwright.sync_api import sync_playwright
from datetime import datetime

DETAIL_URL = "https://www.bseindia.com/corporates/AnnDet_new.aspx?newsid=b4b98761-db0f-44b8-bec5-9f7caf890db4"

def scrape_announcement_detail():
    with sync_playwright() as p:
        # User-Agent is often helpful for BSE to avoid being flagged as a bot
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()

        print("Opening announcement detail page...")
        page.goto(DETAIL_URL, timeout=60000, wait_until="domcontentloaded")

        # Wait for main announcement table
        page.wait_for_selector("#ContentPlaceHolder1_tdDet", timeout=60000)

        company = page.locator("#ContentPlaceHolder1_tdCompNm a").inner_text().strip()
        
        # Using .first here to avoid strict mode errors if multiple spans exist
        security_code = page.locator("#ContentPlaceHolder1_tdCompNm .spn02").first.inner_text().strip()

        title = page.locator("td.TTHeadergrey").first.inner_text().strip()

        # FIX: Target the specific PDF link in the table, avoiding the header/footer FAQs
        # We use a filter to find the link that is actually the "Download" link
        pdf_element = page.locator("a[href$='.pdf']").filter(has_text="") # The official link usually has no text, just an icon
        
        # Alternative approach: use the specific class BSE uses for these links
        pdf_url = page.locator("a.tablebluelink[href$='.pdf']").first.get_attribute("href")
        
        # Ensure the URL is absolute
        if pdf_url and not pdf_url.startswith("http"):
            pdf_url = "https://www.bseindia.com" + pdf_url

        description = page.locator("td.TTRow_leftnotices").inner_text().strip()

        # Improved Time Extraction logic
        time_row = page.locator("text=Exchange Received Time").locator("xpath=..")
        time_text = time_row.inner_text()
        
        # Splitting logic remains the same, but with added safety
        try:
            time_str = time_text.split("Exchange Received Time")[1].split("Exchange Disseminated")[1].strip()
            # Note: BSE sometimes varies spacing, check if your split logic matches the page exactly
            # Re-verifying the exact format from your traceback
            time_str = time_text.split("Exchange Received Time")[1].split("Exchange Disseminated")[0].strip()
            filed_at = datetime.strptime(time_str, "%d/%m/%Y %H:%M:%S")
        except Exception as e:
            print(f"Error parsing date: {e}")
            filed_at = "N/A"

        print("\nExtracted Announcement Details\n")
        print(f"Company       : {company}")
        print(f"Security Code : {security_code}")
        print(f"Title         : {title}")
        print(f"Filed At      : {filed_at}")
        print(f"PDF URL       : {pdf_url}")
        print(f"Description   : {description}")

        browser.close()

if __name__ == "__main__":
    scrape_announcement_detail()