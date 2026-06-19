# providers/semantic_scholar_provider.py
import requests

def search_semantic_scholar(query: str):
    """
    جستجو در Semantic Scholar برای یافتن مقالات علمی
    
    Args:
        query (str): عنوان مقاله یا DOI
        
    Returns:
        dict: اطلاعات مقاله یا None در صورت عدم یافت
    """
    try:
        # ساخت URL جستجو
        if query.startswith("10."):
            # اگر DOI است، از API مستقیم استفاده کن
            url = f"https://api.semanticscholar.org/v1/paper/{query}"
        else:
            # در غیر این صورت جستجو کن
            url = f"https://api.semanticscholar.org/v1/paper/search?query={query}&limit=1"
        
        headers = {
            "User-Agent": "PaperBot/1.0"
        }
        
        print(f"📡 Sending request to Semantic Scholar API...")
        resp = requests.get(url, headers=headers, timeout=30)
        
        if resp.status_code != 200:
            print(f"❌ Semantic Scholar API returned status: {resp.status_code}")
            return None
        
        data = resp.json()
        
        # اگر جستجو بود، اولین نتیجه را بگیر
        if not query.startswith("10."):
            papers = data.get("papers", [])
            if not papers:
                print("❌ No papers found")
                return None
            paper = papers[0]
        else:
            paper = data
        
        title = paper.get("title", "Unknown Title")
        print(f"📄 Found title: {title}")
        
        # پیدا کردن لینک PDF
        pdf_url = None
        open_access = paper.get("openAccess", {})
        if open_access.get("url"):
            pdf_url = open_access.get("url")
            print(f"✅ Found OA URL: {pdf_url}")
        else:
            # بررسی لینک‌ها
            links = paper.get("links", [])
            for link in links:
                if "pdf" in link.lower():
                    pdf_url = link
                    print(f"✅ Found PDF link: {pdf_url}")
                    break
        
        if not pdf_url:
            print("❌ No PDF URL found")
            return None
        
        return {
            "title": title,
            "pdf_url": pdf_url,
            "source": "semantic_scholar"
        }
        
    except requests.exceptions.Timeout:
        print("❌ Semantic Scholar API timeout")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Semantic Scholar API request error: {e}")
        return None
    except Exception as e:
        print(f"❌ Semantic Scholar search error: {e}")
        return None
