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
from providers.openalex_provider import search_openalex
from typing import Optional, Dict, Any, List

def search_open_access(query: str, max_results: int = 5) -> Optional[List[Dict[str, Any]]]:
    """
    جستجو در منابع مختلف Open Access با قابلیت بازگرداندن چندین نتیجه
    """
    providers = [
        ("OpenAlex", search_openalex),      # منبع جدید
        ("Crossref", search_crossref),
        ("Unpaywall", search_unpaywall),
        ("Sci-Hub", search_scihub),
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
                return [result] if not isinstance(result, list) else result
        except Exception as e:
            print(f"⚠️ Error in {provider_name}: {e}")
            continue
    
    print(f"❌ No results found for: {query}")
    return None

def search_open_access_single(query: str) -> Optional[Dict[str, Any]]:
    """
    جستجو و بازگرداندن اولین نتیجه (برای سازگاری با کد قبلی)
    """
    results = search_open_access(query, max_results=1)
    if results and len(results) > 0:
        return results[0]
    return None
