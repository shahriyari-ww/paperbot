# providers/scihub_provider.py
import requests
import re
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any

def search_scihub(query: str) -> Optional[Dict[str, Any]]:
    """
    جستجو در Sci-Hub برای یافتن نسخه PDF واقعی مقاله با چندین روش استخراج
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
            "https://sci-hub.ee",
            "https://sci-hub.wf",
            "https://sci-hub.shop",
            "https://sci-hub.yt",
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
                
                resp = requests.get(url, headers=headers, timeout=30)
                
                if resp.status_code != 200:
                    print(f"❌ Mirror {mirror} returned status: {resp.status_code}")
                    continue
                
                content_type = resp.headers.get('content-type', '').lower()
                
                # اگر مستقیماً PDF بود
                if 'application/pdf' in content_type:
                    print(f"✅ Found PDF directly at {mirror}")
                    return {
                        "title": f"Article from Sci-Hub ({query})",
                        "pdf_url": url,
                        "source": "scihub"
                    }
                
                # استخراج لینک PDF از HTML
                soup = BeautifulSoup(resp.text, 'html.parser')
                pdf_url = None
                
                # روش‌های مختلف استخراج
                extraction_methods = [
                    ("iframe/embed", lambda: next((el.get('src') for el in soup.find_all(['iframe', 'embed']) if el.get('src') and 'pdf' in el.get('src').lower()), None)),
                    ("links", lambda: next((a.get('href') for a in soup.find_all('a') if a.get('href') and ('pdf' in a.get('href').lower() or 'pdf' in a.text.lower())), None)),
                    ("pattern", lambda: re.search(r'(https?://[^\s]+\.pdf)', resp.text).group(1) if re.search(r'(https?://[^\s]+\.pdf)', resp.text) else None),
                    ("script", lambda: re.search(r'location\.href\s*=\s*["\']([^"\']+\.pdf)["\']', resp.text).group(1) if re.search(r'location\.href\s*=\s*["\']([^"\']+\.pdf)["\']', resp.text) else None),
                    ("meta_refresh", lambda: re.search(r'url=([^;]+)', soup.find('meta', attrs={'http-equiv': 'refresh'}).get('content', '')).group(1) if soup.find('meta', attrs={'http-equiv': 'refresh'}) and re.search(r'url=([^;]+)', soup.find('meta', attrs={'http-equiv': 'refresh'}).get('content', '')) else None),
                ]
                
                for method_name, method_func in extraction_methods:
                    try:
                        result = method_func()
                        if result:
                            pdf_url = result
                            print(f"🔍 Found PDF using {method_name}: {pdf_url}")
                            break
                    except:
                        continue
                
                if pdf_url:
                    if pdf_url.startswith('/'):
                        pdf_url = f"{mirror}{pdf_url}"
                    elif not pdf_url.startswith('http'):
                        pdf_url = f"{mirror}/{pdf_url}"
                    
                    # تست لینک
                    try:
                        test_resp = requests.get(pdf_url, headers=headers, timeout=10, stream=True)
                        if test_resp.status_code == 200:
                            test_content_type = test_resp.headers.get('content-type', '').lower()
                            if 'application/pdf' in test_content_type or pdf_url.endswith('.pdf'):
                                print(f"✅ PDF link verified: {pdf_url}")
                                return {
                                    "title": f"Article from Sci-Hub ({query})",
                                    "pdf_url": pdf_url,
                                    "source": "scihub"
                                }
                    except:
                        pass
                
                print(f"⚠️ No valid PDF link found in {mirror}")
                
            except Exception as e:
                print(f"⚠️ Error with {mirror}: {e}")
                continue
        
        print("❌ No working Sci-Hub mirror found")
        return None
        
    except Exception as e:
        print(f"❌ Sci-Hub search error: {e}")
        return None
