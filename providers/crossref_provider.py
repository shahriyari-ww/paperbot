# providers/crossref_provider.py
import requests

def search_crossref(query):
    """
    جستجوی DOI در Crossref برای یافتن نسخه Open Access
    """
    try:
        url = f"https://api.crossref.org/works/{query}"
        resp = requests.get(url, timeout=30)
        
        if resp.status_code != 200:
            return None
        
        data = resp.json()
        work = data.get("message", {})
        title = work.get("title", ["Unknown Title"])[0]
        
        # بررسی Open Access
        oa_url = None
        oa_locations = work.get("oa_locations", [])
        if oa_locations:
            # اولین لینک Open Access را برمی‌گرداند
            for location in oa_locations:
                if location.get("url"):
                    oa_url = location.get("url")
                    break
        
        if not oa_url:
            return None
        
        return {
            "title": title,
            "pdf_url": oa_url,
            "source": "crossref"
        }
        
    except Exception as e:
        print(f"Crossref search error: {e}")
        return None
