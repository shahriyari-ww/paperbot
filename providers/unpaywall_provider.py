import requests

def search_unpaywall(query: str):
    """
    جستجو در Unpaywall برای یافتن نسخه Open Access مقاله
    """
    try:
        # اگر query یک DOI نیست، آن را جستجو نمی‌کنیم
        if not query.startswith("10."):
            return None
            
        url = f"https://api.unpaywall.org/v2/{query}?email=your_email@example.com"
        resp = requests.get(url, timeout=30)
        
        if resp.status_code != 200:
            return None
        
        data = resp.json()
        
        if not data.get("is_oa", False):
            return None
        
        title = data.get("title", "Unknown Title")
        
        # بهترین لینک Open Access
        best_oa = data.get("best_oa_location", {})
        if best_oa and best_oa.get("url"):
            return {
                "title": title,
                "pdf_url": best_oa.get("url"),
                "source": "unpaywall"
            }
        
        # لینک‌های دیگر
        oa_locations = data.get("oa_locations", [])
        for location in oa_locations:
            if location.get("url"):
                return {
                    "title": title,
                    "pdf_url": location.get("url"),
                    "source": "unpaywall"
                }
        
        return None
        
    except Exception as e:
        print(f"Unpaywall search error: {e}")
        return None
