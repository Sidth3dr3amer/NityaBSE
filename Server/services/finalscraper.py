import os
import json
import requests
import io
from datetime import datetime
from playwright.sync_api import sync_playwright
from db import get_db
from summarizer import summarize_text

# Add stealth import for anti-detection
try:
    from playwright_stealth import stealth_sync
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False
    print("[WARNING] playwright-stealth not installed. Install with: pip install playwright-stealth")

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
    print("[WARNING] PyMuPDF not installed. PDF page screenshots will be skipped. Install with: pip install PyMuPDF")

BANKEX_URL = "https://www.bseindia.com/sensex/code/53/"
BASE_URL = "https://www.bseindia.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/pdf",
    "Referer": "https://www.bseindia.com/"
}

# Cloudinary configuration via environment variables
CLOUDINARY_CONFIGURED = False
if CLOUDINARY_AVAILABLE:
    CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
    CLOUD_KEY = os.environ.get('CLOUDINARY_API_KEY')
    CLOUD_SECRET = os.environ.get('CLOUDINARY_API_SECRET')
    
    print(f"[CLOUDINARY] DEBUG - CLOUDINARY_AVAILABLE: {CLOUDINARY_AVAILABLE}")
    print(f"[CLOUDINARY] DEBUG - CLOUD_NAME set: {bool(CLOUD_NAME)}")
    print(f"[CLOUDINARY] DEBUG - CLOUD_KEY set: {bool(CLOUD_KEY)}")
    print(f"[CLOUDINARY] DEBUG - CLOUD_SECRET set: {bool(CLOUD_SECRET)}")
    
    if CLOUD_NAME and CLOUD_KEY and CLOUD_SECRET:
        try:
            cloudinary.config(
                cloud_name=CLOUD_NAME,
                api_key=CLOUD_KEY,
                api_secret=CLOUD_SECRET,
                secure=True
            )
            CLOUDINARY_CONFIGURED = True
            print(f"[CLOUDINARY] [OK] Configured for uploads (cloud_name={CLOUD_NAME})")
        except Exception as e:
            print(f"[CLOUDINARY] [FAIL] Failed to configure: {e}")
    else:
        print(f"[CLOUDINARY] [WARN] Env vars missing - CLOUDINARY_CONFIGURED will be False")
else:
    print("[CLOUDINARY] [WARN] Cloudinary library not available")

