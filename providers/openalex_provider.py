# providers/openalex_provider.py
import requests
from typing import Optional, Dict, Any

def search_openalex(query: str) -> Optional[Dict[str, Any]]:
    """
    جستجو در OpenAlex برای یافتن نسخه Open Access مقاله
    
    Args:
        query (str): DOI مقاله (شروع با 10.)
        
    Returns:
        dict: اطلاعات مقاله یا None در صورت عدم یافت
    """
    try:
        if not query.startswith("10."):
            print("❌ Not a DOI, skipping OpenAlex")
            return None
            
        url = f"https://api.openalex.org/works/https://doi.org/{query}"
        headers = {
            "User-Agent": "PaperBot/2.0 (mailto:your_email@example.com)"
        }
        
        print(f"📡 Sending request to OpenAlex API...")
        resp = requests.get(url, headers=headers, timeout=30)
        
        if resp.status_code != 200:
            print(f"❌ OpenAlex API returned status: {resp.status_code}")
            return None
        
        data = resp.json()
        
        # استخراج عنوان
        title = data.get("title", "Unknown Title")
        print(f"📄 Found title: {title}")
        
        # استخراج نویسندگان
        authors = []
        for authorship in data.get("authorships", []):
            author = authorship.get("author", {})
            if author:
                authors.append(author.get("display_name", ""))
        
        authors_text = ", ".join(authors[:5])
        if len(authors) > 5:
            authors_text += " et al."
        
        # استخراج مجله
        journal = data.get("primary_location", {}).get("source", {}).get("display_name", "Unknown Journal")
        
        # استخراج سال
        year = data.get("publication_year", "Unknown Year")
        
        # پیدا کردن لینک PDF (Open Access)
        pdf_url = None
        
        # 1. بررسی open_access
        open_access = data.get("open_access", {})
        if open_access.get("is_oa", False):
            pdf_url = open_access.get("oa_url")
            if pdf_url:
                print(f"✅ Found OA URL: {pdf_url}")
        
        # 2. بررسی best_oa_location
        if not pdf_url:
            best_oa = data.get("best_oa_location", {})
            if best_oa:
                pdf_url = best_oa.get("pdf_url") or best_oa.get("landing_page_url")
                if pdf_url:
                    print(f"✅ Found best OA location: {pdf_url}")
        
        # 3. بررسی primary_location
        if not pdf_url:
            primary_location = data.get("primary_location", {})
            if primary_location:
                pdf_url = primary_location.get("pdf_url") or primary_location.get("landing_page_url")
                if pdf_url:
                    print(f"✅ Found primary location: {pdf_url}")
        
        if not pdf_url:
            print("❌ No PDF URL found in OpenAlex")
            return None
        
        return {
            "title": title,
            "authors": authors_text,
            "journal": journal,
            "year": year,
            "pdf_url": pdf_url,
            "source": "openalex",
            "doi": query
        }
        
    except requests.exceptions.Timeout:
        print("❌ OpenAlex API timeout")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ OpenAlex API request error: {e}")
        return None
    except Exception as e:
        print(f"❌ OpenAlex search error: {e}")
        return None
