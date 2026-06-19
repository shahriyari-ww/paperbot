# search_service.py
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
    providers = [
        ("Crossref", search_crossref),      # اولویت اول برای دریافت متادیتا
        ("Unpaywall", search_unpaywall),     # منبع قانونی برای PDF
        ("Sci-Hub", search_scihub),          # منبع جایگزین برای PDF
        ("PubMed", search_pubmed),
        ("PubMed Advanced", search_pubmed_advanced),
        ("Semantic Scholar", search_semantic_scholar),
        ("arXiv", search_arxiv),
        ("CORE", search_core),
        ("BASE", search_base),
        ("DOAJ", search_doaj),
    ]
    
    for provider_name, search_func in providers:
        try:
            print(f"🔍 Searching in {provider_name} for: {query}")
            result = search_func(query)
            if result:
                print(f"✅ Found in {provider_name}")
                return result
        except Exception as e:
            print(f"⚠️ Error in {provider_name}: {e}")
            continue
    
    print(f"❌ No results found for: {query}")
    return None
