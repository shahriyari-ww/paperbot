# providers/unpaywall_provider.py
import requests

def search_unpaywall(query: str):
    """
    جستجو در Unpaywall برای یافتن نسخه Open Access مقاله
    """
    try:
        if not query.startswith("10."):
            print("❌ Not a DOI, skipping Unpaywall")
            return None
            
        url = f"https://api.unpaywall.org/v2/{query}?email=your_email@example.com"
        resp = requests.get(url, timeout=30)
        
        if resp.status_code != 200:
            print(f"❌ Unpaywall API returned status: {resp.status_code}")
            return None
        
        data = resp.json()
        
        if not data.get("is_oa", False):
            print("❌ Article is not Open Access according to Unpaywall")
            return None
        
        title = data.get("title", "Unknown Title")
        
        # دریافت بهترین لینک PDF
        best_oa = data.get("best_oa_location", {})
        if best_oa and best_oa.get("url"):
            pdf_url = best_oa.get("url")
            print(f"✅ Found OA URL from Unpaywall: {pdf_url}")
            return {
                "title": title,
                "pdf_url": pdf_url,
                "source": "unpaywall"
            }
        
        oa_locations = data.get("oa_locations", [])
        for location in oa_locations:
            if location.get("url"):
                pdf_url = location.get("url")
                print(f"✅ Found OA URL from Unpaywall: {pdf_url}")
                return {
                    "title": title,
                    "pdf_url": pdf_url,
                    "source": "unpaywall"
                }
        
        return None
        
    except Exception as e:
        print(f"❌ Unpaywall search error: {e}")
        return None
