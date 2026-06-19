# providers/scihub_provider.py
import requests

def search_scihub(query: str):
    """
    جستجو در Sci-Hub برای یافتن نسخه Open Access مقاله
    
    Args:
        query (str): DOI مقاله (شروع با 10.)
        
    Returns:
        dict: اطلاعات مقاله یا None در صورت عدم یافت
    """
    try:
        # اگر query یک DOI نیست، جستجو نمی‌کنیم
        if not query.startswith("10."):
            print("❌ Not a DOI, skipping Sci-Hub")
            return None
            
        # لیست آینه‌های Sci-Hub (ممکن است برخی کار نکنند)
        mirrors = [
            "https://sci-hub.se",
            "https://sci-hub.st",
            "https://sci-hub.ru",
            "https://sci-hub.ee"
        ]
        
        print(f"📡 Searching Sci-Hub for: {query}")
        
        for mirror in mirrors:
            try:
                url = f"{mirror}/{query}"
                resp = requests.get(url, timeout=30)
                
                if resp.status_code == 200:
                    # PDF پیدا شد
                    print(f"✅ Found PDF at {mirror}")
                    
                    # استخراج عنوان (ساده شده)
                    title = f"Article from Sci-Hub ({query})"
                    
                    return {
                        "title": title,
                        "pdf_url": url,
                        "source": "scihub"
                    }
            except:
                continue
        
        print("❌ No working Sci-Hub mirror found")
        return None
        
    except Exception as e:
        print(f"❌ Sci-Hub search error: {e}")
        return None
