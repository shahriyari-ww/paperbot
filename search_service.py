from providers.arxiv_provider import search_arxiv
from providers.pubmed_provider import search_pubmed, search_pubmed_advanced

def search_open_access(query: str):
    """
    جستجو در منابع مختلف Open Access
    """
    providers = [
        ("arXiv", search_arxiv),
        ("PubMed", search_pubmed),
        ("PubMed Advanced", search_pubmed_advanced)
    ]
    
    for provider_name, search_func in providers:
        try:
            print(f"Searching in {provider_name}...")
            result = search_func(query)
            if result:
                print(f"Found in {provider_name}")
                return result
        except Exception as e:
            print(f"Error in {provider_name}: {e}")
            continue
    
    return None