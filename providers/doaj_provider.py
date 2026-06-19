# providers/doaj_provider.py
import requests

def search_doaj(query: str):
    """
    جستجو در DOAJ (Directory of Open Access Journals)
    
    Args:
        query (str): عنوان مقاله
        
    Returns:
        dict: اطلاعات مقاله یا None در صورت عدم یافت
    """
    try:
        # جستجو در DOAJ
        url = f"https://doaj.org/api/v2/search/articles/{query}?pageSize=1"
        
        print(f"📡 Sending request to DOAJ API...")
        resp = requests.get(url, timeout=30)
        
        if resp.status_code != 200:
            print(f"❌ DOAJ API returned status: {resp.status_code}")
            return None
        
        data = resp.json()
        results = data.get("results", [])
        
        if not results:
            print("❌ No results found")
            return None
        
        item = results[0]
        article = item.get("article", {})
        bibjson = article.get("bibjson", {})
        
        title = bibjson.get("title", "Unknown Title")
        print(f"📄 Found title: {title}")
        
        # پیدا کردن لینک PDF
        pdf_url = None
        for link in bibjson.get("link", []):
            if link.get("type") == "pdf":
                pdf_url = link.get("url")
                print(f"✅ Found PDF link: {pdf_url}")
                break
        
        if not pdf_url:
            # اگر PDF پیدا نشد، از لینک اصلی استفاده کن
            for link in bibjson.get("link", []):
                if link.get("url"):
                    pdf_url = link.get("url")
                    print(f"ℹ️ Using generic link: {pdf_url}")
                    break
        
        if not pdf_url:
            print("❌ No link found")
            return None
        
        return {
            "title": title,
            "pdf_url": pdf_url,
            "source": "doaj"
        }
        
    except requests.exceptions.Timeout:
        print("❌ DOAJ API timeout")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ DOAJ API request error: {e}")
        return None
    except Exception as e:
        print(f"❌ DOAJ search error: {e}")
        return None
