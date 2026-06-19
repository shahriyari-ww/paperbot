# providers/base_provider.py
import requests
import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any

def search_base(query: str) -> Optional[Dict[str, Any]]:
    """
    جستجو در BASE (Bielefeld Academic Search Engine)
    
    Args:
        query (str): عنوان مقاله یا DOI
        
    Returns:
        dict: اطلاعات مقاله یا None در صورت عدم یافت
    """
    try:
        # اگر query یک DOI است، آن را به صورت مستقیم جستجو کن
        if query.startswith("10."):
            # BASE معمولاً با DOI کار نمی‌کند، از عنوان استفاده کن
            print("❌ BASE doesn't support DOI directly, skipping...")
            return None
            
        url = f"https://api.base-search.net/cgi-bin/BaseHttpSearchInterface.fcgi?func=PerformSearch&query={query}&format=xml"
        
        print(f"📡 Sending request to BASE API...")
        resp = requests.get(url, timeout=30)
        
        if resp.status_code != 200:
            print(f"❌ BASE API returned status: {resp.status_code}")
            return None
        
        # پردازش پاسخ XML
        root = ET.fromstring(resp.text)
        
        # پیدا کردن اولین نتیجه
        hit = root.find(".//hit")
        if hit is None:
            print("❌ No hits found")
            return None
        
        # استخراج عنوان
        title_elem = hit.find(".//title")
        title = title_elem.text if title_elem is not None else "Unknown Title"
        print(f"📄 Found title: {title}")
        
        # پیدا کردن لینک PDF
        pdf_url = None
        
        # 1. جستجوی لینک‌های با فرمت PDF
        for elem in hit.findall(".//url"):
            if elem.text and elem.text.endswith(".pdf"):
                pdf_url = elem.text
                print(f"✅ Found PDF link: {pdf_url}")
                break
        
        # 2. اگر PDF پیدا نشد، از لینک اصلی استفاده کن
        if not pdf_url:
            url_elem = hit.find(".//url")
            if url_elem is not None and url_elem.text:
                pdf_url = url_elem.text
                print(f"ℹ️ Using generic link: {pdf_url}")
        
        if not pdf_url:
            print("❌ No link found")
            return None
        
        return {
            "title": title,
            "pdf_url": pdf_url,
            "source": "base"
        }
        
    except requests.exceptions.Timeout:
        print("❌ BASE API timeout")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ BASE API request error: {e}")
        return None
    except ET.ParseError as e:
        print(f"❌ BASE XML parse error: {e}")
        return None
    except Exception as e:
        print(f"❌ BASE search error: {e}")
        return None
