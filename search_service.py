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
from providers.nexus_provider import search_nexus

def search_open_access(query: str):
    """
    جستجو در منابع مختلف Open Access
    """
    # لیست ارائه‌دهندگان با ترتیب اولویت
    providers = [
        ("Sci-Hub", search_scihub),
        ("arXiv", search_arxiv),
        ("PubMed", search_pubmed),
        ("PubMed Advanced", search_pubmed_advanced),
        ("CORE", search_core),
        ("BASE", search_base),
        ("DOAJ", search_doaj),
        ("Crossref", search_crossref),
        ("Unpaywall", search_unpaywall),
        ("Semantic Scholar", search_semantic_scholar),
        ("Nexus", search_nexus)         
    ]
    
    for provider_name, search_func in providers:
        try:
            print(f"🔍 Searching in {provider_name} for: {query}")
            result = search_func(query)
            if result:
                print(f"✅ Found in {provider_name}: {result.get('title', 'Unknown')}")
                return result
            else:
                print(f"❌ No result from {provider_name}")
        except Exception as e:
            print(f"⚠️ Error in {provider_name}: {e}")
            continue
    
    print(f"❌ No results found for: {query}")
    return None# search_service.py
from providers.arxiv_provider import search_arxiv
from providers.pubmed_provider import search_pubmed, search_pubmed_advanced
from providers.crossref_provider import search_crossref
from providers.unpaywall_provider import search_unpaywall
from providers.core_provider import search_core
from providers.base_provider import search_base
from providers.semantic_scholar_provider import search_semantic_scholar
from providers.doaj_provider import search_doaj

def search_open_access(query: str):
    """
    جستجو در منابع مختلف Open Access
    
    Args:
        query (str): عنوان مقاله، DOI یا شناسه دیگر
        
    Returns:
        dict: شامل اطلاعات مقاله (title, pdf_url, source) یا None در صورت عدم یافت
    """
    # لیست ارائه‌دهندگان با ترتیب اولویت
    providers = [
        ("Crossref", search_crossref),              # برای DOI ها
        ("Unpaywall", search_unpaywall),            # برای پیدا کردن نسخه رایگان
        ("Semantic Scholar", search_semantic_scholar),  # برای مقالات علمی
        ("arXiv", search_arxiv),                    # برای مقالات arXiv
        ("PubMed", search_pubmed),                  # برای PubMed
        ("PubMed Advanced", search_pubmed_advanced), # برای PMC
        ("CORE", search_core),                      # موتور جستجوی Open Access
        ("BASE", search_base),                      # موتور جستجوی علمی
        ("DOAJ", search_doaj)                       # دایرکتوری مجلات دسترسی آزاد
    ]
    
    for provider_name, search_func in providers:
        try:
            print(f"🔍 Searching in {provider_name} for: {query}")
            result = search_func(query)
            if result:
                print(f"✅ Found in {provider_name}: {result.get('title', 'Unknown')}")
                return result
            else:
                print(f"❌ No result from {provider_name}")
        except Exception as e:
            print(f"⚠️ Error in {provider_name}: {e}")
            continue
    
    print(f"❌ No results found for: {query}")
    return None
