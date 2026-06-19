# providers/crossref_provider.py
import aiohttp
from typing import Optional, Dict, Any
from providers.base_provider import BaseProvider

class CrossrefProvider(BaseProvider):
    name = "crossref"
    timeout = 30
    
    async def search(self, query: str) -> Optional[Dict[str, Any]]:
        """
        جستجو در Crossref و دریافت اطلاعات کامل مقاله
        """
        if not query.startswith("10."):
            print("❌ Not a DOI, skipping Crossref")
            return None
        
        url = f"https://api.crossref.org/works/{query}"
        headers = {"User-Agent": "PaperBot/2.0 (mailto:your_email@example.com)"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=self.timeout) as resp:
                    if resp.status != 200:
                        print(f"❌ Crossref returned status: {resp.status}")
                        return None
                    
                    data = await resp.json()
                    work = data.get("message", {})
                    
                    # استخراج اطلاعات
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
                    
                    # پیدا کردن لینک PDF
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
                    
                    if not pdf_url:
                        print("❌ No PDF URL found in Crossref")
                        return None
                    
                    return {
                        "title": title,
                        "authors": authors,
                        "journal": journal,
                        "year": year,
                        "pdf_url": pdf_url,
                        "source": self.name,
                        "doi": query,
                    }
                    
        except Exception as e:
            print(f"❌ Crossref error: {e}")
            return None

# نمونه سراسری
crossref_provider = CrossrefProvider()
