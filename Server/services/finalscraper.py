import os
import json
import requests
import io
import time
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from db import get_db
from summarizer import summarize_text

# Add stealth import for anti-detection
try:
    from playwright_stealth import stealth_sync
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False
    print("[WARNING] playwright-stealth not installed")

# Optional Cloudinary support
try:
    import cloudinary
    import cloudinary.uploader
    CLOUDINARY_AVAILABLE = True
except Exception:
    CLOUDINARY_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
    print("[WARNING] PyMuPDF not installed - PDF conversion disabled")

BANKEX_URL = "https://www.bseindia.com/sensex/code/53/"
BASE_URL = "https://www.bseindia.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Referer": "https://www.bseindia.com/"
}

# Cloudinary configuration
CLOUDINARY_CONFIGURED = False
if CLOUDINARY_AVAILABLE:
    CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
    CLOUD_KEY = os.environ.get('CLOUDINARY_API_KEY')
    CLOUD_SECRET = os.environ.get('CLOUDINARY_API_SECRET')
    
    if CLOUD_NAME and CLOUD_KEY and CLOUD_SECRET:
        try:
            cloudinary.config(
                cloud_name=CLOUD_NAME,
                api_key=CLOUD_KEY,
                api_secret=CLOUD_SECRET,
                secure=True
            )
            CLOUDINARY_CONFIGURED = True
            print(f"[CLOUDINARY] Configured (cloud_name={CLOUD_NAME})")
        except Exception as e:
            print(f"[CLOUDINARY] Configuration failed: {e}")


def upload_to_cloudinary(file_path, newsid, image_type, page_number=None):
    """Upload a file to Cloudinary and return the secure URL"""
    if not CLOUDINARY_CONFIGURED or not os.path.exists(file_path):
        return None
    
    try:
        folder = f"bankex/{newsid}"
        public_id = f"{folder}/pdf_page_{page_number}" if page_number else f"{folder}/{image_type}"
        
        result = cloudinary.uploader.upload(
            file_path,
            public_id=public_id,
            folder=folder,
            resource_type="image",
            overwrite=True
        )
        
        return result.get('secure_url')
        
    except Exception as e:
        print(f"  [CLOUDINARY] Upload failed: {e}")
        return None


def classify(title, description):
    """Classify announcement based on title and description"""
    text = (title + " " + description).lower()
    
    if any(term in text for term in ["agm", "egm", "general meeting", "annual general meeting"]):
        return "agm_egm"
    
    if "board meeting" in text or "board meet" in text:
        return "board_meeting"
    
    if any(term in text for term in ["financial result", "quarterly result", "results", "unaudited", "audited financial"]):
        return "results"
    
    if any(term in text for term in ["dividend", "bonus", "split", "buyback", "corporate action", "record date"]):
        return "corp_action"
    
    if any(term in text for term in ["insider", "sast", "substantial acquisition", "continual disclosure"]):
        return "insider_trading"
    
    if any(term in text for term in ["update", "clarification", "announcement", "press release"]):
        return "company_update"
    
    if any(term in text for term in ["listing", "ipo", "public offer", "initial public"]):
        return "new_listing"
    
    if any(term in text for term in ["filing", "compliance", "trading window", "outcome"]):
        return "integrated_filing"
    
    return "other"


def scrape_detail(page, newsid):
    """Scrape detailed information for a specific announcement"""
    detail_url = f"{BASE_URL}/corporates/AnnDet_new.aspx?newsid={newsid}"
    
    # Retry logic for detail page
    max_retries = 2
    for attempt in range(max_retries):
        try:
            page.goto(detail_url, timeout=60000, wait_until="domcontentloaded")
            page.wait_for_selector("#ContentPlaceHolder1_tdDet", timeout=30000)
            break
        except PlaywrightTimeoutError:
            if attempt < max_retries - 1:
                print(f"  [RETRY] Attempt {attempt + 1} failed, retrying detail page...")
                time.sleep(2)
            else:
                raise
    
    # Extract basic information
    company = page.locator("#ContentPlaceHolder1_tdCompNm a").inner_text().strip()
    security_code = page.locator("#ContentPlaceHolder1_tdCompNm .spn02").first.inner_text().strip()
    title = page.locator("td.TTHeadergrey").first.inner_text().strip()
    description = page.locator("td.TTRow_leftnotices").inner_text().strip()
    
    # Extract PDF URL
    pdf_url = None
    try:
        pdf_link = page.locator("a.tablebluelink[href$='.pdf']").first
        pdf_url = pdf_link.get_attribute("href")
        if pdf_url and not pdf_url.startswith("http"):
            pdf_url = BASE_URL + pdf_url
    except:
        pass
    
    # Extract filing timestamp
    try:
        time_text = page.locator("text=Exchange Received Time").locator("xpath=..").inner_text()
        time_str = time_text.split("Exchange Received Time")[1].split("Exchange Disseminated")[0].strip()
        time_str_normalized = time_str.replace('-', '/')
        
        try:
            filed_at = datetime.strptime(time_str_normalized, "%d/%m/%Y %H:%M:%S")
        except ValueError:
            filed_at = datetime.strptime(time_str_normalized, "%d/%m/%Y  %H:%M:%S")
    except:
        filed_at = datetime.now()
    
    # Capture screenshots and images
    screenshot_json = capture_images(page, newsid, pdf_url)
    
    # Generate summary
    try:
        summary = summarize_text(title, title, description)
    except Exception as e:
        print(f"  [WARN] Summary generation failed: {e}")
        summary = description[:200] + "..." if len(description) > 200 else description
    
    return {
        "id": newsid,
        "company_code": security_code,
        "company_name": company,
        "title": title,
        "subject": title,
        "summary": summary,
        "category": classify(title, description),
        "filed_at": filed_at,
        "pdf_url": pdf_url,
        "screenshot_url": screenshot_json,
        "source_page": detail_url
    }


