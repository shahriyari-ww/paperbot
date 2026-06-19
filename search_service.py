# search_service.py
from providers.arxiv_provider import search_arxiv
from providers.pubmed_provider import search_pubmed, search_pubmed_advanced

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
        ("arXiv", search_arxiv),
        ("PubMed", search_pubmed),
        ("PubMed Advanced", search_pubmed_advanced)
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
