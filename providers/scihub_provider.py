# providers/scihub_provider.py
import requests
import re
from bs4 import BeautifulSoup

def search_scihub(query: str):
    """
    جستجو در Sci-Hub برای یافتن نسخه PDF واقعی مقاله
    
    Args:
        query (str): DOI مقاله (شروع با 10.)
        
    Returns:
        dict: اطلاعات مقاله با لینک PDF واقعی یا None در صورت عدم یافت
    """
    try:
        if not query.startswith("10."):
            print("❌ Not a DOI, skipping Sci-Hub")
            return None
            
        # آینه‌های Sci-Hub (مرتب‌شده بر اساس سرعت)
        mirrors = [
            "https://sci-hub.se",
            "https://sci-hub.st",
            "https://sci-hub.ru",
            "https://sci-hub.ee"
        ]
        
        print(f"📡 Searching Sci-Hub for: {query}")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }
        
        for mirror in mirrors:
            try:
                url = f"{mirror}/{query}"
                print(f"🔍 Trying mirror: {mirror}")
                
                # دریافت صفحه HTML
                resp = requests.get(url, headers=headers, timeout=30)
                
                if resp.status_code != 200:
                    print(f"❌ Mirror {mirror} returned status: {resp.status_code}")
                    continue
                
                # بررسی محتوا
                content_type = resp.headers.get('content-type', '').lower()
                
                # اگر مستقیماً PDF بود
                if 'application/pdf' in content_type:
                    print(f"✅ Found PDF directly at {mirror}")
                    return {
                        "title": f"Article from Sci-Hub ({query})",
                        "pdf_url": url,
                        "source": "scihub"
                    }
                
                # اگر HTML بود، لینک PDF را استخراج کن
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # ============================================================
                # روش‌های مختلف استخراج لینک PDF
                # ============================================================
                pdf_url = None
                
                # روش 1: پیدا کردن iframe یا embed
                for iframe in soup.find_all(['iframe', 'embed']):
                    src = iframe.get('src', '')
                    if src and 'pdf' in src.lower():
                        pdf_url = src
                        break
                
                # روش 2: پیدا کردن لینک دانلود
                if not pdf_url:
                    for link in soup.find_all('a'):
                        href = link.get('href', '')
                        text = link.text.lower()
                        # جستجو در متن و href
                        if 'pdf' in href.lower() or 'pdf' in text or 'دانلود' in text:
                            pdf_url = href
                            break
                
                # روش 3: جستجوی الگوی PDF در کل صفحه
                if not pdf_url:
                    pdf_pattern = re.compile(r'(https?://[^\s]+\.pdf)', re.IGNORECASE)
                    match = pdf_pattern.search(resp.text)
                    if match:
                        pdf_url = match.group(1)
                
                # روش 4: جستجوی الگوی PDF در اسکریپت‌ها
                if not pdf_url:
                    script_pattern = re.compile(r'location\.href\s*=\s*["\']([^"\']+\.pdf)["\']', re.IGNORECASE)
                    match = script_pattern.search(resp.text)
                    if match:
                        pdf_url = match.group(1)
                
                # روش 5: جستجوی دکمه دانلود
                if not pdf_url:
                    for button in soup.find_all(['button', 'div', 'span']):
                        text = button.text.lower()
                        if 'pdf' in text or 'دانلود' in text or 'download' in text:
                            # بررسی لینک اطراف
                            parent = button.find_parent('a')
                            if parent and parent.get('href'):
                                pdf_url = parent.get('href')
                                break
                
                # اگر لینک پیدا شد، آن را کامل کن
                if pdf_url:
                    # اگر لینک نسبی بود، کاملش کن
                    if pdf_url.startswith('/'):
                        pdf_url = f"{mirror}{pdf_url}"
                    elif not pdf_url.startswith('http'):
                        pdf_url = f"{mirror}/{pdf_url}"
                    
                    print(f"✅ Found PDF link: {pdf_url}")
                    
                    # تست لینک PDF پیدا شده
                    try:
                        test_resp = requests.get(pdf_url, headers=headers, timeout=10, stream=True)
                        if test_resp.status_code == 200 and 'application/pdf' in test_resp.headers.get('content-type', '').lower():
                            return {
                                "title": f"Article from Sci-Hub ({query})",
                                "pdf_url": pdf_url,
                                "source": "scihub"
                            }
                        else:
                            print(f"⚠️ PDF link test failed: {test_resp.status_code}")
                    except:
                        print(f"⚠️ PDF link test error, trying next mirror")
                        continue
                
                print(f"⚠️ No PDF link found in {mirror}, trying next mirror...")
                
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Error with {mirror}: {e}")
                continue
            except Exception as e:
                print(f"⚠️ Unexpected error with {mirror}: {e}")
                continue
        
        print("❌ No working Sci-Hub mirror found")
        return None
        
    except Exception as e:
        print(f"❌ Sci-Hub search error: {e}")
        return None
