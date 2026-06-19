# providers/crossref_provider.py
import requests
import re
from typing import Optional, Dict, Any

def search_crossref(query: str) -> Optional[Dict[str, Any]]:
    """
    جستجوی DOI در Crossref برای دریافت اطلاعات کامل مقاله
    
    Args:
        query (str): DOI مقاله (شروع با 10.)
        
    Returns:
        dict: اطلاعات کامل مقاله یا None در صورت عدم یافت
    """
    try:
        if not query.startswith("10."):
            print("❌ Not a DOI, skipping Crossref")
            return None
            
        url = f"https://api.crossref.org/works/{query}"
        headers = {
            "User-Agent": "PaperBot/2.0 (mailto:your_email@example.com)"
        }
        
        print(f"📡 Sending request to Crossref API...")
        resp = requests.get(url, headers=headers, timeout=30)
        
        if resp.status_code != 200:
            print(f"❌ Crossref API returned status: {resp.status_code}")
            return None
        
        data = resp.json()
        work = data.get("message", {})
        
        # استخراج اطلاعات کامل
        title_list = work.get("title", ["Unknown Title"])
        title = title_list[0] if title_list else "Unknown Title"
        
        # استخراج نویسندگان
        authors_list = work.get("author", [])
        if authors_list:
            authors = ", ".join([f"{a.get('given', '')} {a.get('family', '')}".strip() for a in authors_list[:5]])
            if len(authors_list) > 5:
                authors += " et al."
        else:
            authors = "Unknown Authors"
        
        # استخراج مجله و سال
        journal = work.get("container-title", ["Unknown Journal"])[0]
        year = work.get("issued", {}).get("date-parts", [[None]])[0][0]
        if not year:
            year = "Unknown Year"
        
        # بررسی لینک‌های Open Access
        pdf_url = None
        
        # 1. OA Locations
        for loc in work.get("oa_locations", []):
            if loc.get("url"):
                pdf_url = loc.get("url")
                break
        
        # 2. Links
        if not pdf_url:
            for link in work.get("link", []):
                if "pdf" in link.get("content-type", "").lower():
                    pdf_url = link.get("url")
                    break
        
        # 3. اگر PDF پیدا نشد، از Sci-Hub استفاده کن
        if not pdf_url:
            scihub_result = search_scihub(query)
            if scihub_result:
                pdf_url = scihub_result.get("pdf_url")
        
        if not pdf_url:
            print("❌ No PDF URL found in Crossref")
            return None
        
        return {
            "title": title,
            "authors": authors,
            "journal": journal,
            "year": year,
            "pdf_url": pdf_url,
            "source": "crossref",
            "doi": query
        }
        
    except requests.exceptions.Timeout:
        print("❌ Crossref API timeout")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Crossref API request error: {e}")
        return None
    except Exception as e:
        print(f"❌ Crossref search error: {e}")
        return None


def search_scihub(query: str) -> Optional[Dict[str, Any]]:
    """
    تابع کمکی برای جستجو در Sci-Hub (Fallback)
    
    Args:
        query (str): DOI مقاله
        
    Returns:
        dict: شامل pdf_url یا None
    """
    try:
        if not query.startswith("10."):
            return None
            
        mirrors = [
            "https://sci-hub.se",
            "https://sci-hub.st",
            "https://sci-hub.ru",
            "https://sci-hub.ee"
        ]
        
        for mirror in mirrors:
            try:
                url = f"{mirror}/{query}"
                resp = requests.get(url, timeout=30)
                if resp.status_code == 200:
                    # بررسی اینکه آیا PDF مستقیم است
                    content_type = resp.headers.get('content-type', '').lower()
                    if 'application/pdf' in content_type:
                        return {"pdf_url": url}
                    
                    # اگر HTML بود، لینک PDF را استخراج کن
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    
                    # جستجو در iframe
                    for iframe in soup.find_all('iframe'):
                        src = iframe.get('src', '')
                        if src and 'pdf' in src.lower():
                            pdf_url = src if src.startswith('http') else f"{mirror}{src}"
                            return {"pdf_url": pdf_url}
                    
                    # جستجو در لینک‌ها
                    for link in soup.find_all('a'):
                        href = link.get('href', '')
                        if href and 'pdf' in href.lower():
                            pdf_url = href if href.startswith('http') else f"{mirror}{href}"
                            return {"pdf_url": pdf_url}
                    
                    # اگر هیچ PDF پیدا نشد، از همان URL استفاده کن
                    return {"pdf_url": url}
            except:
                continue
        
        return None
    except:
        return None


def get_paper_metadata(doi: str) -> Optional[Dict[str, Any]]:
    """
    تابع کمکی برای دریافت متادیتا از منابع مختلف
    """
    # 1. ابتدا از Crossref
    result = search_crossref(doi)
    if result and result.get("authors") != "Unknown Authors":
        return result
    
    # 2. اگر کامل نبود، از Sci-Hub استفاده کن
    scihub_result = search_scihub(doi)
    if scihub_result:
        return {
            "title": f"Article from Sci-Hub ({doi})",
            "authors": "Unknown Authors",
            "journal": "Unknown Journal",
            "year": "Unknown Year",
            "pdf_url": scihub_result.get("pdf_url", ""),
            "source": "scihub",
            "doi": doi
        }
    
    return None
