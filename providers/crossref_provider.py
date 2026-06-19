# providers/crossref_provider.py
import requests

def search_crossref(query: str):
    try:
        if not query.startswith("10."):
            return None
            
        url = f"https://api.crossref.org/works/{query}"
        headers = {"User-Agent": "PaperBot/2.0 (mailto:your_email@example.com)"}
        
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code != 200:
            return None
        
        data = resp.json()
        work = data.get("message", {})
        
        title = work.get("title", ["Unknown Title"])[0]
        
        # استخراج نویسندگان
        authors_list = work.get("author", [])
        if authors_list:
            authors = ", ".join([f"{a.get('given', '')} {a.get('family', '')}".strip() for a in authors_list[:5]])
            if len(authors_list) > 5:
                authors += " et al."
        else:
            authors = "Unknown Authors"
        
        journal = work.get("container-title", ["Unknown Journal"])[0]
        year = work.get("issued", {}).get("date-parts", [[None]])[0][0]
        if not year:
            year = "Unknown Year"
        
        # پیدا کردن PDF
        pdf_url = None
        for loc in work.get("oa_locations", []):
            if loc.get("url"):
                pdf_url = loc.get("url")
                break
        
        if not pdf_url:
            for link in work.get("link", []):
                if "pdf" in link.get("content-type", "").lower():
                    pdf_url = link.get("url")
                    break
        
        # اگر PDF پیدا نشد، از Sci-Hub استفاده کن
        if not pdf_url:
            scihub_result = search_scihub(query)
            if scihub_result:
                pdf_url = scihub_result.get("pdf_url")
        
        if not pdf_url:
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
        print(f"❌ Crossref error: {e}")
        return None

def search_scihub(query: str):
    try:
        mirrors = ["https://sci-hub.se", "https://sci-hub.st", "https://sci-hub.ru"]
        for mirror in mirrors:
            try:
                url = f"{mirror}/{query}"
                resp = requests.get(url, timeout=30)
                if resp.status_code == 200:
                    return {"pdf_url": url}
            except:
                continue
        return None
    except:
        return None