def capture_images(page, newsid, pdf_url):
    """Capture announcement screenshot and PDF page images"""
    images = []
    screenshot_dir = os.path.join(os.path.dirname(__file__), 'bankex_data', newsid)
    os.makedirs(screenshot_dir, exist_ok=True)
    
    # 1. Screenshot of announcement
    announcement_screenshot_path = os.path.join(screenshot_dir, 'announcement.png')
    try:
        page.locator("#ContentPlaceHolder1_tdDet").screenshot(path=announcement_screenshot_path)
        
        if os.path.exists(announcement_screenshot_path) and os.path.getsize(announcement_screenshot_path) > 0:
            cloudinary_url = upload_to_cloudinary(announcement_screenshot_path, newsid, 'announcement')
            
            if cloudinary_url:
                images.append({
                    'filename': 'announcement_details.png',
                    'url': cloudinary_url,
                    'type': 'announcement'
                })
    except Exception as e:
        print(f"  [SCREENSHOT] Failed: {e}")
    
    # 2. PDF page conversion
    if pdf_url and HAS_PYMUPDF:
        try:
            pdf_response = requests.get(pdf_url, headers=HEADERS, timeout=30)
            
            if pdf_response.status_code == 200:
                pdf_data = io.BytesIO(pdf_response.content)
                pdf_document = fitz.open(stream=pdf_data, filetype="pdf")
                page_count = min(len(pdf_document), 5)
                
                for page_num in range(page_count):
                    pdf_page = pdf_document[page_num]
                    mat = fitz.Matrix(2, 2)
                    pix = pdf_page.get_pixmap(matrix=mat)
                    
                    pdf_page_path = os.path.join(screenshot_dir, f'pdf_page_{page_num + 1}.png')
                    pix.save(pdf_page_path)
                    
                    cloudinary_url = upload_to_cloudinary(
                        pdf_page_path, 
                        newsid, 
                        'pdf_page', 
                        page_number=page_num + 1
                    )
                    
                    if cloudinary_url:
                        images.append({
                            'filename': f'pdf_page_{page_num + 1}.png',
                            'url': cloudinary_url,
                            'type': 'pdf_page',
                            'page_number': page_num + 1
                        })
                
                pdf_document.close()
                print(f"  [PDF] Converted {page_count} page(s)")
                
        except Exception as e:
            print(f"  [PDF] Processing failed: {e}")
    
    return json.dumps({'images': images})


def announcement_exists(conn, newsid):
    """Check if announcement already exists in database"""
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM announcements WHERE id = %s", (newsid,))
        return cur.fetchone() is not None


