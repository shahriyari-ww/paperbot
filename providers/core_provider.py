# providers/core_provider.py
import requests
from typing import Optional, Dict, Any

def search_core(query: str) -> Optional[Dict[str, Any]]:
    """
    جستجو در CORE (سامانه جستجوی مقالات Open Access)
    
    Args:
        query (str): عنوان مقاله یا DOI
        
    Returns:
        dict: اطلاعات مقاله یا None در صورت عدم یافت
    """
    try:
        # اگر query یک DOI است، آن را به صورت مستقیم جستجو کن
        if query.startswith("10."):
            url = f"https://api.core.ac.uk/v3/search/works?q={query}&limit=1"
        else:
            url = f"https://api.core.ac.uk/v3/search/works?q={query}&limit=1"
        
        headers = {
            "User-Agent": "PaperBot/2.0"
        }
        
        print(f"📡 Sending request to CORE API...")
        resp = requests.get(url, headers=headers, timeout=30)
        
        if resp.status_code != 200:
            print(f"❌ CORE API returned status: {resp.status_code}")
            return None
        
        data = resp.json()
        results = data.get("results", [])
        
        if not results:
            print("❌ No results found")
            return None
        
        item = results[0]
        title = item.get("title", "Unknown Title")
        print(f"📄 Found title: {title}")
        
        # پیدا کردن لینک PDF
        pdf_url = None
        for link in item.get("links", []):
            if link.get("type") == "application/pdf":
                pdf_url = link.get("url")
                print(f"✅ Found PDF link: {pdf_url}")
                break
        
        if not pdf_url:
            # اگر PDF مستقیم نبود، از لینک اصلی استفاده کن
            pdf_url = item.get("link", "")
            if pdf_url:
                print(f"ℹ️ Using generic link: {pdf_url}")
            else:
                print("❌ No link found")
                return None
        
        return {
            "title": title,
            "pdf_url": pdf_url,
            "source": "core"
        }
        
    except requests.exceptions.Timeout:
        print("❌ CORE API timeout")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ CORE API request error: {e}")
        return None
    except Exception as e:
        print(f"❌ CORE search error: {e}")
        return None
