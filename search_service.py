# search_service.py
import asyncio
from typing import Optional, Dict, Any
from providers.arxiv_provider import search_arxiv
from providers.pubmed_provider import search_pubmed, search_pubmed_advanced
from providers.crossref_provider import search_crossref
from providers.unpaywall_provider import search_unpaywall
from providers.semantic_scholar_provider import search_semantic_scholar
from providers.core_provider import search_core
from providers.base_provider import search_base
from providers.doaj_provider import search_doaj
from providers.scihub_provider import search_scihub
from channel_search import search_in_channels  # ← این تابع را ایجاد کنید

def search_open_access(query: str, bot=None, context=None) -> Optional[Dict[str, Any]]:
    """
    جستجو در منابع مختلف Open Access با اولویت کانال‌های تلگرام
    
    اولویت:
    1. کش (Supabase)
    2. کانال‌های تلگرام
    3. منابع خارجی (Crossref, Sci-Hub, ...)
    """
    # 1. جستجو در کانال‌های تلگرام (اگر bot و context موجود باشد)
    if bot and context:
        print(f"🔍 Searching in Telegram channels for: {query}")
        channel_result = asyncio.run(search_in_channels(query, bot, context))
        if channel_result:
            print(f"✅ Found in Telegram channels")
            return channel_result
    
    # 2. جستجو در منابع خارجی
    providers = [
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
                return result
        except Exception as e:
            print(f"⚠️ Error in {provider_name}: {e}")
            continue
    
    print(f"❌ No results found for: {query}")
    return None
