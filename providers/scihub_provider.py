# providers/scihub_provider.py
import requests
import re
from bs4 import BeautifulSoup

def search_scihub(query: str):
    """
    جستجو در Sci-Hub برای یافتن نسخه PDF واقعی مقاله
    """
    try:
        if not query.startswith("10."):
            print("❌ Not a DOI, skipping Sci-Hub")
            return None
            
        # آینه‌های Sci-Hub
        mirrors = [
            "https://sci-hub.se",
            "https://sci-hub.st",
            "https://sci-hub.ru",
            "https://sci-hub.ee"
        ]
        
        print(f"📡 Searching Sci-Hub for: {query}")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        for mirror in mirrors:
            try:
                url = f"{mirror}/{query}"
                resp = requests.get(url, headers=headers, timeout=30)
                
                if resp.status_code == 200:
                    # بررسی محتوا برای پیدا کردن PDF واقعی
                    content_type = resp.headers.get('content-type', '')
                    
                    # اگر مستقیم PDF بود
                    if 'application/pdf' in content_type:
                        print(f"✅ Found PDF directly at {mirror}")
                        return {
                            "title": f"Article from Sci-Hub ({query})",
                            "pdf_url": url,  # خود URL برای دانلود PDF
                            "source": "scihub"
                        }
                    
                    # اگر HTML بود، لینک PDF را استخراج کن
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    
                    # روش 1: پیدا کردن لینک دانلود
                    pdf_link = None
                    for link in soup.find_all('a'):
                        href = link.get('href', '')
                        if href.endswith('.pdf') or 'pdf' in href.lower():
                            pdf_link = href
                            break
                    
                    # روش 2: پیدا کردن iframe یا embed
                    if not pdf_link:
                        for iframe in soup.find_all(['iframe', 'embed']):
                            src = iframe.get('src', '')
                            if src and 'pdf' in src.lower():
                                pdf_link = src
                                break
                    
                    # روش 3: جستجوی لینک در متون
                    if not pdf_link:
                        # جستجوی الگوی PDF در متن
                        pdf_pattern = re.compile(r'(https?://[^\s]+\.pdf)', re.IGNORECASE)
                        match = pdf_pattern.search(resp.text)
                        if match:
                            pdf_link = match.group(1)
                    
                    # اگر لینک پیدا شد، آن را کامل کن
                    if pdf_link:
                        if pdf_link.startswith('/'):
                            pdf_link = f"{mirror}{pdf_link}"
                        elif not pdf_link.startswith('http'):
                            pdf_link = f"{mirror}/{pdf_link}"
                        
                        print(f"✅ Found PDF link: {pdf_link}")
                        return {
                            "title": f"Article from Sci-Hub ({query})",
                            "pdf_url": pdf_link,
                            "source": "scihub"
                        }
                    
                    # اگر لینک PDF پیدا نشد، از همان URL استفاده کن
                    print(f"ℹ️ No PDF link found, using original URL")
                    return {
                        "title": f"Article from Sci-Hub ({query})",
                        "pdf_url": url,
                        "source": "scihub"
                    }
                    
            except requests.exceptions.RequestException:
                continue
            except Exception as e:
                print(f"⚠️ Error processing {mirror}: {e}")
                continue
        
        print("❌ No working Sci-Hub mirror found")
        return None
        
    except Exception as e:
        print(f"❌ Sci-Hub search error: {e}")
        return None
