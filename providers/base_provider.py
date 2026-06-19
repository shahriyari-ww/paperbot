import requests
import xml.etree.ElementTree as ET

def search_base(query: str):
    """
    جستجو در BASE (Bielefeld Academic Search Engine)
    """
    try:
        url = f"https://api.base-search.net/cgi-bin/BaseHttpSearchInterface.fcgi?func=PerformSearch&query={query}&format=xml"
        resp = requests.get(url, timeout=30)
        
        if resp.status_code != 200:
            return None
        
        root = ET.fromstring(resp.text)
        
        # پیدا کردن اولین نتیجه
        hit = root.find(".//hit")
        if hit is None:
            return None
        
        title_elem = hit.find(".//title")
        title = title_elem.text if title_elem is not None else "Unknown Title"
        
        # پیدا کردن لینک PDF
        pdf_url = None
        for elem in hit.findall(".//url"):
            if elem.text and elem.text.endswith(".pdf"):
                pdf_url = elem.text
                break
        
        if not pdf_url:
            # اگر PDF پیدا نشد، از لینک اصلی استفاده کن
            url_elem = hit.find(".//url")
            if url_elem is not None:
                pdf_url = url_elem.text
        
        if not pdf_url:
            return None
        
        return {
            "title": title,
            "pdf_url": pdf_url,
            "source": "base"
        }
        
    except Exception as e:
        print(f"BASE search error: {e}")
        return None
