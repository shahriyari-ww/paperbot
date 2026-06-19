# search_service.py
import time
import random
from providers.arxiv_provider import search_arxiv
from providers.pubmed_provider import search_pubmed, search_pubmed_advanced
from providers.crossref_provider import search_crossref
from providers.unpaywall_provider import search_unpaywall
from providers.semantic_scholar_provider import search_semantic_scholar
from providers.core_provider import search_core
from providers.base_provider import search_base
from providers.doaj_provider import search_doaj
from providers.scihub_provider import search_scihub

def search_open_access(query: str):
    """
    جستجو در منابع مختلف Open Access با اولویت‌بندی جدید
    """
    # لیست ارائه‌دهندگان با اولویت جدید (Sci-Hub و PubMed در اولویت)
    providers = [
        ("Sci-Hub", search_scihub),            # منبع اصلی برای مقالات پولی
        ("PubMed", search_pubmed),              # منبع اصلی برای مقالات پزشکی
        ("PubMed Advanced", search_pubmed_advanced),
        ("Crossref", search_crossref),
        ("Unpaywall", search_unpaywall),
        ("Semantic Scholar", search_semantic_scholar),
        ("arXiv", search_arxiv),
        ("CORE", search_core),
        ("BASE", search_base),
        ("DOAJ", search_doaj),
    ]
    
    for provider_name, search_func in providers:
        try:
            # افزودن تأخیر تصادفی برای جلوگیری از خطای 429
            time.sleep(random.uniform(1.0, 2.5))
            
            print(f"🔍 Searching in {provider_name} for: {query}")
            result = search_func(query)
            if result:
                print(f"✅ Found in {provider_name}: {result.get('title', 'Unknown')}")
                return result
            else:
                print(f"❌ No result from {provider_name}")
        except Exception as e:
            print(f"⚠️ Error in {provider_name}: {e}")
            # در صورت بروز خطا (مثل 429)، ۳ ثانیه صبر کن و ادامه بده
            time.sleep(3)
            continue
    
    print(f"❌ No results found for: {query}")
    return None