def upload_to_cloudinary(file_path, newsid, image_type, page_number=None):
    """Upload a file to Cloudinary and return the secure URL"""
    print(f"  [CLOUDINARY] upload_to_cloudinary called: file_path={file_path}, newsid={newsid}, type={image_type}, page={page_number}")
    print(f"  [CLOUDINARY] CLOUDINARY_CONFIGURED={CLOUDINARY_CONFIGURED}")
    
    if not CLOUDINARY_CONFIGURED:
        print(f"  [CLOUDINARY] [SKIP] Skipping upload - CLOUDINARY_CONFIGURED is False")
        return None
    
    if not os.path.exists(file_path):
        print(f"  [CLOUDINARY] [FAIL] File not found: {file_path}")
        return None
    
    file_size = os.path.getsize(file_path)
    print(f"  [CLOUDINARY] File exists, size: {file_size} bytes")
    
    try:
        # Create a folder structure: bankex/{newsid}/
        folder = f"bankex/{newsid}"
        
        # Create a unique public_id
        if page_number:
            public_id = f"{folder}/pdf_page_{page_number}"
        else:
            public_id = f"{folder}/{image_type}"
        
        print(f"  [CLOUDINARY] Uploading to folder={folder}, public_id={public_id}")
        
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            file_path,
            public_id=public_id,
            folder=folder,
            resource_type="image",
            overwrite=True
        )
        
        secure_url = result.get('secure_url')
        print(f"  [CLOUDINARY] [OK] Upload successful: {secure_url}")
        return secure_url
        
    except Exception as e:
        print(f"  [CLOUDINARY] [FAIL] Upload failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None

def classify(title, description):
    text = (title + description).lower()
    
    # AGM/EGM
    if "agm" in text or "egm" in text or "general meeting" in text or "annual general meeting" in text:
        return "agm_egm"
    
    # Board Meeting
    if "board meeting" in text or "board" in text:
        return "board_meeting"
    
    # Results
    if "financial result" in text or "results" in text or "unaudited" in text or "audited" in text:
        return "results"
    
    # Corporate Action
    if "dividend" in text or "bonus" in text or "split" in text or "buyback" in text or "corporate action" in text:
        return "corp_action"
    
    # Insider Trading / SAST
    if "insider" in text or "sast" in text or "substantial acquisition" in text or "shareholding" in text:
        return "insider_trading"
    
    # Company Update
    if "update" in text or "clarification" in text or "announcement" in text:
        return "company_update"
    
    # New Listing
    if "listing" in text or "ipo" in text or "public offer" in text:
        return "new_listing"
    
    # Integrated Filing (general filings)
    if "filing" in text or "compliance" in text or "trading window" in text:
        return "integrated_filing"
    
    return "other"

def scrape_detail(page, newsid):
    detail_url = f"{BASE_URL}/corporates/AnnDet_new.aspx?newsid={newsid}"
    page.goto(detail_url, timeout=60000, wait_until="domcontentloaded")
    try:
        page.wait_for_selector("#ContentPlaceHolder1_tdDet", timeout=30000)
    except Exception:
        print("[WARN] Detail container not found, continuing anyway")

    
    company = page.locator("#ContentPlaceHolder1_tdCompNm a").inner_text().strip()
    security_code = page.locator("#ContentPlaceHolder1_tdCompNm .spn02").first.inner_text().strip()
    title = page.locator("td.TTHeadergrey").first.inner_text().strip()
    description = page.locator("td.TTRow_leftnotices").inner_text().strip()
    
    pdf_url = page.locator("a.tablebluelink[href$='.pdf']").first.get_attribute("href")
    if pdf_url and not pdf_url.startswith("http"):
        pdf_url = BASE_URL + pdf_url
    
    # Upload images to Cloudinary and store URLs
    screenshot_json = None
    print(f"\n[SCRAPE_DETAIL] Starting image capture for newsid={newsid}")
    print(f"[SCRAPE_DETAIL] CLOUDINARY_CONFIGURED={CLOUDINARY_CONFIGURED}")
    try:
        images = []
        screenshot_dir = os.path.join(os.path.dirname(__file__), 'bankex_data', newsid)
        os.makedirs(screenshot_dir, exist_ok=True)
        print(f"[SCRAPE_DETAIL] Screenshot directory: {screenshot_dir}")
        
        # 1. Screenshot of announcement details section
        announcement_screenshot_path = os.path.join(screenshot_dir, 'announcement.png')
        try:
            print(f"[SCRAPE_DETAIL] Capturing announcement screenshot...")
            page.locator("#ContentPlaceHolder1_tdDet").screenshot(path=announcement_screenshot_path)
            
            if os.path.exists(announcement_screenshot_path) and os.path.getsize(announcement_screenshot_path) > 0:
                file_size = os.path.getsize(announcement_screenshot_path)
                print(f"[SCRAPE_DETAIL] Screenshot captured: {file_size} bytes")
                
                # Try Cloudinary upload
                print(f"[SCRAPE_DETAIL] Calling upload_to_cloudinary...")
                cloudinary_url = upload_to_cloudinary(announcement_screenshot_path, newsid, 'announcement')
                
                if cloudinary_url:
                    images.append({
                        'filename': 'announcement_details.png',
                        'url': cloudinary_url,
                        'type': 'announcement'
                    })
                    print(f"  [SCREENSHOT] [OK] Uploaded to Cloudinary: {cloudinary_url}")
                else:
                    print(f"  [SCREENSHOT] [WARN] upload_to_cloudinary returned None - NOT adding fallback")
                    print(f"  [SCREENSHOT] Images array now has {len(images)} items")
            else:
                print(f"[SCRAPE_DETAIL] [WARN] Screenshot file missing or empty")
        except Exception as screenshot_err:
            print(f"  [SCREENSHOT] [ERROR] Exception during capture: {type(screenshot_err).__name__}: {screenshot_err}")
        
        # 2. Download PDF and convert pages to images
        if pdf_url and HAS_PYMUPDF:
            try:
                print(f"  [PDF] Downloading PDF from {pdf_url}")
                pdf_response = requests.get(pdf_url, headers=HEADERS, timeout=30)
                
                if pdf_response.status_code == 200:
                    pdf_data = io.BytesIO(pdf_response.content)
                    pdf_document = fitz.open(stream=pdf_data, filetype="pdf")
                    page_count = min(len(pdf_document), 5)  # Limit to first 5 pages
                    print(f"  [PDF] Converting {page_count} page(s) to images")
                    
                    for page_num in range(page_count):
                        pdf_page = pdf_document[page_num]
                        
                        # Render page to image (zoom=2 for better quality)
                        mat = fitz.Matrix(2, 2)
                        pix = pdf_page.get_pixmap(matrix=mat)
                        
                        # Save to file
                        pdf_page_path = os.path.join(screenshot_dir, f'pdf_page_{page_num + 1}.png')
                        pix.save(pdf_page_path)
                        
                        # Upload to Cloudinary
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
                            print(f"  [PDF] [OK] Converted and uploaded page {page_num + 1} to Cloudinary")
                        else:
                            print(f"  [PDF] [WARN] upload_to_cloudinary returned None for page {page_num + 1} - NOT adding fallback")
                    
                    pdf_document.close()
                else:
                    print(f"  [PDF] Failed to download: HTTP {pdf_response.status_code}")
                    
            except Exception as pdf_err:
                print(f"  [PDF] Failed to process: {pdf_err}")
                
        elif pdf_url and not HAS_PYMUPDF:
            print(f"  [PDF] Skipping PDF conversion (PyMuPDF not installed)")
        
        # Store all image URLs as JSON
        screenshot_json = json.dumps({'images': images})
        if len(images) == 0:
            print(f"  [SCREENSHOT] [WARN] No images captured! Images array is EMPTY")
            print(f"  [SCREENSHOT] This will be stored in DB as: {screenshot_json}")
        else:
            cloudinary_count = sum(1 for i in images if 'url' in i)
            base64_count = sum(1 for i in images if 'data' in i)
            print(f"  [SCREENSHOT] [OK] Total: {len(images)} image(s) stored (Cloudinary: {cloudinary_count}, base64: {base64_count})")
        
    except Exception as e:
        print(f"  [SCREENSHOT] Failed: {e}")
    
    time_text = page.locator("text=Exchange Received Time").locator("xpath=..").inner_text()
    time_str = time_text.split("Exchange Received Time")[1].split("Exchange Disseminated")[0].strip()
    
    # Handle both date formats: dd/mm/yyyy and dd-mm-yyyy
    time_str_normalized = time_str.replace('-', '/')
    
    try:
        filed_at = datetime.strptime(time_str_normalized, "%d/%m/%Y %H:%M:%S")
    except ValueError:
        filed_at = datetime.strptime(time_str_normalized, "%d/%m/%Y  %H:%M:%S")
    
    # Generate summary using Ollama
    summary = summarize_text(title, title, description)
    
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

def announcement_exists(conn, newsid):
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM announcements WHERE id = %s", (newsid,))
        return cur.fetchone() is not None

def insert_announcement(conn, data):
    print(f"\n[INSERT] Inserting announcement id={data['id']}")
    print(f"[INSERT] screenshot_url value: {data['screenshot_url']}")
    print(f"[INSERT] screenshot_url length: {len(data['screenshot_url']) if data['screenshot_url'] else 0}")
    
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
    print(f"[INSERT] [OK] Announcement inserted")

def scrape_bankex():
    conn = get_db()
    
    with sync_playwright() as p:
        # 1. Add args to reduce RAM usage and detection
        browser = p.chromium.launch(
            headless=True,
            args=['--disable-dev-shm-usage', '--no-sandbox']
        )
        context = browser.new_context(user_agent=HEADERS["User-Agent"])
        page = context.new_page()
        page.route("**/*", lambda route: (
    route.abort()
    if route.request.resource_type in ["image", "font", "media"]
    else route.continue_()
))

        
        # 2. Apply Stealth to the page if available
        if STEALTH_AVAILABLE:
            stealth_sync(page)
            print("[STEALTH] Applied stealth mode to page")
        else:
            print("[STEALTH] Stealth mode not available, proceeding without it")
        
        print("Opening Bankex page...")
        # 3. Change "load" to "domcontentloaded" and increase timeout
        page.goto(BANKEX_URL, wait_until="domcontentloaded", timeout=90000)
        
        # 4. Wait for the specific element instead of the whole page
        page.wait_for_selector("div.cannn ul.ullist li a", timeout=60000)
        
        links = page.query_selector_all("div.cannn ul.ullist li a")
        newsids = []
        
        for a in links:
            href = a.get_attribute("href")
            if href and "newsid=" in href:
                newsids.append(href.split("newsid=")[1])
        
        print(f"\nFound {len(newsids)} announcements\n")
        
        for idx, newsid in enumerate(newsids, start=1):
            print(f"\n[{idx}] ========== Processing newsid: {newsid} ==========")
            
            # Check if already exists
            if announcement_exists(conn, newsid):
                print("  [SKIP] Already in DB, skipping")
                continue
            
            try:
                print(f"  [FLOW] Calling scrape_detail...")
                detail_page = context.new_page()
                page.route("**/*", lambda route: (
    route.abort()
    if route.request.resource_type in ["image", "font", "media"]
    else route.continue_()
))

                data = scrape_detail(detail_page, newsid)
                detail_page.close()

                print(f"  [FLOW] scrape_detail returned, screenshot_url={data.get('screenshot_url')[:50] if data.get('screenshot_url') else 'None'}...")
                insert_announcement(conn, data)
                print("  [OK] Inserted into DB")
            except Exception as e:
                print(f"  [ERROR] Failed: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
        
        browser.close()
    
    conn.close()

if __name__ == "__main__":
    scrape_bankex()