def insert_announcement(conn, data):
    """Insert announcement into database"""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO announcements (
                id, company_code, company_name, title, subject,
                summary, category, filed_at, pdf_url, screenshot_url,
                source_page, exchange, index_name
            ) VALUES (
                %(id)s, %(company_code)s, %(company_name)s, %(title)s, %(subject)s,
                %(summary)s, %(category)s, %(filed_at)s, %(pdf_url)s, %(screenshot_url)s,
                %(source_page)s, 'BSE', 'BANKEX'
            )
            ON CONFLICT (id) DO NOTHING;
        """, data)
    conn.commit()


def try_goto_with_retries(page, url, max_retries=3, timeout=120000):
    """Try to navigate to URL with exponential backoff retry"""
    for attempt in range(max_retries):
        try:
            print(f"  [ATTEMPT {attempt + 1}/{max_retries}] Loading {url}...")
            
            # Increase timeout with each retry
            current_timeout = timeout + (attempt * 30000)
            
            page.goto(url, wait_until="domcontentloaded", timeout=current_timeout)
            
            # Wait for content to appear
            page.wait_for_selector("div.cannn ul.ullist li a", timeout=60000)
            
            print(f"  [SUCCESS] Page loaded successfully")
            return True
            
        except PlaywrightTimeoutError as e:
            print(f"  [TIMEOUT] Attempt {attempt + 1} failed after {current_timeout/1000}s")
            
            if attempt < max_retries - 1:
                wait_time = 5 * (attempt + 1)  # 5s, 10s, 15s
                print(f"  [WAIT] Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                print(f"  [FATAL] All {max_retries} attempts failed")
                raise
        
        except Exception as e:
            print(f"  [ERROR] Attempt {attempt + 1} failed: {type(e).__name__}: {e}")
            if attempt < max_retries - 1:
                time.sleep(3 * (attempt + 1))
            else:
                raise
    
    return False


def scrape_bankex():
    """Main scraper function with enhanced retry logic"""
    print("\n" + "="*60)
    print(f" BANKEX SCRAPER - {datetime.now()}")
    print("="*60)
    print(f"[CONFIG] Cloudinary: {CLOUDINARY_CONFIGURED}")
    print(f"[CONFIG] PyMuPDF: {HAS_PYMUPDF}")
    print(f"[CONFIG] Stealth: {STEALTH_AVAILABLE}")
    print("="*60 + "\n")
    
    conn = get_db()
    
    with sync_playwright() as p:
        # Launch browser with aggressive anti-detection
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-gpu',
                '--disable-software-rasterizer',
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process'
            ]
        )
        
        context = browser.new_context(
            user_agent=HEADERS["User-Agent"],
            viewport={'width': 1920, 'height': 1080},
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
            }
        )
        
        page = context.new_page()
        
        # Apply stealth mode
        if STEALTH_AVAILABLE:
            stealth_sync(page)
            print("[STEALTH] Applied to page")
        
        # Block unnecessary resources
        def handle_route(route):
            if route.request.resource_type in ["image", "font", "media"]:
                route.abort()
            else:
                route.continue_()
        
        page.route("**/*", handle_route)
        print("[WARMUP] Allowing browser context to stabilize...")
        time.sleep(15)

        
        try:
            print("[MAIN] Attempting to load BANKEX page...")
            
            # Try loading the page with retries
            if not try_goto_with_retries(page, BANKEX_URL, max_retries=3):
                time.sleep(3)
                raise Exception("Failed to load BANKEX page after all retries")
               

            
            # Extract announcement links
            links = page.query_selector_all("div.cannn ul.ullist li a")
            newsids = []
            
            for a in links:
                href = a.get_attribute("href")
                if href and "newsid=" in href:
                    newsids.append(href.split("newsid=")[1])
            
            print(f"\n[INFO] Found {len(newsids)} announcements\n")
            
            if len(newsids) == 0:
                print("[WARN] No announcements found - page may not have loaded correctly")
                print("[DEBUG] Taking screenshot for debugging...")
                page.screenshot(path="debug_bankex_page.png")
            
            success_count = 0
            skip_count = 0
            error_count = 0
            
            # Process each announcement
            for idx, newsid in enumerate(newsids, start=1):
                print(f"\n[{idx}/{len(newsids)}] Processing newsid: {newsid}")
                
                if announcement_exists(conn, newsid):
                    print("  [SKIP] Already in database")
                    skip_count += 1
                    continue
                
                try:
                    detail_page = context.new_page()
                    detail_page.route("**/*", handle_route)

                    try:
                        data = scrape_detail(detail_page, newsid)
                    except Exception as e:
                        if idx == 1:
                            print("  [WARMUP RETRY] Retrying first announcement...")
                            time.sleep(10)
                            data = scrape_detail(detail_page, newsid)
                        else:
                            raise

                    insert_announcement(conn, data)

                    detail_page.close()
                    success_count += 1
                    print("  [SUCCESS] Inserted into database")

                    time.sleep(1)

                except Exception as e:
                    error_count += 1
                    print(f"  [ERROR] {type(e).__name__}: {e}")

            
            print("\n" + "="*60)
            print("SCRAPING COMPLETE")
            print(f"  Success: {success_count}")
            print(f"  Skipped: {skip_count}")
            print(f"  Errors:  {error_count}")
            print("="*60 + "\n")
            
        except Exception as e:
            print(f"\n[FATAL] Scraper failed: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            
            # Take debug screenshot
            try:
                page.screenshot(path="debug_error.png")
                print("[DEBUG] Error screenshot saved to debug_error.png")
            except:
                pass
        
        finally:
            browser.close()
            conn.close()


if __name__ == "__main__":
    scrape_bankex()