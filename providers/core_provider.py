import requests

def search_core(query: str):
    """
    جستجو در CORE (سامانه جستجوی مقالات Open Access)
    """
    try:
        # ساخت URL جستجو
        url = "https://api.core.ac.uk/v3/search/works"
        params = {
            "q": query,
            "limit": 1,
            "scroll": "true"
        }
        headers = {
            "Authorization": "Bearer YOUR_CORE_API_KEY"  # برای دریافت کلید رایگان ثبت‌نام کنید
        }
        
        resp = requests.get(url, params=params, headers=headers, timeout=30)
        
        if resp.status_code != 200:
            return None
        
        data = resp.json()
        results = data.get("results", [])
        
        if not results:
            return None
        
        item = results[0]
        title = item.get("title", "Unknown Title")
        
        # پیدا کردن لینک PDF
        pdf_url = None
        for link in item.get("links", []):
            if link.get("type") == "application/pdf":
                pdf_url = link.get("url")
                break
        
        if not pdf_url:
            # اگر PDF مستقیم نبود، از لینک اصلی استفاده کن
            pdf_url = item.get("link", "")
        
        if not pdf_url:
            return None
        
        return {
            "title": title,
            "pdf_url": pdf_url,
            "source": "core"
        }
        
    except Exception as e:
        print(f"CORE search error: {e}")
        return None
