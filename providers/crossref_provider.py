# providers/crossref_provider.py
import requests

def search_crossref(query: str):
    """
    جستجوی DOI در Crossref برای یافتن نسخه Open Access و اطلاعات کامل مقاله
    """
    try:
        if not query.startswith("10."):
            print("❌ Not a DOI, skipping Crossref")
            return None
            
        url = f"https://api.crossref.org/works/{query}"
        headers = {
            "User-Agent": "PaperBot/1.0 (mailto:your_email@example.com)"
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
        oa_locations = work.get("oa_locations", [])
        for location in oa_locations:
            if location.get("url"):
                pdf_url = location.get("url")
                break
        
        if not pdf_url:
            links = work.get("link", [])
            for link in links:
                if "pdf" in link.get("content-type", "").lower():
                    pdf_url = link.get("url")
                    break
        
        if not pdf_url:
            print("❌ No PDF URL found in Crossref response")
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
        
    except Exception as e:
        print(f"❌ Crossref search error: {e}")
        return None
